"""
通用策略回测平台 DAG

支持用户通过 Web UI 提交 JoinQuant 格式的策略代码进行回测
"""

from __future__ import annotations

import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import backtrader as bt
from airflow.decorators import dag, task
from airflow.models import Param
from airflow.exceptions import AirflowFailException

# 导入 JoinQuant 适配器和策略加载器
import sys
sys.path.insert(0, str(Path(__file__).parent))

from jq_adapter import JQStrategyAdapter, reset_global_context
from jq_strategy_loader import validate_strategy_code, load_strategy_functions

# ============================================================================
# 常量定义
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STRATEGIES_BASE_DIR = Path('/opt/airflow/strategies')
if not STRATEGIES_BASE_DIR.exists():
    fallback_dir = PROJECT_ROOT / 'strategies'
    if fallback_dir.exists():
        STRATEGIES_BASE_DIR = fallback_dir


# =============================================================================
# 复用现有组件
# =============================================================================

class CNStockCommission(bt.CommInfoBase):
    """A股佣金模式实现"""
    params = (
        ('stocklike', True),
        ('commtype', bt.CommInfoBase.COMM_PERC),
        ('perc', 0.0003),        # 万三
        ('stamp_duty', 0.001),   # 印花税千一
        ('min_comm', 5.0),       # 最低佣金5元
    )

    def _getcommission(self, size, price, pseudoexec):
        if pseudoexec:
            return 0.0
        
        value = abs(size) * price
        commission = value * self.p.perc
        
        # 卖出加印花税
        if size < 0:
            commission += value * self.p.stamp_duty
        
        # 最低佣金
        commission = max(commission, self.p.min_comm)
        
        return commission


class LotSizeSizer(bt.Sizer):
    """A股手（100股）规则"""
    params = (('stake', 100),)
    
    def _getsizing(self, comminfo, cash, data, isbuy):
        if isbuy:
            price = data.close[0]
            if price <= 0:
                return 0
            size = int(cash / price / 100) * 100
            return max(size, 0)
        else:
            position = self.broker.getposition(data)
            size = int(position.size / 100) * 100
            return max(size, 0)


# =============================================================================
# 辅助函数
# =============================================================================

def _load_local_stock_data(path: Path, security: str, start_date: str, end_date: str, freq: str):
    """
    从本地目录加载股票数据
    
    优化点：
    - 增强错误信息提示
    - 添加数据质量验证
    - 支持数据缓存（如果文件已存在且有效）
    """
    # 检查是否已有有效缓存
    if path.exists():
        try:
            cached_df = pd.read_csv(path, encoding='utf-8')
            if len(cached_df) > 0:
                print(f"[INFO] 使用缓存数据: {path}, {len(cached_df)} 条记录")
                return
        except Exception as e:
            print(f"[WARN] 缓存数据无效: {e}，重新加载")
    
    # 解析股票代码: 000001.XSHE -> 000001
    stock_code = security.split('.')[0]
    
    # 本地数据路径
    local_data_dir = Path('/opt/airflow/stockdata/1d_1w_1m') / stock_code
    source_file = local_data_dir / f"{stock_code}_daily.csv"
    
    print(f"[INFO] 尝试加载本地数据: {source_file}")
    
    if not source_file.exists():
        raise FileNotFoundError(
            f"本地数据文件不存在: {source_file}\n"
            f"请确认：\n"
            f"1. 股票代码 '{security}' 是否正确\n"
            f"2. 数据目录 {local_data_dir} 是否存在\n"
            f"3. 文件名是否为 '{stock_code}_daily.csv'"
        )
    
    # 读取 CSV
    try:
        df = pd.read_csv(source_file, encoding='utf-8')
    except Exception as e:
        raise ValueError(f"读取数据文件失败: {source_file}, 错误: {e}")
    
    # 列名映射 (中文 -> 英文)
    column_mapping = {
        '日期': 'datetime',
        '开盘': 'open',
        '收盘': 'close',
        '最高': 'high',
        '最低': 'low',
        '成交量': 'volume',
    }
    df = df.rename(columns=column_mapping)
    
    # 验证必需列
    required_columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(
            f"数据文件缺少必需列: {missing_columns}\n"
            f"当前列: {list(df.columns)}"
        )
    
    # 确保日期列为 datetime
    if 'datetime' in df.columns:
        try:
            df['datetime'] = pd.to_datetime(df['datetime'])
        except Exception as e:
            raise ValueError(f"日期列格式错误: {e}")
    
    # 过滤日期范围
    start_ts = pd.to_datetime(start_date)
    end_ts = pd.to_datetime(end_date)
    df = df[(df['datetime'] >= start_ts) & (df['datetime'] <= end_ts)]
    
    if len(df) == 0:
        raise ValueError(
            f"指定日期范围内没有数据: {start_date} ~ {end_date}\n"
            f"请检查日期范围是否合理"
        )
    
    # 只保留需要的列
    df = df[required_columns]
    df = _resample_ohlcv(df, freq)
    df['datetime'] = df['datetime'].dt.strftime('%Y-%m-%d')
    
    # 保存到临时文件
    df.to_csv(path, index=False)
    print(f"[SUCCESS] 本地数据加载完成: {path}")
    print(f"  - 数据条数: {len(df)} 条")
    print(f"  - 日期范围: {df['datetime'].min()} ~ {df['datetime'].max()}")
    print(f"  - 回测频率: {freq}")


