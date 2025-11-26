# -*- coding: utf-8 -*-
"""
Strategy: Announcement Reaction
Frequency: Daily
Note: Monitors opening gaps and reacts accordingly.
"""

from jqdata import *


def initialize(context):
    set_benchmark('000300.XSHG')
    set_option('use_real_price', True)
    g.security = '000001.XSHE'
    g.positive_gap = 0.04
    g.negative_gap = -0.03
    g.hold_days = 3
    g.holding_days = 0
    run_daily(handle, time='open')


def handle(context):
    security = g.security
    bars = attribute_history(security, 3, '1d', ['open', 'close'], skip_paused=True, df=True)
    if bars is None or bars.empty or len(bars) < 2:
        return
    bars = bars.dropna()
    if len(bars) < 2:
        return

    prev_close = bars['close'].iloc[-2]
    today_open = bars['open'].iloc[-1]
    if prev_close <= 0:
        return

    gap = (today_open - prev_close) / prev_close
    positions = context.portfolio.positions
    position = None
    if hasattr(positions, '__contains__') and security in positions:
        position = positions[security]
    elif hasattr(positions, 'get'):
        position = positions.get(security)
    has_position = position is not None and getattr(position, 'closeable_amount', 0) > 0

    if has_position:
        g.holding_days = max(0, g.holding_days - 1)

    if gap >= g.positive_gap:
        if has_position:
            order_target_value(security, 0)
            log.info('Gap down exit %s gap=%.2f' % (security, gap))
        g.holding_days = 0
        return

    if gap <= g.negative_gap:
        target_value = context.portfolio.total_value * 0.6
        order_target_value(security, target_value)
        g.holding_days = g.hold_days
        log.info('Gap up buy %s gap=%.2f' % (security, gap))
    elif g.holding_days == 0 and has_position:
        order_target_value(security, 0)
        log.info('Holding window ended, flat position %s' % security)

    try:
        record(gap=gap)
    except Exception:
        pass
