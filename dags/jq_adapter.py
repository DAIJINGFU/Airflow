"""
JoinQuant API 到 Backtrader 的适配层

本模块提供 JoinQuant 量化平台 API 的 Backtrader 实现，
使得 JoinQuant 格式的策略代码可以在 Backtrader 引擎中运行。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import pandas as pd
import backtrader as bt


# =============================================================================
# 1. 全局对象模拟
# =============================================================================

class GlobalContext:
    """模拟 JoinQuant 的 g 对象（全局上下文）"""
    
    def __init__(self):
        self.reset()
        
    def reset(self):
        """重置上下文，避免不同回测之间的数据串扰"""
        object.__setattr__(self, 'security', None)   # 股票代码
        object.__setattr__(self, 'unit', '1d')       # 数据频率
        object.__setattr__(self, 'lookback', 60)     # 回看天数
        object.__setattr__(self, 'params', {})       # 策略参数
        object.__setattr__(self, 'benchmark', None)  # 基准
        object.__setattr__(self, 'options', {})      # 运行选项
        
    def __setattr__(self, name: str, value: Any):
        """允许动态设置任意属性"""
        object.__setattr__(self, name, value)
    
    def __getattr__(self, name: str):
        """访问不存在属性时返回 None 而不是抛出异常"""
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            return None


class ContextObject:
    """模拟 JoinQuant 的 context 对象"""
    
    def __init__(self, strategy: bt.Strategy):
        self._strategy = strategy
        self.portfolio = PortfolioObject(strategy)
        self.current_dt = None  # 当前时间
        self.previous_date = None  # 前一交易日
        
    def update_datetime(self, dt: datetime):
        """更新当前时间"""
        self.current_dt = dt


class PortfolioObject:
    """模拟 JoinQuant 的 portfolio 对象"""
    
    def __init__(self, strategy: bt.Strategy):
        self._strategy = strategy
    
    @property
    def available_cash(self) -> float:
        """可用资金"""
        return self._strategy.broker.getcash()
    
    @property
    def total_value(self) -> float:
        """总资产"""
        return self._strategy.broker.getvalue()
    
    @property
    def positions(self) -> Dict[str, Any]:
        """持仓信息"""
        positions = {}
        for data in self._strategy.datas:
            pos = self._strategy.getposition(data)
            if pos.size != 0:
                positions[data._name] = PositionObject(pos, data)
        return positions
    
    @property
    def positions_value(self) -> float:
        """持仓市值"""
        return self.total_value - self.available_cash


class PositionObject:
    """模拟 JoinQuant 的 position 对象"""
    
    def __init__(self, position, data):
        self._position = position
        self._data = data
    
    @property
    def total_amount(self) -> int:
        """持仓数量"""
        return int(self._position.size)
    
    @property
    def closeable_amount(self) -> int:
        """可卖出数量（A股 T+1，这里简化处理）"""
        return int(self._position.size)
    
    @property
    def avg_cost(self) -> float:
        """持仓成本价"""
        return self._position.price
    
    @property
    def price(self) -> float:
        """当前价格"""
        return self._data.close[0]
    
    @property
    def value(self) -> float:
        """持仓市值"""
        return self.total_amount * self.price


class DataObject:
    """模拟 JoinQuant 的 data 对象（用于访问行情数据）"""
    
    def __init__(self, strategy: bt.Strategy):
        self._strategy = strategy
        self._data_cache = {}
    
    def __getitem__(self, security: str):
        """获取指定股票的数据"""
        # 查找对应的 data feed
        for data in self._strategy.datas:
            if data._name == security:
                return SecurityDataObject(data)
        
        # 如果未找到，返回空对象
        return SecurityDataObject(None)


class SecurityDataObject:
    """单只股票的行情数据对象"""
    
    def __init__(self, data: Optional[bt.DataBase]):
        self._data = data
    
    @property
    def close(self) -> float:
        """收盘价"""
        return self._data.close[0] if self._data else 0.0
    
    @property
    def open(self) -> float:
        """开盘价"""
        return self._data.open[0] if self._data else 0.0
    
    @property
    def high(self) -> float:
        """最高价"""
        return self._data.high[0] if self._data else 0.0
    
    @property
    def low(self) -> float:
        """最低价"""
        return self._data.low[0] if self._data else 0.0
    
    @property
    def volume(self) -> float:
        """成交量"""
        return self._data.volume[0] if self._data else 0.0


# =============================================================================
# 2. JoinQuant API 函数实现
# =============================================================================

def attribute_history(
    security: str,
    count: int,
    unit: str = '1d',
    fields: Optional[List[str]] = None,
    skip_paused: bool = False,
    df: bool = True,
    fq: str = 'pre'
) -> pd.DataFrame:
    """
    获取历史数据
    
    注意：此函数需要在策略上下文中调用，通过全局变量访问 strategy 实例
    
    优化点：
    - 使用 get() 方法批量提取数据，提升性能
    - 增强数据不足时的警告提示
    - 改进错误处理
    """
    # 从全局上下文获取策略实例
    strategy = _get_current_strategy()
    if not strategy:
        raise RuntimeError("attribute_history must be called within strategy context")
    
    # 查找对应的 data feed
    data_feed = None
    for data in strategy.datas:
        if data._name == security:
            data_feed = data
            break
    
    if not data_feed:
        print(f"[WARNING] attribute_history: 未找到股票 {security} 的数据")
        return pd.DataFrame()
    
    # 默认字段
    if fields is None:
        fields = ['open', 'close', 'high', 'low', 'volume']
    
    # 提取历史数据（优化：使用批量获取）
    result = {}
    for field in fields:
        if hasattr(data_feed, field):
            line = getattr(data_feed, field)
            try:
                # 优化：使用 get() 方法批量获取数据
                values = line.get(ago=-count+1, size=count)
                if values is None or len(values) == 0:
                    # 数据不足，尝试逐个获取
                    values = []
                    for i in range(count - 1, -1, -1):
                        try:
                            values.append(line[-i])
                        except (IndexError, KeyError):
                            pass
                    if len(values) < count:
                        print(f"[WARNING] attribute_history: 数据不足，请求 {count} 条，实际获取 {len(values)} 条")
                result[field] = values
            except Exception as e:
                print(f"[ERROR] attribute_history: 提取字段 '{field}' 失败: {e}")
                result[field] = []
    
    return pd.DataFrame(result) if df else result


def get_price(
    security: Union[str, List[str]],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    frequency: str = 'daily',
    fields: Optional[List[str]] = None,
    skip_paused: bool = False,
    fq: str = 'pre',
    count: Optional[int] = None
) -> Union[pd.DataFrame, pd.Panel]:
    """
    获取历史行情数据
    
    简化版本：主要用于获取当前价格
    """
    strategy = _get_current_strategy()
    if not strategy:
        raise RuntimeError("get_price must be called within strategy context")
    
    # 如果只请求单只股票的当前价格
    if isinstance(security, str) and not start_date and not end_date:
        for data in strategy.datas:
            if data._name == security:
                if fields:
                    result = {}
                    for field in fields:
                        if hasattr(data, field):
                            result[field] = getattr(data, field)[0]
                    return pd.Series(result)
                else:
                    return data.close[0]
    
    # 复杂查询暂不支持，返回空
    return pd.DataFrame()


def order(security: str, amount: int, style: Optional[Any] = None, side: str = 'long'):
    """
    按股数下单
    
    amount > 0: 买入
    amount < 0: 卖出
    """
    strategy = _get_current_strategy()
    if not strategy:
        return None
    
    # 查找对应的 data feed
    data_feed = None
    for data in strategy.datas:
        if data._name == security:
            data_feed = data
            break
    
    if not data_feed:
        return None
    
    # 执行订单
    if amount > 0:
        return strategy.buy(data=data_feed, size=amount)
    elif amount < 0:
        return strategy.sell(data=data_feed, size=abs(amount))
    
    return None


def order_value(security: str, value: float, style: Optional[Any] = None):
    """
    按金额下单
    
    value > 0: 买入
    value < 0: 卖出
    """
    strategy = _get_current_strategy()
    if not strategy:
        return None
    
    # 查找对应的 data feed
    data_feed = None
    for data in strategy.datas:
        if data._name == security:
            data_feed = data
            break
    
    if not data_feed:
        return None
    
    # 计算股数（A股100股一手）
    current_price = data_feed.close[0]
    if current_price <= 0:
        return None
    
    amount = int(value / current_price / 100) * 100  # 向下取整到100的倍数
    
    # 执行订单
    if amount > 0:
        return strategy.buy(data=data_feed, size=amount)
    elif amount < 0:
        return strategy.sell(data=data_feed, size=abs(amount))
    
    return None


def order_target(security: str, amount: int, style: Optional[Any] = None):
    """
    调整持仓到目标股数
    
    amount: 目标持仓数量
    """
    strategy = _get_current_strategy()
    if not strategy:
        return None
    
    # 查找对应的 data feed
    data_feed = None
    for data in strategy.datas:
        if data._name == security:
            data_feed = data
            break
    
    if not data_feed:
        return None
    
    # 计算需要交易的数量
    current_position = strategy.getposition(data_feed).size
    delta = amount - current_position
    
    if delta > 0:
        return strategy.buy(data=data_feed, size=delta)
    elif delta < 0:
        return strategy.sell(data=data_feed, size=abs(delta))
    
    return None


def order_target_value(security: str, value: float, style: Optional[Any] = None):
    """
    调整持仓到目标市值
    
    value: 目标持仓市值
    """
    strategy = _get_current_strategy()
    if not strategy:
        return None
    
    # 查找对应的 data feed
    data_feed = None
    for data in strategy.datas:
        if data._name == security:
            data_feed = data
            break
    
    if not data_feed:
        return None
    
    # 计算目标股数
    current_price = data_feed.close[0]
    if current_price <= 0:
        return None
    
    target_amount = int(value / current_price / 100) * 100
    
    # 使用 order_target
    return order_target(security, target_amount)


def set_benchmark(security: str):
    """设置基准指数（暂不实现）"""
    pass


def set_option(key: str, value: Any):
    """设置运行选项（暂不实现）"""
    pass


def run_daily(func, time: str = 'open', reference_security: Optional[str] = None):
    """注册每日定时任务（暂不实现）"""
    pass


def run_weekly(func, weekday: int, time: str = 'open', reference_security: Optional[str] = None):
    """注册每周定时任务（暂不实现）"""
    pass


def run_monthly(func, monthday: int, time: str = 'open', reference_security: Optional[str] = None):
    """注册每月定时任务（暂不实现）"""
    pass


def log(*args, **kwargs):
    """日志输出"""
    print(*args, **kwargs)


# 创建 log 对象with info/warning/error 方法
class Logger:
    """模拟 JoinQuant 的 log 对象"""
    @staticmethod
    def info(*args, **kwargs):
        print("[INFO]", *args, **kwargs)
    
    @staticmethod
    def warn(*args, **kwargs):
        print("[WARN]", *args, **kwargs)
    
    @staticmethod
    def warning(*args, **kwargs):
        print("[WARNING]", *args, **kwargs)
    
    @staticmethod
    def error(*args, **kwargs):
        print("[ERROR]", *args, **kwargs)
    
    @staticmethod
    def debug(*args, **kwargs):
        print("[DEBUG]", *args, **kwargs)


log = Logger()


def record(**kwargs):
    """记录自定义数据（暂不实现，仅打印）"""
    print(f"[RECORD] {kwargs}")


# =============================================================================
# 3. 全局变量和辅助函数
# =============================================================================

# 全局上下文对象
g = GlobalContext()

# 当前策略实例（通过 thread-local 或全局变量存储）
_current_strategy: Optional[bt.Strategy] = None


def _set_current_strategy(strategy: bt.Strategy):
    """设置当前策略实例"""
    global _current_strategy
    _current_strategy = strategy


def _get_current_strategy() -> Optional[bt.Strategy]:
    """获取当前策略实例"""
    return _current_strategy


def reset_global_context():
    """对外暴露的 g.reset()，便于在任务之间清理状态"""
    g.reset()


# =============================================================================
# 4. JoinQuant 策略适配器
# =============================================================================

class JQStrategyAdapter(bt.Strategy):
    """
    JoinQuant 策略适配器
    
    将 JoinQuant 格式的策略代码（initialize + handle_data）
    转换为 Backtrader 策略类
    """
    
    params = (
        ('jq_initialize', None),     # JoinQuant initialize 函数
        ('jq_handle_data', None),    # JoinQuant handle_data 函数
        ('data_frequency', 'day'),   # 回测频率
        ('benchmark', None),         # 基准代码
    )
    
    def __init__(self):
        # 设置全局策略实例
        _set_current_strategy(self)
        g.reset()
        g.unit = self.params.data_frequency
        g.benchmark = self.params.benchmark
        g.params = {
            'frequency': self.params.data_frequency,
            'benchmark': self.params.benchmark,
        }
        
        # 创建 context 和 data 对象
        self.context = ContextObject(self)
        self.data_obj = DataObject(self)
        
        # 调用 JoinQuant 的 initialize 函数
        if self.params.jq_initialize:
            self.params.jq_initialize(self.context)
    
    def next(self):
        """每个交易周期调用"""
        try:
            # 更新当前时间
            self.context.update_datetime(self.datas[0].datetime.datetime(0))
            
            # 设置全局策略实例（确保在 handle_data 中可访问）
            _set_current_strategy(self)
            
            # 调用 JoinQuant 的 handle_data 函数
            if self.params.jq_handle_data:
                self.params.jq_handle_data(self.context, self.data_obj)
        except Exception as e:
            # 捕获用户策略代码中的异常，打印详细信息但不中断回测
            current_date = self.datas[0].datetime.date(0)
            print(f"[ERROR] 策略执行异常 (日期: {current_date}): {type(e).__name__}: {e}")
            import traceback
            print(traceback.format_exc())


# =============================================================================
# 5. 导出模块
# =============================================================================

__all__ = [
    # 全局对象
    'g',
    'log',
    'GlobalContext',
    'ContextObject',
    'DataObject',
    
    # API 函数
    'attribute_history',
    'get_price',
    'order',
    'order_value',
    'order_target',
    'order_target_value',
    'set_benchmark',
    'set_option',
    'run_daily',
    'run_weekly',
    'run_monthly',
    'record',
    
    # 策略适配器
    'JQStrategyAdapter',
    
    # 辅助函数
    '_set_current_strategy',
    '_get_current_strategy',
    'reset_global_context',
]
