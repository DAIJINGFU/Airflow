from __future__ import annotations

import glob
import os
from pathlib import Path
from typing import List, Optional

import pandas as pd


def load_pricing_from_stockdata(stockdata_root: str, pattern: str = '*_daily_hfq.csv') -> pd.DataFrame:
    """Load back-adjusted daily close prices from local stockdata.

    Returns a wide DataFrame with index=date and columns=stockcode (6-digit, no suffix).
    """
    data_dir = Path(stockdata_root)
    if not data_dir.exists():
        raise FileNotFoundError(f"stockdata root not found: {data_dir}")
    files = glob.glob(str(data_dir / '*' / pattern))
    if not files:
        raise FileNotFoundError(f"no files found under {data_dir} with pattern {pattern}")
    dfs: List[pd.DataFrame] = []
    for f in files:
        try:
            df = pd.read_csv(f, dtype=str)
        except Exception:
            continue
        # normalize column names (handle Chinese headers)
        if '日期' in df.columns:
            date_col = '日期'
        elif 'date' in df.columns:
            date_col = 'date'
        else:
            continue
        if '收盘' in df.columns:
            close_col = '收盘'
        elif 'close' in df.columns:
            close_col = 'close'
        else:
            continue
        # code column
        if '股票代码' in df.columns:
            code_col = '股票代码'
        elif 'code' in df.columns:
            code_col = 'code'
        else:
            # try to infer from filename
            code = Path(f).stem.split('_')[0]
            df[ 'code_inferred'] = code
            code_col = 'code_inferred'
        df = df[[date_col, code_col, close_col]].rename(columns={date_col: 'date', code_col: 'code', close_col: 'close'})
        df['date'] = pd.to_datetime(df['date'])
        df['code'] = df['code'].astype(str).str.zfill(6)
        dfs.append(df)
    if not dfs:
        raise RuntimeError('no valid pricing files parsed')
    all_df = pd.concat(dfs, ignore_index=True)
    pricing = all_df.pivot(index='date', columns='code', values='close')
    pricing = pricing.sort_index()
    # convert to numeric
    pricing = pricing.apply(pd.to_numeric, errors='coerce')
    return pricing


def factor_df_to_series(factor_df: pd.DataFrame, date_col: str = 'date', code_col: str = 'symbol', value_col: str = 'factor_value') -> pd.Series:
    """Convert a long-format factor DataFrame to Alphalens MultiIndex Series.

    factor_df: must contain date, symbol, factor_value columns.
    Returns pd.Series indexed by (date, asset) with name 'factor'.
    """
    df = factor_df.copy()
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col])
    else:
        raise ValueError('date_col not in DataFrame')
    if code_col not in df.columns:
        raise ValueError('code_col not in DataFrame')
    if value_col not in df.columns:
        raise ValueError('value_col not in DataFrame')
    df['code'] = df[code_col].astype(str).str.zfill(6)
    df = df.set_index([date_col, 'code'])[value_col]
    df.index.names = ['date', 'asset']
    s = pd.Series(df.values, index=df.index, name='factor')
    return s


def infer_market_suffix(code: str) -> str:
    """Infer .XSHG or .XSHE suffix for 6-digit code (simple heuristic)."""
    # Simple heuristic: codes starting with 6 -> XSHG; else XSHE
    c = str(code).zfill(6)
    if c.startswith('6'):
        return c + '.XSHG'
    return c + '.XSHE'


def compute_factor_from_expression(pricing: pd.DataFrame, expression: str) -> pd.DataFrame:
    """Compute factor values from a simple expression string using pricing DataFrame.

    Supported function names: Ref(pricing, n), Mean(pricing, n), Std(pricing, n),
    Cov(x, y, n), Var(x, n). The expression should use `$close` to refer to the
    pricing DataFrame, e.g. "Ref($close, 5) / $close - 1".

    Returns a DataFrame with same index and columns as `pricing` containing factor values.
    """
    # prepare namespace
    def Ref(p, n):
        return p.shift(int(n))

    def Mean(p, n):
        return p.rolling(int(n), min_periods=1).mean()

    def Std(p, n):
        return p.rolling(int(n), min_periods=1).std()

    def Var(p, n):
        return p.rolling(int(n), min_periods=1).var()

    def Cov(x, y, n):
        # rolling covariance between x and y; works column-wise
        return x.rolling(int(n), min_periods=1).cov(y)

    # Replace $close token with variable name 'pricing'
    expr = expression.replace('$close', 'pricing')

    local_vars = {
        'pricing': pricing,
        'Ref': Ref,
        'Mean': Mean,
        'Std': Std,
        'Var': Var,
        'Cov': Cov,
    }

    # Evaluate expression in restricted namespace
    try:
        result = eval(expr, {'__builtins__': {}}, local_vars)
    except Exception as exc:
        raise RuntimeError(f'failed to evaluate expression "{expression}": {exc}') from exc

    # If result is a Series, convert to DataFrame
    if isinstance(result, pd.Series):
        result = result.to_frame()

    # Ensure DataFrame index and columns align with pricing
    if isinstance(result, pd.DataFrame):
        # if result has same index as pricing, good; otherwise try to align
        result = result.reindex(index=pricing.index, columns=pricing.columns)
        return result

    raise RuntimeError('expression did not return DataFrame or Series')
