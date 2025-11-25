from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from airflow.decorators import dag, task
from airflow.exceptions import AirflowFailException

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_STORAGE_ROOT = WORKSPACE_ROOT / ".airflow_factor_pipeline"
DEFAULT_STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
DEFAULT_FACTOR_FILE = WORKSPACE_ROOT / "configs" / "factors.json"
QLIB_DEFAULT_ROOT = WORKSPACE_ROOT / "stockdata" / "qlib_data" / "cn_data"

DEFAULT_FACTORS: List[Dict[str, Any]] = [
    {
        "code": "alpha_mom_5",
        "name": "5日动量",
        "expression": "Ref($close, 5) / $close - 1",
        "category": "momentum",
    },
    {
        "code": "alpha_mom_20",
        "name": "20日动量",
        "expression": "Ref($close, 20) / $close - 1",
        "category": "momentum",
    },
    {
        "code": "alpha_vol_10",
        "name": "10日波动率",
        "expression": "Std($close, 10) / Mean($close, 10)",
        "category": "volatility",
    },
    {
        "code": "alpha_meanrev_15",
        "name": "15日均值回归",
        "expression": "($close - Mean($close, 15)) / Std($close, 15)",
        "category": "mean_reversion",
    },
    {
        "code": "alpha_beta_30",
        "name": "30日Beta",
        "expression": "Cov($close, Mean($close, 5), 30) / Var(Mean($close, 5), 30)",
        "category": "beta",
    },
]


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _parse_date(value: str, fallback: str) -> str:
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return value
    except Exception:
        return fallback


def _load_factor_catalog(path: Path) -> List[Dict[str, Any]]:
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, list) and data:
                return data
        except Exception:
            pass
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(DEFAULT_FACTORS, ensure_ascii=False, indent=2), encoding="utf-8")
    return DEFAULT_FACTORS


def _calc_daily_ic(df: pd.DataFrame, factor_col: str, target_col: str) -> Dict[str, float]:
    if df.empty:
        return {"mean": 0.0, "std": 0.0}
    daily = df.groupby("datetime").apply(lambda x: x[factor_col].corr(x[target_col]))
    return {
        "mean": float(daily.mean(skipna=True) or 0.0),
        "std": float(daily.std(skipna=True) or 0.0),
    }


def _calc_sharpe(series: pd.Series) -> float:
    if series.empty:
        return 0.0
    std = series.std()
    if not std or np.isnan(std):
        return 0.0
    return float(np.sqrt(252) * series.mean() / std)


def _calc_drawdown(returns: pd.Series) -> float:
    if returns.empty:
        return 0.0
    wealth = (1 + returns.fillna(0)).cumprod()
    running_max = wealth.cummax()
    drawdown = (wealth - running_max) / running_max
    return float(abs(drawdown.min()))


@task(execution_timeout=timedelta(minutes=5))
def bootstrap_environment() -> Dict[str, Any]:
    storage_dir = Path(os.environ.get("FACTOR_PIPELINE_STORAGE", DEFAULT_STORAGE_ROOT))
    storage_dir.mkdir(parents=True, exist_ok=True)
    qlib_path = Path(os.environ.get("QLIB_DATA_PATH", QLIB_DEFAULT_ROOT))
    if not qlib_path.exists():
        raise AirflowFailException(
            f"未找到 qlib 数据目录：{qlib_path}。请确认 D:/JoinQuant/VScode/airflow/stockdata/qlib_data/cn_data 已同步到当前环境，或者设置 QLIB_DATA_PATH。"
        )
    start = _parse_date(os.environ.get("FACTOR_START_DATE", "2018-01-01"), "2018-01-01")
    end = _parse_date(os.environ.get("FACTOR_END_DATE", "2024-12-31"), "2024-12-31")
    freq = os.environ.get("FACTOR_FREQ", "day").strip().lower() or "day"
    instruments = os.environ.get("FACTOR_INSTRUMENTS", "csi300").split(",")
    return {
        "storage_dir": str(storage_dir),
        "qlib_path": str(qlib_path),
        "start": start,
        "end": end,
        "freq": freq,
        "instruments": [item.strip() for item in instruments if item.strip()],
        "factor_catalog": str(DEFAULT_FACTOR_FILE),
    }


@task
def load_factor_catalog(env: Dict[str, Any]) -> str:
    catalog_path = Path(os.environ.get("FACTOR_CATALOG_PATH", env["factor_catalog"]))
    _ = _load_factor_catalog(catalog_path)
    return str(catalog_path)


@task
def prepare_factor_queue(catalog_path: str) -> List[Dict[str, Any]]:
    factors = json.loads(Path(catalog_path).read_text(encoding="utf-8"))
    batch = max(int(os.environ.get("FACTOR_BATCH_SIZE", "8")), 1)
    jobs: List[Dict[str, Any]] = []
    for spec in factors[:batch]:
        expression = spec.get("expression")
        if not expression:
            continue
        jobs.append(
            {
                "code": spec.get("code"),
                "name": spec.get("name", spec.get("code")),
                "expression": expression,
                "category": spec.get("category"),
                "instruments": spec.get("instruments"),
            }
        )
    if not jobs:
        raise AirflowFailException("因子目录中没有可执行的表达式。")
    return jobs


