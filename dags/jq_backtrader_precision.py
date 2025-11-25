
from __future__ import annotations

import os
import sys
import math
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import backtrader as bt
from airflow.decorators import dag, task
from airflow.exceptions import AirflowFailException

# Note: 避免在顶层导入loguru，会导致DAG导入超时

# =============================================================================
# 1. Backtrader 自定义组件 (核心交易规则实现)
#    参考原系统逻辑，但在 Backtrader 框架下重写
# =============================================================================

class CNStockCommission(bt.CommInfoBase):
    """
    A股佣金模式实现
    规则：
    1. 买入：佣金 (默认万3)
    2. 卖出：佣金 (默认万3) + 印花税 (千1)
    3. 最低佣金：5元
    """
    params = (
        ('stocklike', True),
        ('commtype', bt.CommInfoBase.COMM_PERC),
        ('perc', 0.0003),        # 默认佣金万3
        ('stamp_duty', 0.001),   # 印花税千1
        ('min_comm', 5.0),       # 最低佣金5元
    )

    def _getcommission(self, size, price, pseudoexec):
        """
        计算手续费
        size > 0 为买入，size < 0 为卖出
        """
        if pseudoexec:
            return 0.0

        # 基础交易额
        value = abs(size) * price
        
        # 1. 计算基础佣金
        commission = value * self.p.perc
        # 最低佣金限制
        if commission < self.p.min_comm:
            commission = self.p.min_comm
            
        # 2. 如果是卖出 (size < 0)，额外加印花税
        if size < 0:
            stamp_duty = value * self.p.stamp_duty
            commission += stamp_duty
            
        return commission

class LotSizeSizer(bt.Sizer):
    """
    A股手数限制管理器
    规则：买卖必须是100股的整数倍
    """
    params = (('percents', 100),)

    def _getsizing(self, comminfo, cash, data, isbuy):
        if isbuy:
            # 计算最大可买股数
            # 预留一部分资金给手续费 (粗略估计1%)
            target_cash = cash * 0.99
            price = data.close[0]
            if price <= 0:
                return 0
            
            shares = int(target_cash / price)
            # 向下取整到100的倍数
            shares = (shares // 100) * 100
            return shares
        
        # 卖出时，Backtrader 默认逻辑通常是全仓卖出或指定数量
        # 这里我们假设策略控制卖出逻辑，Sizer主要辅助买入计算
        # 如果需要全仓卖出，返回 position.size 即可
        position = self.broker.getposition(data)
        if not position.size:
            return 0
        return position.size

# =============================================================================
# 2. 策略基类与具体策略
# =============================================================================

class BaseCNStrategy(bt.Strategy):
    """
    中国股市策略基类
    包含：
    - 订单日志记录
    - 交易日志记录
    - 简单的 T+1 逻辑辅助 (通过 self.bar_executed 记录)
    """
    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'[{dt.isoformat()}] {txt}')

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
            elif order.issell():
                self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
            
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log(f'OPERATION PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}')

class DualMovingAverageStrategy(BaseCNStrategy):
    """
    双均线策略
    - 5日均线上穿20日均线 -> 全仓买入
    - 5日均线下穿20日均线 -> 全仓卖出
    """
    params = (
        ('fast_period', 5),
        ('slow_period', 20),
    )

    def __init__(self):
        # 初始化订单跟踪变量
        self.order = None
        
        self.sma_fast = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.fast_period)
        self.sma_slow = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.slow_period)
        
        self.crossover = bt.indicators.CrossOver(self.sma_fast, self.sma_slow)

    def next(self):
        # 检查是否已有订单在处理中
        if self.order:
            return

        # 检查是否持仓
        if not self.position:
            # 金叉买入 (1.0 表示向上突破)
            if self.crossover > 0:
                self.log(f'Buy Create, {self.datas[0].close[0]:.2f}')
                self.order = self.buy() # Sizer 会自动计算数量
        else:
            # 死叉卖出 (-1.0 表示向下突破)
            if self.crossover < 0:
                self.log(f'Sell Create, {self.datas[0].close[0]:.2f}')
                self.order = self.sell()

