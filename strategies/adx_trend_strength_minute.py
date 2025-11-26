# -*- coding: utf-8 -*-

"""
Strategy: Adx Trend Strength
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
    g.lookback = 80
    g.fields = ["high", "low", "close"]
    g.min_bars = 50
    g.target_percent = 1.0
    g.params = {"period": 14, "entry": 25, "exit": 20, "target_percent": 0.9}
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
    position = context.portfolio.positions.get(security)
    has_position = position is not None and position.closeable_amount > 0
    params = g.params
    high = bars['high']
    low = bars['low']
    close_series = bars['close']
    period = int(params.get('period', 14))
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    tr_components = pd.concat([high - low, (high - close_series.shift()).abs(), (low - close_series.shift()).abs()], axis=1)
    true_range = tr_components.max(axis=1)
    atr = true_range.rolling(period).mean()
    plus_di = 100 * pd.Series(plus_dm, index=bars.index).rolling(period).sum() / atr
    minus_di = 100 * pd.Series(minus_dm, index=bars.index).rolling(period).sum() / atr
    dx = (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan) * 100
    adx = dx.rolling(period).mean()
    if np.isnan(adx.iloc[-1]) or np.isnan(plus_di.iloc[-1]) or np.isnan(minus_di.iloc[-1]):
        return
    adx_now = adx.iloc[-1]
    plus_now = plus_di.iloc[-1]
    minus_now = minus_di.iloc[-1]
    if adx_now >= params.get('entry', 25) and plus_now > minus_now:
        if cash > price:
            target_pct = params.get('target_percent', g.target_percent)
            target_value = portfolio_value * target_pct
            order_target_value(security, target_value)
            log.info('BUY %s @ %.2f' % (security, price))
    elif (adx_now <= params.get('exit', 20) or plus_now < minus_now) and has_position:
        order_target_value(security, 0)
        log.info('SELL %s @ %.2f' % (security, price))
    try:
        record(price=price, adx=adx_now, plus=plus_now, minus=minus_now)
    except Exception:
        pass