def _generate_mock_csv(path: Path, security: str, start_date: str, end_date: str, freq: str):
    """生成模拟数据（临时方案 - 已废弃，请使用本地数据）"""
    import random
    
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    base_price = 10.0
    
    data = []
    for date in date_range:
        if date.weekday() < 5:  # 只保留工作日
            change = random.uniform(-0.05, 0.05)
            base_price = base_price * (1 + change)
            data.append({
                'datetime': date.strftime('%Y-%m-%d'),
                'open': base_price * random.uniform(0.98, 1.02),
                'high': base_price * random.uniform(1.00, 1.05),
                'low': base_price * random.uniform(0.95, 1.00),
                'close': base_price,
                'volume': random.randint(100000, 1000000),
            })
    
    df = pd.DataFrame(data)
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = _resample_ohlcv(df, freq)
    df['datetime'] = df['datetime'].dt.strftime('%Y-%m-%d')
    df.to_csv(path, index=False)
    print(f"[WARN] 使用模拟数据（非真实数据）: {path}, {len(df)} 条记录")


def _generate_strategy_name(code: str) -> str:
    """根据代码内容生成策略名称"""
    code_hash = hashlib.md5(code.encode()).hexdigest()[:8]
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"strategy_{timestamp}_{code_hash}"


def _resample_ohlcv(df: pd.DataFrame, freq: str) -> pd.DataFrame:
    """根据频率（日/周/月）重采样数据"""
    if df.empty or freq == 'day':
        return df
    
    freq_mapping = {
        'week': 'W-FRI',
        'month': 'M',
    }
    rule = freq_mapping.get(freq)
    if not rule:
        return df
    
    resampled = (
        df.set_index('datetime')
          .resample(rule)
          .agg({
              'open': 'first',
              'high': 'max',
              'low': 'min',
              'close': 'last',
              'volume': 'sum',
          })
          .dropna(subset=['open', 'high', 'low', 'close'])
          .reset_index()
    )
    return resampled


def _normalize_strategy_code(code: str) -> str:
    """
    规范化用户粘贴的策略代码

    主要针对以下几类情况：
    - 浏览器/系统只保留了 \\r（回车）而丢失 \\n（换行），导致整段代码被视为单行注释
    - 文本区域把 \\n 当作字面量字符串 `\\n`
    - 代码前带有 UTF-8 BOM
    """
    if not code:
        return code

    cleaned = code.lstrip('\ufeff')
    cleaned = cleaned.replace('\r\n', '\n').replace('\r', '\n')

    # 如果只有字面量 "\n" 而没有真实换行，尝试替换
    if '\n' not in cleaned and '\\n' in cleaned:
        cleaned = cleaned.replace('\\r\\n', '\n').replace('\\n', '\n').replace('\\r', '\n')

    return cleaned


def _load_strategy_code_from_file(strategy_file: str) -> str:
    """根据文件名读取策略代码"""
    file_path = Path(strategy_file.strip())
    candidate_paths = []

    if file_path.is_absolute():
        candidate_paths.append(file_path)
    else:
        candidate_paths.append(STRATEGIES_BASE_DIR / file_path)
        candidate_paths.append(PROJECT_ROOT / file_path)

    for candidate in candidate_paths:
        if candidate.exists():
            if candidate.is_dir():
                raise IsADirectoryError(f"策略文件路径指向目录: {candidate}")
            return candidate.read_text(encoding='utf-8')

    tried_paths = ", ".join(str(p) for p in candidate_paths)
    raise FileNotFoundError(f"策略文件不存在（已尝试: {tried_paths}）")


