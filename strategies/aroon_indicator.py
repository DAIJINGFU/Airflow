# -*- coding: utf-8 -*-

"""
Strategy: Aroon Indicator
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
    g.lookback = 120
    g.fields = ["high", "low", "close"]
    g.min_bars = 60
    g.target_percent = 1.0
    g.params = {"period": 25, "target_percent": 0.8}
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
    period = int(params.get('period', 25))
    up_index = high.rolling(period).apply(lambda x: np.argmax(x), raw=True)
    down_index = low.rolling(period).apply(lambda x: np.argmin(x), raw=True)
    aroon_up = (period - up_index) / period * 100
    aroon_down = (period - down_index) / period * 100
    if np.isnan(aroon_up.iloc[-1]) or np.isnan(aroon_down.iloc[-1]):
        return
    aroon_up_now = aroon_up.iloc[-1]
    aroon_down_now = aroon_down.iloc[-1]
    if aroon_up_now > 70 and aroon_down_now < 30:
        if cash > price:
            target_pct = params.get('target_percent', g.target_percent)
            target_value = portfolio_value * target_pct
            order_target_value(security, target_value)
            log.info('BUY %s @ %.2f' % (security, price))
    elif (aroon_down_now > 70 and aroon_up_now < 30) and has_position:
        order_target_value(security, 0)
        log.info('SELL %s @ %.2f' % (security, price))
    try:
        record(price=price, aroon_up=aroon_up_now, aroon_down=aroon_down_now)
    except Exception:
        pass