@task
def evaluate_factor(job: Dict[str, Any], env: Dict[str, Any]) -> Dict[str, Any]:
    try:
        import qlib
        from qlib.data import D
    except ModuleNotFoundError as exc:
        raise AirflowFailException("未安装 qlib，请运行 pip install pyqlib") from exc

    # Airflow 3.x 自带的 qlib 0.9+ 不再接受布尔类型的 expression_cache 参数
    qlib.init(provider_uri=env["qlib_path"], region="cn")

    raw_instruments = job.get("instruments") or env["instruments"]
    if isinstance(raw_instruments, str):
        raw_tokens = [raw_instruments]
    else:
        raw_tokens = list(raw_instruments)
    tokens: List[str] = []
    for item in raw_tokens:
        for part in str(item).split(","):
            part = part.strip()
            if part:
                tokens.append(part)
    if not tokens:
        tokens = ["csi300"]

    resolved: List[str] = []
    for token in tokens:
        key = token.lower()
        try:
            if key.startswith("csi"):
                pool_cfg = D.instruments(token)
                resolved.extend(D.list_instruments(pool_cfg, as_list=True))
            else:
                resolved.append(token)
        except Exception:
            resolved.append(token)
    instruments = list(dict.fromkeys(resolved)) or D.instruments("csi300")
    start = env["start"]
    end = env["end"]
    freq = env["freq"]

    try:
        factor_df = D.features(instruments, [job["expression"]], start_time=start, end_time=end, freq=freq)
        factor_df.columns = ["factor"]
        label_df = D.features(
            instruments,
            ["Ref($close, -1)/$close - 1"],
            start_time=start,
            end_time=end,
            freq=freq,
        )
        label_df.columns = ["label"]
    except Exception as exc:
        return {
            "code": job["code"],
            "name": job.get("name"),
            "status": "FAILED",
            "error": f"拉取qlib数据失败: {exc}",
        }

    merged = pd.concat([factor_df, label_df], axis=1).dropna()
    if merged.empty:
        return {
            "code": job["code"],
            "name": job.get("name"),
            "status": "FAILED",
            "error": "提取出的因子或标签为空",
        }
    if isinstance(merged.index, pd.MultiIndex):
        inst_name, dt_name = merged.index.names
        merged = merged.reset_index()
        merged = merged.rename(
            columns={
                (inst_name or "level_0"): "instrument",
                (dt_name or "level_1"): "datetime",
            }
        )
    if "datetime" not in merged.columns:
        merged["datetime"] = merged.index
    ic_stats = _calc_daily_ic(merged, "factor", "label")
    rank_df = merged.assign(rank_factor=merged["factor"].rank(), rank_label=merged["label"].rank())
    rank_stats = _calc_daily_ic(rank_df, "rank_factor", "rank_label")
    daily_returns = merged.groupby("datetime")["label"].mean().reset_index(drop=False)
    annual_return = float(daily_returns["label"].mean() * 252)
    sharpe = _calc_sharpe(daily_returns["label"])
    max_dd = _calc_drawdown(daily_returns.set_index("datetime")["label"])

    metrics = {
        "IC": ic_stats["mean"],
        "ICIR": float(ic_stats["mean"] / ic_stats["std"]) if ic_stats["std"] else 0.0,
        "Rank IC": rank_stats["mean"],
        "Rank ICIR": float(rank_stats["mean"] / rank_stats["std"]) if rank_stats["std"] else 0.0,
        "annual_return": annual_return,
        "sharpe_ratio": sharpe,
        "max_drawdown": max_dd,
    }
    return {
        "code": job["code"],
        "name": job.get("name"),
        "status": "SUCCESS",
        "metrics": metrics,
        "expression": job["expression"],
    }


@task
def aggregate_results(evaluations: List[Dict[str, Any]], env: Dict[str, Any]) -> str:
    successes = [item for item in evaluations if item.get("status") == "SUCCESS"]
    if not successes:
        raise AirflowFailException("所有因子评估均失败，请检查日志。")
    rows = []
    for item in successes:
        metrics = item.get("metrics", {})
        rows.append(
            {
                "code": item.get("code"),
                "name": item.get("name"),
                "IC": metrics.get("IC"),
                "ICIR": metrics.get("ICIR"),
                "Rank IC": metrics.get("Rank IC"),
                "Rank ICIR": metrics.get("Rank ICIR"),
                "annual_return": metrics.get("annual_return"),
                "sharpe_ratio": metrics.get("sharpe_ratio"),
                "max_drawdown": metrics.get("max_drawdown"),
                "expression": item.get("expression"),
            }
        )
    df = pd.DataFrame(rows)
    df.sort_values(by=["ICIR", "IC"], ascending=False, inplace=True)
    summary_path = Path(env["storage_dir"]) / f"qlib_factor_summary_{_timestamp()}.csv"
    df.to_csv(summary_path, index=False)
    return str(summary_path)


@task
def publish_summary(summary_path: str) -> None:
    path = Path(summary_path)
    if not path.exists():
        raise AirflowFailException(f"汇总文件不存在: {summary_path}")
    df = pd.read_csv(path)
    top_rows = df.head(10)
    print("=" * 80)
    print("QLib 因子分析报告（Top 10 by ICIR）")
    print("=" * 80)
    print(top_rows.to_string(index=False))
    print("=" * 80)


default_args = {
    "owner": "qlib_factor_pipeline",
    "retries": 0,
    "execution_timeout": timedelta(minutes=30),
}


@dag(
    dag_id="starquant_factor_pipeline",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    is_paused_upon_creation=False,
    default_args=default_args,
    tags=["factor", "qlib", "analysis"],
    description="基于本地 qlib 数据的因子分析 DAG",
)
def starquant_factor_pipeline() -> None:
    env = bootstrap_environment()
    catalog_path = load_factor_catalog(env)
    jobs = prepare_factor_queue(catalog_path)
    evaluations = evaluate_factor.partial(env=env).expand(job=jobs)
    summary = aggregate_results(evaluations, env)
    publish_summary(summary)


dag = starquant_factor_pipeline()