# =============================================================================
# Airflow 任务
# =============================================================================

@task
def validate_and_prepare(**context) -> Dict[str, Any]:
    """
    步骤1: 验证策略代码并准备参数
    """
    print("[TASK] validate_and_prepare 开始")
    
    # 调试：打印 context 的键
    print(f"[DEBUG] context keys: {list(context.keys())}")
    
    # 从 context 中提取 DAG params
    dag_params = context.get('params', {})
    print(f"[DEBUG] dag_params keys: {list(dag_params.keys())}")
    
    # 提取参数
    strategy_file = (dag_params.get('strategy_file') or '').strip()
    raw_strategy_code = dag_params.get('strategy_code', '')

    if strategy_file:
        print(f"[INFO] 从策略文件加载代码: {strategy_file}")
        try:
            raw_strategy_code = _load_strategy_code_from_file(strategy_file)
        except (FileNotFoundError, IsADirectoryError) as file_error:
            raise AirflowFailException(f"策略文件读取失败: {file_error}")
        except Exception as file_error:
            raise AirflowFailException(f"策略文件解析异常: {file_error}")

    strategy_code = _normalize_strategy_code(raw_strategy_code)
    strategy_name = (dag_params.get('strategy_name') or '').strip()
    start_date = dag_params.get('start_date', '')
    end_date = dag_params.get('end_date', '')
    freq = str(dag_params.get('freq', 'day')).lower()
    benchmark = (dag_params.get('benchmark') or '').strip()

    if raw_strategy_code and raw_strategy_code != strategy_code:
        print("[INFO] 已自动修复策略代码的换行符（检测到粘贴文本只有回车没有换行）")
    
    validation_errors = []
    if not strategy_code or not strategy_code.strip():
        validation_errors.append("策略代码不能为空")
    
    try:
        initial_cash = float(dag_params.get('initial_cash', 100000))
    except (TypeError, ValueError):
        validation_errors.append("初始资金必须为数字")
        initial_cash = 0.0
    
    if initial_cash <= 0:
        validation_errors.append("初始资金必须大于 0")
    
    if not start_date:
        validation_errors.append("start_date 不能为空")
    if not end_date:
        validation_errors.append("end_date 不能为空")
    
    start_dt = None
    end_dt = None
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        except ValueError:
            validation_errors.append(f"start_date 格式错误: {start_date}，应为 YYYY-MM-DD")
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            validation_errors.append(f"end_date 格式错误: {end_date}，应为 YYYY-MM-DD")
    
    allowed_freq = {'day', 'week', 'month'}
    if freq not in allowed_freq:
        validation_errors.append("freq 参数仅支持 day/week/month")
    
    if start_dt and end_dt and start_dt > end_dt:
        validation_errors.append("start_date 不能晚于 end_date")
    
    if validation_errors:
        error_msg = "参数验证失败:\n" + "\n".join(f"- {msg}" for msg in validation_errors)
        print(f"[ERROR] {error_msg}")
        raise AirflowFailException(error_msg)
    
    # 标准化日期字符串，保证后续流程一致
    start_date = start_dt.strftime('%Y-%m-%d') if start_dt else start_date
    end_date = end_dt.strftime('%Y-%m-%d') if end_dt else end_date
    
    # 调试：打印策略代码前100个字符
    print(f"[DEBUG] strategy_code (前100字符): {strategy_code[:100] if strategy_code else 'EMPTY'}")
    
    # 验证策略代码
    print("[INFO] 验证策略代码...")
    result = validate_strategy_code(strategy_code, strategy_name)
    
    if not result.is_valid:
        error_msg = "策略代码验证失败:\n" + "\n".join(result.errors)
        print(f"[ERROR] {error_msg}")
        raise AirflowFailException(error_msg)
    
    print(f"[SUCCESS] 策略验证通过")
    print(f"  - 股票代码: {result.security}")
    print(f"  - 策略名称: {result.strategy_name}")
    
    if result.warnings:
        print(f"[WARNING] 警告信息:")
        for warning in result.warnings:
            print(f"  - {warning}")
    
    # 生成策略名称（如果未提供）
    final_strategy_name = strategy_name if strategy_name else result.strategy_name
    
    # 准备数据文件路径
    data_dir = Path('/tmp/backtest_data')
    data_dir.mkdir(parents=True, exist_ok=True)
    
    csv_filename = f"{result.security.replace('.', '_')}_{start_date}_{end_date}.csv"
    csv_path = data_dir / csv_filename
    
    # 返回参数
    return {
        'strategy_code': strategy_code,
        'strategy_name': final_strategy_name,
        'security': result.security,
        'start_date': start_date,
        'end_date': end_date,
        'initial_cash': initial_cash,
        'freq': freq,
        'benchmark': benchmark,
        'csv_path': str(csv_path),
    }


