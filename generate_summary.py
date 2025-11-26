#!/usr/bin/env python
"""
独立脚本:从registry读取成功的因子评估作业并生成summary CSV
可以在Airflow外部直接运行
"""
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
from factor_platform.factor_store import FactorStore, DEFAULT_DB_PATH

def generate_summary(
    registry_db: str = None,
    output_dir: str = None,
    status_filter: str = "SUCCESS"
):
    """
    从registry读取成功的作业并生成summary CSV
    
    Args:
        registry_db: registry数据库路径(默认使用DEFAULT_DB_PATH)
        output_dir: 输出目录(默认使用./.airflow_factor_pipeline)
        status_filter: 要包含的作业状态(默认SUCCESS)
    """
    if registry_db is None:
        registry_db = DEFAULT_DB_PATH
    
    if output_dir is None:
        output_dir = Path("./.airflow_factor_pipeline")
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 连接registry
    store = FactorStore(Path(registry_db))
    
    # 获取所有作业
    all_jobs = store.list_jobs()
    
    # 过滤成功的作业
    success_jobs = [j for j in all_jobs if j.get("status") == status_filter]
    
    if not success_jobs:
        print(f"未找到状态为 {status_filter} 的作业")
        return None
    
    print(f"找到 {len(success_jobs)} 个{status_filter}作业")
    
    # 构建summary数据
    rows = []
    for job in success_jobs:
        job_id = job.get("job_id")
        factor_code = job.get("factor_code")
        
        # 获取因子详情
        factors = store.list_factors()
        factor_info = next((f for f in factors if f.get("code") == factor_code), {})
        
        # 解析metrics JSON
        metrics_json = job.get("metrics_json")  # 修正列名
        if isinstance(metrics_json, str):
            try:
                # Python的NaN在JSON中,需要特殊处理
                import math
                import re
                # 替换JSON中的NaN为null
                cleaned_json = re.sub(r'\bNaN\b', 'null', metrics_json)
                metrics = json.loads(cleaned_json)
            except Exception as e:
                print(f"Warning: 无法解析job {job_id}的metrics: {e}")
                metrics = {}
        elif isinstance(metrics_json, dict):
            metrics = metrics_json
        else:
            metrics = {}
        
        rows.append({
            "job_id": job_id,
            "code": factor_code,
            "name": factor_info.get("name", ""),
            "IC": metrics.get("IC"),
            "ICIR": metrics.get("ICIR"),
            "Rank IC": metrics.get("Rank IC"),
            "Rank ICIR": metrics.get("Rank ICIR"),
            "annual_return": metrics.get("annual_return"),
            "sharpe_ratio": metrics.get("sharpe_ratio"),
            "max_drawdown": metrics.get("max_drawdown"),
            "expression": factor_info.get("expression", ""),
            "start_date": job.get("start_date"),
            "end_date": job.get("end_date"),
            "created_at": job.get("created_at"),
            "updated_at": job.get("updated_at"),
        })
    
    # 创建DataFrame并排序
    df = pd.DataFrame(rows)
    df.sort_values(by=["ICIR", "IC"], ascending=False, inplace=True, na_position='last')
    
    # 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_path = output_dir / f"qlib_factor_summary_{timestamp}.csv"
    
    # 保存CSV
    df.to_csv(summary_path, index=False, encoding='utf-8-sig')
    
    print(f"\n{'='*80}")
    print(f"Summary CSV 已生成: {summary_path}")
    print(f"{'='*80}")
    print(f"\n前10个因子(按ICIR排序):\n")
    print(df[["code", "name", "IC", "ICIR", "annual_return", "sharpe_ratio", "max_drawdown"]].head(10).to_string(index=False))
    print(f"\n{'='*80}\n")
    
    # 更新registry中的result_path
    job_ids = [r["job_id"] for r in rows]
    store.attach_result_path(job_ids, str(summary_path))
    
    return str(summary_path)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="生成因子分析summary CSV")
    parser.add_argument("--registry-db", help="registry数据库路径", default=None)
    parser.add_argument("--output-dir", help="输出目录", default=None)
    parser.add_argument("--status", help="作业状态过滤(默认SUCCESS)", default="SUCCESS")
    
    args = parser.parse_args()
    
    summary_path = generate_summary(
        registry_db=args.registry_db,
        output_dir=args.output_dir,
        status_filter=args.status
    )
    
    if summary_path:
        print(f"✓ 成功生成summary: {summary_path}")
    else:
        print("✗ 未能生成summary")