class MomentumStrategy(BaseCNStrategy):
    """
    动量策略
    - 过去10天涨幅 > 5% -> 买入
    - 过去10天跌幅 < -2% -> 卖出
    """
    params = (
        ('period', 10),
        ('buy_threshold', 0.05),
        ('sell_threshold', -0.02),
    )

    def __init__(self):
        # 初始化订单跟踪变量
        self.order = None

    def next(self):
        if self.order:
            return

        # 确保有足够的数据
        if len(self.datas[0]) < self.params.period:
            return

        current_price = self.datas[0].close[0]
        past_price = self.datas[0].close[-self.params.period]
        
        if past_price == 0:
            return
            
        momentum = (current_price - past_price) / past_price

        if not self.position:
            if momentum > self.params.buy_threshold:
                self.log(f'Momentum {momentum:.2%} > {self.params.buy_threshold:.2%}, Buy Create')
                self.order = self.buy()
        else:
            if momentum < self.params.sell_threshold:
                self.log(f'Momentum {momentum:.2%} < {self.params.sell_threshold:.2%}, Sell Create')
                self.order = self.sell()

# 映射策略名称到类
STRATEGY_REGISTRY = {
    "dual_ma": DualMovingAverageStrategy,
    "momentum": MomentumStrategy
}

# =============================================================================
# 3. Airflow Tasks
# =============================================================================

def _generate_mock_csv(path: Path):
    """生成符合 Backtrader 格式的模拟数据"""
    dates = pd.date_range(end=datetime.now(), periods=252, freq='B')
    data = []
    price = 100.0
    for d in dates:
        change = random.uniform(-0.05, 0.05)
        price *= (1 + change)
        high = price * (1 + random.uniform(0, 0.02))
        low = price * (1 - random.uniform(0, 0.02))
        open_p = (high + low) / 2
        vol = random.randint(10000, 50000)
        # 将日期转换为字符串格式 YYYY-MM-DD
        data.append([d.strftime('%Y-%m-%d'), open_p, high, low, price, vol, 0]) # Last 0 is OpenInterest
    
    df = pd.DataFrame(data, columns=['datetime', 'open', 'high', 'low', 'close', 'volume', 'openinterest'])
    df.to_csv(path, index=False)
    print(f"Generated mock data at {path}")

@task
def prepare_backtrader_data() -> Dict[str, str]:
    """
    准备数据任务
    1. 优先查找本地 stockdata
    2. 找不到则生成 Mock 数据
    3. 返回包含数据文件路径的字典（兼容Airflow 3.x XCom）
    """
    # 尝试查找真实数据 (假设挂载路径)
    real_data_path = Path("/opt/airflow/stockdata/1d_1w_1m/000001/000001_daily_qfq.csv")
    temp_data_path = Path("/opt/airflow/logs/bt_temp_data.csv")
    
    if real_data_path.exists():
        print(f"Using real data from {real_data_path}")
        # Backtrader GenericCSVData 需要特定格式，这里做简单的清洗和转换
        try:
            df = pd.read_csv(real_data_path)
            # 假设列名是中文，需要映射
            # 常见格式: 日期,开盘,收盘,最高,最低,成交量,成交额,振幅,涨跌幅,涨跌额,换手率
            rename_map = {
                '日期': 'datetime', 'date': 'datetime',
                '开盘': 'open', 'open': 'open',
                '收盘': 'close', 'close': 'close',
                '最高': 'high', 'high': 'high',
                '最低': 'low', 'low': 'low',
                '成交量': 'volume', 'volume': 'volume'
            }
            df.rename(columns=rename_map, inplace=True)
            df['openinterest'] = 0
            
            # 确保包含必要列
            required = ['datetime', 'open', 'high', 'low', 'close', 'volume', 'openinterest']
            if not all(col in df.columns for col in required):
                print("Real data missing columns, falling back to mock.")
                _generate_mock_csv(temp_data_path)
            else:
                df[required].to_csv(temp_data_path, index=False)
        except Exception as e:
            print(f"Error processing real data: {e}")
            _generate_mock_csv(temp_data_path)
    else:
        print("Real data not found, generating mock data.")
        _generate_mock_csv(temp_data_path)
        
    return {"data_path": str(temp_data_path)}

