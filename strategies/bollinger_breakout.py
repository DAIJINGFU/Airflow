# -*- coding: utf-8 -*-

"""
Strategy: Bollinger Breakout
Frequency: daily
Note: Auto-generated strategy source file.
"""

from jqdata import *
import numpy as np
import pandas as pd


def initialize(context):
    set_benchmark("000300.XSHG")
    set_option("use_real_price", True)
    g.security = "000001.XSHE"
    g.unit = "1d"
    g.lookback = 60
    g.fields = ["close"]
    g.min_bars = 40
    g.target_percent = 1.0
    g.params = {"window": 20, "std_multiplier": 2.0, "target_percent": 0.9}
    if isinstance(g.params, dict) and g.params.get('unit'):
        g.unit = g.params['unit']
    run_daily(_handle_daily, time='open')


def handle_data(context, data):
    if g.unit == '1m':
        _handle(context, data)


def _handle_daily(context):
    _handle(context, None)

def _handle(context, data):
    security = g.security
    try:
        bars = attribute_history(
            security,
            g.lookback,
            g.unit,
            g.fields,
            skip_paused=True,
            df=True,
        )
    except Exception:
        bars = None
    if bars is None or bars.empty:
        return
    bars = bars.dropna()
    if len(bars) < g.min_bars:
        return
    price = bars['close'].iloc[-1]
    cash = context.portfolio.available_cash
    portfolio_value = context.portfolio.total_value
    positions = context.portfolio.positions
    position = None
    if hasattr(positions, '__contains__') and security in positions:
        position = positions[security]
    elif hasattr(positions, 'get'):
        position = positions.get(security)
    has_position = position is not None and getattr(position, 'closeable_amount', 0) > 0
    params = g.params
    closes = bars['close']
    window = int(params.get('window', 20))
    rolling = closes.rolling(window)
    mid = rolling.mean()
    std = rolling.std(ddof=0)
    if np.isnan(mid.iloc[-1]) or np.isnan(std.iloc[-1]):
        return
    mid_now = mid.iloc[-1]
    std_now = std.iloc[-1]
    upper = mid_now + params.get('std_multiplier', 2.0) * std_now
    lower = mid_now - params.get('std_multiplier', 2.0) * std_now
    if price > upper:
        if cash > price:
            target_pct = params.get('target_percent', g.target_percent)
            target_value = portfolio_value * target_pct
            order_target_value(security, target_value)
            log.info('BUY %s @ %.2f' % (security, price))
    elif (price < mid_now or price < lower) and has_position:
        order_target_value(security, 0)
        log.info('SELL %s @ %.2f' % (security, price))
    try:
        record(price=price, upper=upper, lower=lower, middle=mid_now)
    except Exception:
        pass
