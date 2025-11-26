# 聚宽（JoinQuant）策略代码格式说明

> **文档目的**: 说明通用回测平台支持的策略代码格式规范
>
> **适用范围**: Airflow `universal_backtest_platform` DAG
>
> **策略来源**: 基于聚宽（JoinQuant）量化平台的策略语法

---

## 📋 目录

- [快速开始](#快速开始)
- [核心结构](#核心结构)
- [关键 API](#关键-api)
- [策略示例](#策略示例)
- [与 Backtrader 的区别](#与-backtrader-的区别)
- [常见问题](#常见问题)

---

## 🚀 快速开始

### 最简单的策略模板

```python
from jqdata import *

def initialize(context):
    # ⭐ 必须指定股票代码
    g.security = '000001.XSHE'
    set_benchmark('000300.XSHG')
    set_option('use_real_price', True)

def handle_data(context, data):
    security = g.security
    current_price = data[security].close

    # 策略逻辑
    if 买入条件:
        order_value(security, context.portfolio.available_cash)
    elif 卖出条件:
        order_target(security, 0)
```

### 用户输入参数

用户在 Airflow Web UI 中只需填写：

1. **策略代码**（必填）⭐ - 包含 `g.security` 股票代码定义
2. **起始日期** - 如 `2023-01-01`
3. **结束日期** - 如 `2024-12-31`
4. **初始资金** - 如 `100000`
5. **回测频率** - 日线/周线/月线
6. **策略名称**（可选）- 留空自动生成

**系统自动配置**:

- 佣金率: 0.0003 (万三)
- 印花税: 0.001 (千一，仅卖出)
- 最低佣金: 5 元

---

## 🏗️ 核心结构

### 1. 必需函数

#### `initialize(context)` - 初始化函数

在回测开始时调用一次，用于设置全局参数。

```python
def initialize(context):
    # 设置基准指数
    set_benchmark('000300.XSHG')  # 沪深300

    # 开启真实价格模式（考虑涨跌停、停牌）
    set_option('use_real_price', True)

    # ⭐ 必须定义：指定交易股票代码
    g.security = '000001.XSHE'  # 平安银行

    # 可选：策略参数
    g.unit = '1d'           # 数据频率：'1d'日线, '1w'周线, '1m'分钟线
    g.lookback = 60         # 历史数据回看天数
    g.params = {            # 策略超参数
        'period': 20,
        'target_percent': 0.9
    }

    # 可选：定时任务
    run_daily(handle_daily, time='open')    # 每日开盘时执行
    run_monthly(rebalance, 1, time='open')  # 每月1号执行
```

**关键全局变量**:

- `g.security` ⭐ **必需** - 股票代码
- `g.unit` - 数据频率
- `g.params` - 策略参数字典
- `g.*` - 任意自定义全局变量

#### `handle_data(context, data)` - 主逻辑函数

每个交易周期（日/周/月/分钟）调用一次。

```python
def handle_data(context, data):
    security = g.security

    # 获取当前价格
    current_price = data[security].close

    # 获取资金和持仓
    cash = context.portfolio.available_cash
    position = context.portfolio.positions.get(security)

    # 策略逻辑
    if 买入条件 and cash > current_price:
        order_value(security, cash)  # 全仓买入
        log.info("买入 %s @ %.2f" % (security, current_price))

    if 卖出条件 and position and position.closeable_amount > 0:
        order_target(security, 0)  # 清仓
        log.info("卖出 %s @ %.2f" % (security, current_price))
```

**`context` 对象属性**:

- `context.portfolio.available_cash` - 可用资金
- `context.portfolio.total_value` - 总资产（现金+持仓市值）
- `context.portfolio.positions` - 持仓字典 `{股票代码: 持仓对象}`
- `context.portfolio.positions[security].closeable_amount` - 可卖出数量

**`data` 对象用法**:

- `data[security].close` - 最新收盘价
- `data[security].open` - 最新开盘价
- `data[security].high` - 最新最高价
- `data[security].low` - 最新最低价

---

### 2. 可选函数

#### 自定义定时任务

```python
def initialize(context):
    run_daily(my_function, time='open')   # 每日开盘
    run_weekly(my_function, 1, time='14:50')  # 每周一14:50
    run_monthly(my_function, 1, time='open')  # 每月1号

def my_function(context):
    # 自定义逻辑
    pass
```

---

## 🔧 关键 API

### 数据获取

#### `attribute_history()` - 获取历史行情

```python
# 获取最近60天的日线数据
bars = attribute_history(
    security='000001.XSHE',     # 股票代码
    count=60,                   # 数据条数
    unit='1d',                  # 频率：'1d'日, '1w'周, '1m'分钟
    fields=['close', 'high', 'low', 'open', 'volume'],  # 字段
    skip_paused=True,           # 跳过停牌日
    df=True                     # 返回DataFrame（推荐）
)

# 返回 pandas.DataFrame
print(bars.head())
#             close    high     low    open  volume
# 2023-01-01  10.50   10.80   10.20   10.30  1000000
# 2023-01-02  10.60   10.90   10.40   10.50  1200000
```

**参数说明**:

- `security`: 股票代码（如 `'000001.XSHE'`）
- `count`: 获取最近 N 条数据
- `unit`:
  - `'1d'` - 日线
  - `'1w'` - 周线
  - `'1m'` - 分钟线
- `fields`: 数据字段列表
  - `'close'` - 收盘价
  - `'open'` - 开盘价
  - `'high'` - 最高价
  - `'low'` - 最低价
  - `'volume'` - 成交量
  - `'money'` - 成交额

#### `get_price()` - 获取价格数据（备用）

```python
# 获取最近30天收盘价
hist = get_price(
    '000001.XSHE',
    count=30,
    frequency='daily',  # 'daily', 'minute'
    fields=['close']
)
```

---

### 交易操作

#### `order_value(security, cash)` - 买入指定金额

```python
# 用10000元买入股票
order_value('000001.XSHE', 10000)

# 全仓买入
cash = context.portfolio.available_cash
order_value(security, cash)
```

#### `order_target(security, amount)` - 调整持仓到目标数量

```python
# 持仓调整到1000股
order_target('000001.XSHE', 1000)

# 清仓（卖出所有）
order_target('000001.XSHE', 0)
```

#### `order_target_value(security, value)` - 调整持仓到目标市值

```python
# 持仓市值调整到总资产的80%
total_value = context.portfolio.total_value
order_target_value(security, total_value * 0.8)

# 清仓
order_target_value(security, 0)
```

#### `order(security, amount)` - 买入/卖出指定数量

```python
# 买入100股
order('000001.XSHE', 100)

# 卖出100股
order('000001.XSHE', -100)
```

---

### 持仓查询

```python
def handle_data(context, data):
    security = g.security

    # 获取持仓对象
    position = context.portfolio.positions.get(security)

    # 检查是否有持仓
    if position is None:
        print("没有持仓")
    else:
        print("可卖数量:", position.closeable_amount)
        print("持仓成本:", position.avg_cost)
        print("当前市值:", position.value)
        print("持仓盈亏:", position.value - position.avg_cost * position.closeable_amount)
```

**持仓对象属性**:

- `closeable_amount` - 可卖出数量（T+1，当天买入不可卖）
- `total_amount` - 总持仓数量
- `avg_cost` - 持仓成本价
- `value` - 当前市值

---

### 日志输出

```python
log.info("这是普通日志")
log.warn("这是警告日志")
log.error("这是错误日志")

# 格式化输出
log.info("买入 %s @ 价格 %.2f" % (security, price))
```

---

### 指标绘制（可选）

```python
# 记录指标到图表
record(
    price=current_price,
    ma5=ma5,
    position_value=context.portfolio.positions_value
)
```

---

## 📚 策略示例

### 示例 1: 简单均线策略 (MA5)

```python
from jqdata import *

def initialize(context):
    g.security = '000514.XSHE'
    set_benchmark('000300.XSHG')
    set_option('use_real_price', True)

def handle_data(context, data):
    security = g.security

    # 获取最近5天收盘价
    close_data = attribute_history(security, 5, '1d', ['close'])
    ma5 = close_data['close'].mean()
    current_price = close_data['close'][-1]
    cash = context.portfolio.available_cash

    # 价格突破MA5上方5%，全仓买入
    if current_price > 1.05 * ma5 and cash > 0:
        order_value(security, cash)
        log.info("买入 %s" % security)

    # 价格跌破MA5下方5%，清仓
    elif current_price < 0.95 * ma5:
        position = context.portfolio.positions.get(security)
        if position and position.closeable_amount > 0:
            order_target(security, 0)
            log.info("卖出 %s" % security)
```

---

### 示例 2: ADX 趋势强度策略

```python
from jqdata import *
import numpy as np
import pandas as pd

def initialize(context):
    set_benchmark("000300.XSHG")
    set_option("use_real_price", True)
    g.security = "000001.XSHE"
    g.params = {
        "period": 14,      # ADX周期
        "entry": 25,       # 入场阈值
        "exit": 20,        # 出场阈值
        "target_percent": 0.9  # 仓位比例
    }
    run_daily(handle_daily, time='open')

def handle_daily(context):
    security = g.security
    params = g.params

    # 获取历史数据
    bars = attribute_history(security, 80, '1d', ['high', 'low', 'close'],
                            skip_paused=True, df=True)

    if len(bars) < 50:
        return

    # 计算ADX指标
    period = params['period']
    high = bars['high']
    low = bars['low']
    close = bars['close']

    # +DM 和 -DM
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    # ATR
    tr_components = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1)
    true_range = tr_components.max(axis=1)
    atr = true_range.rolling(period).mean()

    # +DI 和 -DI
    plus_di = 100 * pd.Series(plus_dm).rolling(period).sum() / atr
    minus_di = 100 * pd.Series(minus_dm).rolling(period).sum() / atr

    # ADX
    dx = (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan) * 100
    adx = dx.rolling(period).mean()

    if np.isnan(adx.iloc[-1]):
        return

    adx_now = adx.iloc[-1]
    plus_now = plus_di.iloc[-1]
    minus_now = minus_di.iloc[-1]

    price = bars['close'].iloc[-1]
    cash = context.portfolio.available_cash
    position = context.portfolio.positions.get(security)

    # 交易信号
    if adx_now >= params['entry'] and plus_now > minus_now:
        # 强趋势 + 上涨 → 买入
        if cash > price:
            target_value = context.portfolio.total_value * params['target_percent']
            order_target_value(security, target_value)
            log.info('买入 %s @ %.2f, ADX=%.2f' % (security, price, adx_now))

    elif (adx_now <= params['exit'] or plus_now < minus_now):
        # 趋势减弱 or 下跌 → 卖出
        if position and position.closeable_amount > 0:
            order_target_value(security, 0)
            log.info('卖出 %s @ %.2f, ADX=%.2f' % (security, price, adx_now))
```

---

### 示例 3: 布林带突破策略

```python
from jqdata import *
import numpy as np

def initialize(context):
    set_benchmark("000300.XSHG")
    set_option("use_real_price", True)
    g.security = "000001.XSHE"
    g.params = {
        "window": 20,           # 布林带周期
        "std_multiplier": 2.0,  # 标准差倍数
        "target_percent": 0.9   # 仓位比例
    }
    run_daily(handle_daily, time='open')

def handle_daily(context):
    security = g.security
    params = g.params

    # 获取历史数据
    bars = attribute_history(security, 60, '1d', ['close'],
                            skip_paused=True, df=True)

    if len(bars) < params['window']:
        return

    close = bars['close']

    # 计算布林带
    window = params['window']
    std_mult = params['std_multiplier']

    ma = close.rolling(window).mean()
    std = close.rolling(window).std()
    upper_band = ma + std_mult * std
    lower_band = ma - std_mult * std

    current_price = close.iloc[-1]
    upper = upper_band.iloc[-1]
    lower = lower_band.iloc[-1]

    if np.isnan(upper) or np.isnan(lower):
        return

    cash = context.portfolio.available_cash
    position = context.portfolio.positions.get(security)

    # 交易信号
    if current_price < lower and cash > current_price:
        # 突破下轨 → 买入
        target_value = context.portfolio.total_value * params['target_percent']
        order_target_value(security, target_value)
        log.info('买入 %s @ %.2f (下轨=%.2f)' % (security, current_price, lower))

    elif current_price > upper:
        # 突破上轨 → 卖出
        if position and position.closeable_amount > 0:
            order_target_value(security, 0)
            log.info('卖出 %s @ %.2f (上轨=%.2f)' % (security, current_price, upper))
```

---

### 示例 4: 多资产轮动策略

```python
from jqdata import *
import pandas as pd

def initialize(context):
    set_benchmark('000300.XSHG')
    set_option('use_real_price', True)

    # 多只股票/ETF
    g.universe = [
        '000300.XSHG',  # 沪深300
        '399005.XSHE',  # 中小板指
        '510300.XSHG',  # 沪深300ETF
        '510500.XSHG',  # 中证500ETF
    ]
    g.max_positions = 3

    run_monthly(rebalance, 1, time='open')

def rebalance(context):
    # 计算所有资产的动量（过去60天收益）
    scores = []
    for asset in g.universe:
        hist = get_price(asset, count=60, frequency='daily', fields=['close'])
        if hist is None or hist.empty or len(hist['close']) < 2:
            continue

        ret = hist['close'][-1] / hist['close'][0] - 1
        scores.append((asset, ret))

    if not scores:
        return

    # 按收益率排序，选择前N名
    scores.sort(key=lambda x: x[1], reverse=True)
    selected = [asset for asset, _ in scores[:g.max_positions]]

    # 等权重配置
    total_value = context.portfolio.total_value
    target_value_per_asset = total_value / len(selected)

    # 平仓不在选择列表中的资产
    for asset in context.portfolio.positions.keys():
        if asset not in selected:
            order_target_value(asset, 0)
            log.info("平仓 %s" % asset)

    # 建仓选中的资产
    for asset in selected:
        order_target_value(asset, target_value_per_asset)
        log.info("配置 %s 市值=%.2f" % (asset, target_value_per_asset))
```

---

## ⚖️ 与 Backtrader 的区别

| 特性         | 聚宽（JoinQuant）                       | Backtrader                                  |
| ------------ | --------------------------------------- | ------------------------------------------- |
| **入口函数** | `initialize()` + `handle_data()`        | `__init__()` + `next()`                     |
| **股票代码** | `g.security = "000001.XSHE"`            | 通过 `cerebro.adddata()` 外部加载           |
| **全局变量** | `g.*` （如 `g.security`, `g.params`）   | `self.*` （策略类属性）                     |
| **数据获取** | `attribute_history()`, `get_price()`    | `self.data.close[0]`, `self.data.close[-1]` |
| **下单**     | `order_value()`, `order_target()`       | `self.buy()`, `self.sell()`                 |
| **持仓**     | `context.portfolio.positions[security]` | `self.position.size`                        |
| **现金**     | `context.portfolio.available_cash`      | `self.broker.getcash()`                     |
| **日志**     | `log.info()`, `log.warn()`              | `print()` 或外部 logger                     |
| **定时任务** | `run_daily()`, `run_monthly()`          | 在 `next()` 中判断日期                      |
| **数据结构** | pandas DataFrame                        | 内置 Line 对象                              |

**核心差异总结**:

1. **聚宽**是函数式编程风格，**Backtrader**是面向对象风格
2. **聚宽**策略代码更简洁，**Backtrader**更灵活
3. **聚宽**使用 `g.*` 全局变量，**Backtrader**使用 `self.*` 实例属性
4. **聚宽**股票代码在策略内定义，**Backtrader**通过外部数据源加载

---

## ❓ 常见问题

### Q1: 如何指定多只股票？

**A**: 当前版本仅支持单只股票。多股票需要使用数组：

```python
def initialize(context):
    g.securities = ['000001.XSHE', '000002.XSHE', '600000.XSHG']

def handle_data(context, data):
    for security in g.securities:
        # 处理每只股票
        pass
```

### Q2: 如何获取分钟线数据？

**A**: 设置 `unit='1m'`：

```python
# 获取最近240分钟的分钟线数据（1个交易日）
bars = attribute_history(security, 240, '1m', ['close'])
```

### Q3: 如何避免未来数据（Look-ahead Bias）？

**A**:

- 使用 `set_option('use_real_price', True)` 开启真实价格模式
- `attribute_history()` 默认不包含当前 Bar
- 当前价格通过 `data[security].close` 获取

### Q4: 如何处理停牌股票？

**A**: 使用 `skip_paused=True` 跳过停牌日：

```python
bars = attribute_history(security, 60, '1d', ['close'], skip_paused=True)
```

### Q5: 策略代码中可以使用哪些第三方库？

**A**: 支持的库：

- ✅ `numpy`, `pandas` - 数据处理
- ✅ `talib` - 技术指标（如果安装）
- ✅ Python 标准库（`datetime`, `math`, `collections` 等）
- ❌ 不支持网络请求库（`requests`, `urllib`）
- ❌ 不支持文件操作（安全限制）

### Q6: 如何调试策略？

**A**: 使用 `log.info()` 输出日志到 Airflow 任务日志：

```python
log.info("当前价格: %.2f, MA5: %.2f" % (current_price, ma5))
log.info("持仓数量: %d" % position.closeable_amount)
```

### Q7: 佣金和印花税如何设置？

**A**: 系统自动配置，无需在策略中设置：

- 佣金率: 0.0003 (万三)
- 印花税: 0.001 (千一，仅卖出)
- 最低佣金: 5 元

### Q8: 如何在策略中使用自定义参数？

**A**: 通过 `g.params` 字典：

```python
def initialize(context):
    g.params = {
        'ma_period': 20,
        'threshold': 0.05,
        'stop_loss': 0.1
    }

def handle_data(context, data):
    period = g.params['ma_period']
    threshold = g.params['threshold']
    # 使用参数...
```

---

## 📁 参考策略文件

本项目 `strategies/` 目录下包含完整策略示例：

| 文件名                         | 策略类型     | 难度          | 说明                      |
| ------------------------------ | ------------ | ------------- | ------------------------- |
| `MA5.py`                       | 均线策略     | ⭐ 入门       | 最简单的 5 日均线突破策略 |
| `bollinger_breakout.py`        | 布林带突破   | ⭐⭐ 初级     | 布林带上下轨突破策略      |
| `aroon_indicator.py`           | Aroon 指标   | ⭐⭐ 初级     | Aroon 上下线交叉策略      |
| `announcement_reaction.py`     | 公告反应     | ⭐⭐⭐ 中级   | 开盘跳空缺口策略          |
| `adx_trend_strength_minute.py` | ADX 趋势强度 | ⭐⭐⭐ 中级   | 基于 ADX 指标判断趋势强度 |
| `daily_factor_rotation.py`     | 因子轮动     | ⭐⭐⭐⭐ 高级 | 多资产动态配置策略        |

---

## 📞 技术支持

如有疑问，请查看：

- 聚宽官方文档: https://www.joinquant.com/help/api/
- Airflow DAG 配置: `conversation_notes.md` 问题 9
- 项目 GitHub: https://github.com/DAIJINGFU/Airflow

---

**文档版本**: v1.0  
**最后更新**: 2025-11-25  
**维护者**: Claude Sonnet 4.5