@task
def prepare_data(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    步骤2: 准备回测数据
    
    优化点：
    - 增强错误处理和用户提示
    - 支持数据缓存
    - 更详细的进度信息
    """
    print("[TASK] prepare_data 开始")
    print("="*60)
    
    security = config['security']
    start_date = config['start_date']
    end_date = config['end_date']
    freq = config['freq']
    csv_path = Path(config['csv_path'])
    
    print(f"[数据准备] 股票代码: {security}")
    print(f"[数据准备] 日期范围: {start_date} ~ {end_date}")
    print(f"[数据准备] 回测频率: {freq}")
    print(f"[数据准备] 保存路径: {csv_path}")
    print("-"*60)
    
    try:
        # 优先使用本地真实数据
        print("[1/2] 尝试从本地加载数据...")
        _load_local_stock_data(csv_path, security, start_date, end_date, freq)
        print("[2/2] 数据加载成功")
        
    except FileNotFoundError as e:
        print(f"[WARNING] 本地数据不存在: {e}")
        print("[1/2] 切换到模拟数据模式...")
        try:
            _generate_mock_csv(csv_path, security, start_date, end_date, freq)
            print("[2/2] 模拟数据生成成功")
            print("[WARNING] 正在使用模拟数据，回测结果仅供参考！")
        except Exception as mock_error:
            raise AirflowFailException(
                f"数据准备完全失败\n"
                f"- 本地数据加载失败: {e}\n"
                f"- 模拟数据生成失败: {mock_error}"
            )
    
    except Exception as e:
        print(f"[ERROR] 数据加载失败: {e}")
        raise AirflowFailException(f"数据准备失败: {e}")
    
    print("="*60)
    print(f"[SUCCESS] 数据准备完成")
    print()
    
    return config


@task
def run_backtest(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    步骤3: 执行回测
    
    优化点：
    - 增强异常处理
    - 更详细的进度提示
    - 改进回测结果输出
    """
    print("[TASK] run_backtest 开始")
    print("="*60)
    
    strategy_code = config['strategy_code']
    strategy_name = config['strategy_name']
    security = config['security']
    csv_path = Path(config['csv_path'])
    initial_cash = config['initial_cash']
    freq = config['freq']
    benchmark = config['benchmark']
    
    # 加载策略函数
    print("[1/5] 加载策略代码...")
    try:
        reset_global_context()
        initialize_func, handle_data_func, namespace = load_strategy_functions(strategy_code)
        
        if not initialize_func or not handle_data_func:
            raise AirflowFailException("策略加载失败：未找到 initialize 或 handle_data 函数")
        
        print("      ✓ 策略函数加载成功")
    except Exception as e:
        raise AirflowFailException(f"策略加载失败: {e}")
    
    # 创建 Cerebro 引擎
    print("[2/5] 配置 Backtrader 引擎...")
    try:
        cerebro = bt.Cerebro()
        
        # 添加策略（使用适配器）
        cerebro.addstrategy(
            JQStrategyAdapter,
            jq_initialize=initialize_func,
            jq_handle_data=handle_data_func,
            data_frequency=freq,
            benchmark=benchmark or None,
        )
        
        # 加载数据
        if not csv_path.exists():
            raise AirflowFailException(f"数据文件不存在: {csv_path}")
        
        data = bt.feeds.GenericCSVData(
            dataname=str(csv_path),
            dtformat='%Y-%m-%d',
            datetime=0,
            open=1,
            high=2,
            low=3,
            close=4,
            volume=5,
            openinterest=-1,
            name=security
        )
        cerebro.adddata(data)
        
        # 设置初始资金
        cerebro.broker.setcash(initial_cash)
        
        # 设置佣金
        comminfo = CNStockCommission()
        cerebro.broker.addcommissioninfo(comminfo)
        
        # 设置手规则
        cerebro.addsizer(LotSizeSizer)
        
        # 添加分析器
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', riskfreerate=0.03)
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        
        print("      ✓ 引擎配置完成")
    except Exception as e:
        raise AirflowFailException(f"Backtrader 配置失败: {e}")
    
    print("[3/5] 回测配置信息:")
    print(f"      - 策略名称: {strategy_name}")
    print(f"      - 股票代码: {security}")
    print(f"      - 初始资金: ￥{initial_cash:,.2f}")
    print(f"      - 回测频率: {freq}")
    print(f"      - 数据文件: {csv_path.name}")
    
    # 运行回测
    print("[4/5] 正在执行回测...")
    try:
        start_value = cerebro.broker.getvalue()
        results = cerebro.run()
        strat = results[0]
        end_value = cerebro.broker.getvalue()
        print("      ✓ 回测执行完成")
    except Exception as e:
        raise AirflowFailException(f"回测执行失败: {e}\n\n请检查策略代码是否正确")
    
    # 提取分析结果
    print("[5/5] 生成回测结果...")
    try:
        returns_analyzer = strat.analyzers.returns.get_analysis()
        sharpe_analyzer = strat.analyzers.sharpe.get_analysis()
        drawdown_analyzer = strat.analyzers.drawdown.get_analysis()
        trades_analyzer = strat.analyzers.trades.get_analysis()
        
        # 计算性能指标
        total_return = (end_value - start_value) / start_value
        annual_return = returns_analyzer.get('rnorm100', 0.0)
        sharpe_ratio = sharpe_analyzer.get('sharperatio', None)
        max_drawdown = drawdown_analyzer.get('max', {}).get('drawdown', 0.0)
        
        total_trades = trades_analyzer.get('total', {}).get('total', 0)
        won_trades = trades_analyzer.get('won', {}).get('total', 0)
        lost_trades = trades_analyzer.get('lost', {}).get('total', 0)
        win_rate = (won_trades / total_trades * 100) if total_trades > 0 else 0.0
        
        # 计算平均盈利和平均亏损
        avg_win = trades_analyzer.get('won', {}).get('pnl', {}).get('average', 0.0) if won_trades > 0 else 0.0
        avg_loss = trades_analyzer.get('lost', {}).get('pnl', {}).get('average', 0.0) if lost_trades > 0 else 0.0
        
        results_dict = {
            'strategy_name': strategy_name,
            'security': security,
            'start_date': config['start_date'],
            'end_date': config['end_date'],
            'start_value': start_value,
            'end_value': end_value,
            'total_return': total_return,
            'total_return_pct': total_return * 100,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe_ratio if sharpe_ratio else 0.0,
            'max_drawdown': max_drawdown,
            'max_drawdown_pct': max_drawdown,
            'total_trades': total_trades,
            'won_trades': won_trades,
            'lost_trades': lost_trades,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_loss_ratio': abs(avg_win / avg_loss) if avg_loss != 0 else 0.0,
            'freq': freq,
            'benchmark': benchmark,
        }
        
        print("      ✓ 结果计算完成")
    except Exception as e:
        raise AirflowFailException(f"结果分析失败: {e}")
    
    print("-"*60)
    print("[回测结果概要]")
    print(f"  初始资金: ￥{start_value:,.2f}")
    print(f"  最终资金: ￥{end_value:,.2f}")
    print(f"  总收益率: {total_return*100:.2f}%")
    print(f"  年化收益: {annual_return:.2f}%")
    print(f"  夏普比率: {sharpe_ratio if sharpe_ratio else 'N/A'}")
    print(f"  最大回撤: {max_drawdown:.2f}%")
    print(f"  交易次数: {total_trades}")
    print(f"  胜    率: {win_rate:.2f}%")
    print("="*60)
    
    return results_dict


@task
def generate_report(results: Dict[str, Any]):
    """
    步骤4: 生成回测报告
    """
    print("[TASK] generate_report 开始")
    
    # 保存 JSON 报告
    report_dir = Path('/tmp/backtest_reports')
    report_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    json_file = report_dir / f"report_{results['strategy_name']}_{timestamp}.json"
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"[SUCCESS] 报告已生成: {json_file}")
    
    # 打印总结
    print("\n" + "="*60)
    print("回测报告总结".center(60))
    print("="*60)
    print(f"策略名称: {results['strategy_name']}")
    print(f"股票代码: {results['security']}")
    print(f"回测频率: {results['freq']}")
    if results['benchmark']:
        print(f"基准指数: {results['benchmark']}")
    print(f"初始资金: ¥{results['start_value']:,.2f}")
    print(f"最终资金: ¥{results['end_value']:,.2f}")
    print(f"总收益率: {results['total_return_pct']:.2f}%")
    print(f"年化收益: {results['annual_return']:.2f}%")
    print(f"夏普比率: {results['sharpe_ratio']:.4f}")
    print(f"最大回撤: {results['max_drawdown_pct']:.2f}%")
    print(f"交易次数: {results['total_trades']}")
    print(f"胜率: {results['win_rate']:.2f}%")
    print("="*60)