@task
def run_backtrader_strategy(strategy_name: str, data_path: Dict[str, str]) -> Dict[str, Any]:
    """
    运行 Backtrader 回测
    """
    cerebro = bt.Cerebro()
    
    # 1. 加载数据
    # GenericCSVData 参数配置
    data = bt.feeds.GenericCSVData(
        dataname=data_path["data_path"],  # 从字典中提取路径
        dtformat='%Y-%m-%d', # 假设日期格式 YYYY-MM-DD
        datetime=0,
        open=1,
        high=2,
        low=3,
        close=4,
        volume=5,
        openinterest=6,
        timeframe=bt.TimeFrame.Days
    )
    cerebro.adddata(data)
    
    # 2. 设置资金
    start_cash = 1_000_000.0
    cerebro.broker.setcash(start_cash)
    
    # 3. 设置 A股 佣金模式 (自定义类)
    comminfo = CNStockCommission()
    cerebro.broker.addcommissioninfo(comminfo)
    
    # 4. 设置 A股 手数限制 (自定义 Sizer)
    cerebro.addsizer(LotSizeSizer)
    
    # 5. 添加策略
    strategy_class = STRATEGY_REGISTRY.get(strategy_name)
    if not strategy_class:
        raise AirflowFailException(f"Unknown strategy: {strategy_name}")
    
    cerebro.addstrategy(strategy_class)
    
    # 6. 添加分析器
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    
    # 7. 运行
    print(f"Starting Backtrader for {strategy_name}...")
    results = cerebro.run()
    strat = results[0]
    
    # 8. 提取结果
    final_value = cerebro.broker.getvalue()
    
    # 安全获取分析器结果 (有些分析器在数据不足时返回 None)
    sharpe_info = strat.analyzers.sharpe.get_analysis()
    sharpe_ratio = sharpe_info.get('sharperatio', 0.0)
    
    drawdown_info = strat.analyzers.drawdown.get_analysis()
    max_drawdown = drawdown_info.get('max', {}).get('drawdown', 0.0)
    
    returns_info = strat.analyzers.returns.get_analysis()
    total_return = returns_info.get('rtot', 0.0) # 对数收益率
    
    return {
        "strategy": strategy_name,
        "start_cash": start_cash,
        "final_value": final_value,
        "total_return_pct": (final_value - start_cash) / start_cash * 100,
        "sharpe_ratio": sharpe_ratio if sharpe_ratio is not None else 0,
        "max_drawdown": max_drawdown,
        "status": "SUCCESS"
    }

@task
def generate_precision_report(results: List[Dict[str, Any]]):
    """生成最终报告"""
    print("\n" + "="*80)
    print("   BACKTRADER PRECISION BACKTEST REPORT")
    print("   (Features: CN Commission, Min 5 RMB, Board Lot 100)")
    print("="*80)
    
    # 转换为 DataFrame 展示
    df = pd.DataFrame(results)
    # 格式化列
    if not df.empty:
        cols = ['strategy', 'final_value', 'total_return_pct', 'sharpe_ratio', 'max_drawdown']
        print(df[cols].to_markdown(index=False, floatfmt=".2f"))
    else:
        print("No results to display.")
        
    print("="*80 + "\n")

# =============================================================================
# 4. DAG Definition
# =============================================================================

@dag(
    dag_id="jq_backtrader_precision",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["quant", "backtrader", "precision"],
    description="High-precision backtest system using Backtrader with CN market rules."
)
def backtrader_precision_dag():
    # 1. 准备数据
    data_path = prepare_backtrader_data()
    
    # 2. 定义策略列表
    strategies = ["dual_ma", "momentum"]
    
    # 3. 并发运行 - 使用 partial 固定 data_path，只在 strategy_name 上展开
    results = run_backtrader_strategy.partial(data_path=data_path).expand(strategy_name=strategies)
    
    # 4. 汇总
    generate_precision_report(results)

dag = backtrader_precision_dag()
