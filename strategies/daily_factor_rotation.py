# -*- coding: utf-8 -*-
"""
Strategy: Daily Factor Rotation
Frequency: daily
Note: Auto-generated allocation strategy.
"""

from jqdata import *
import numpy as np
import pandas as pd


def initialize(context):
    set_benchmark('000300.XSHG')
    set_option('use_real_price', True)
    g.max_positions = 3
    g.cash_buffer = 0.1
    g.universe = ['000300.XSHG', '399005.XSHE', '510300.XSHG', '510500.XSHG', '159915.XSHE', '512100.XSHG']
    run_monthly(rebalance, 1, time='open')


def handle_data(context, data):
    if 'monthly' == 'daily':
        return


def rebalance(context):
    max_positions = g.max_positions
    cash_buffer = g.cash_buffer
    selected = []
    candidates = g.universe
    scores = []
    for asset in candidates:
        hist = get_price(asset, count=60, frequency='daily', fields=['close'])
        if hist is None or hist.empty:
            continue
        closes = hist['close']
        if len(closes) < 2:
            continue
        ret = closes[-1] / closes[0] - 1
        scores.append((asset, ret))
    if not scores:
        return
    scores.sort(key=lambda x: x[1], reverse=True)
    for asset, _ in scores:
        selected.append(asset)
    selected = list(dict.fromkeys(selected))
    selected = selected[:max_positions]
    current_positions = list(context.portfolio.positions.keys())
    total_value = context.portfolio.total_value
    if not selected:
        for asset in current_positions:
            order_target_value(asset, 0)
        return
    weight = (1 - cash_buffer) / len(selected)
    for asset in selected:
        order_target_value(asset, total_value * weight)
    for asset in current_positions:
        if asset not in selected:
            order_target_value(asset, 0)