# =============================================================================
# DAG 定义
# =============================================================================

@dag(
    dag_id='universal_backtest_platform',
    description='通用策略回测平台 - 支持 JoinQuant 格式策略',
    schedule=None,  # 手动触发
    start_date=datetime(2025, 11, 25),
    catchup=False,
    tags=['backtest', 'joinquant', 'universal'],
    params={
        "strategy_name": Param(
            default="",
            type="string",
            title="策略名称",
            description="策略名称（留空自动生成）",
        ),
        "strategy_file": Param(
            default="",
            type="string",
            title="策略文件（可选）",
            description="可选: 相对于 /opt/airflow/strategies 的文件路径，如 MA5.py 或 strategies/MA5.py",
        ),
        "strategy_code": Param(
            default="""from jqdata import *

def initialize(context):
    # 设置股票代码
    g.security = '000001.XSHE'
    set_benchmark('000300.XSHG')
    set_option('use_real_price', True)

def handle_data(context, data):
    security = g.security
    
    # 获取最近5日收盘价
    prices = attribute_history(security, 5, '1d', ['close'])
    ma5 = prices['close'].mean()
    
    # 当前价格
    current_price = data[security].close
    
    # 简单均线策略
    if current_price > ma5:
        # 买入
        order_value(security, context.portfolio.available_cash * 0.9)
    elif current_price < ma5 * 0.98:
        # 卖出
        order_target(security, 0)
""",
            type="string",
            title="策略代码",
            description="JoinQuant 格式策略代码（必须包含 initialize 和 handle_data 函数，并在代码中指定 g.security）",
        ),
        "start_date": Param(
            default="2020-01-01",
            type="string",
            pattern=r"^\d{4}-\d{2}-\d{2}$",
            title="开始日期",
            description="回测开始日期（格式：YYYY-MM-DD）",
        ),
        "end_date": Param(
            default="2024-12-31",
            type="string",
            pattern=r"^\d{4}-\d{2}-\d{2}$",
            title="结束日期",
            description="回测结束日期（格式：YYYY-MM-DD）",
        ),
        "initial_cash": Param(
            default=100000.0,
            type="number",
            title="初始资金",
            description="初始资金（元）",
        ),
        "freq": Param(
            default="day",
            type="string",
            enum=["day", "week", "month"],
            title="回测频率",
            description="回测频率（day=日线, week=周线, month=月线）",
        ),
        "benchmark": Param(
            default="000300.XSHG",
            type="string",
            title="基准指数",
            description="基准指数代码（可选，如沪深300: 000300.XSHG）",
        ),
    },
)
def universal_backtest_platform_dag():
    """
    通用策略回测平台 DAG
    
    任务流程:
    1. validate_and_prepare: 验证策略代码并准备参数
    2. prepare_data: 获取或生成回测数据
    3. run_backtest: 执行回测
    4. generate_report: 生成回测报告
    """
    
    # 定义任务流程（直接调用，params 通过 context 自动传递）
    validated_config = validate_and_prepare()
    data_ready = prepare_data(validated_config)
    results = run_backtest(data_ready)
    generate_report(results)


# 实例化 DAG
universal_backtest_platform_dag()
