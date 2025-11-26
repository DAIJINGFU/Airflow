#!/usr/bin/env python3
"""
触发并监控通用回测平台 DAG

使用 Airflow REST API 触发 DAG 并实时监控执行状态
"""

import requests
import time
import json
from datetime import datetime

# Airflow API 配置
AIRFLOW_URL = "http://localhost:8080"
USERNAME = "admin"
PASSWORD = "ZdPgCVpvRpH4y6eh"  # 从容器日志中获取的最新密码

# DAG 配置
DAG_ID = "universal_backtest_platform"

# 默认策略代码（MA5 示例）
DEFAULT_STRATEGY_CODE = """from jqdata import *

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
"""


def trigger_dag(strategy_code=None, strategy_name=None, start_date="2020-01-01", 
                end_date="2024-12-31", initial_cash=100000.0, freq="day", benchmark="000300.XSHG"):
    """触发 DAG"""
    
    if strategy_code is None:
        strategy_code = DEFAULT_STRATEGY_CODE
    
    if strategy_name is None:
        strategy_name = f"MA5_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    url = f"{AIRFLOW_URL}/api/v2/dags/{DAG_ID}/dagRuns"
    
    payload = {
        "conf": {
            "strategy_code": strategy_code,
            "strategy_name": strategy_name,
            "start_date": start_date,
            "end_date": end_date,
            "initial_cash": initial_cash,
            "freq": freq,
            "benchmark": benchmark
        }
    }
    
    print(f"[触发 DAG] {DAG_ID}")
    print(f"  策略名称: {strategy_name}")
    print(f"  回测时间: {start_date} ~ {end_date}")
    print(f"  初始资金: ¥{initial_cash:,.2f}")
    print(f"  回测频率: {freq}")
    print(f"  基准指数: {benchmark}")
    print("-" * 60)
    
    try:
        response = requests.post(
            url,
            json=payload,
            auth=(USERNAME, PASSWORD),
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            dag_run_id = result.get('dag_run_id')
            print(f"✓ DAG 触发成功")
            print(f"  DAG Run ID: {dag_run_id}")
            return dag_run_id
        else:
            print(f"✗ DAG 触发失败")
            print(f"  状态码: {response.status_code}")
            print(f"  响应: {response.text}")
            return None
            
    except Exception as e:
        print(f"✗ 触发失败: {e}")
        return None


def get_dag_run_state(dag_run_id):
    """获取 DAG 运行状态"""
    url = f"{AIRFLOW_URL}/api/v2/dags/{DAG_ID}/dagRuns/{dag_run_id}"
    
    try:
        response = requests.get(
            url,
            auth=(USERNAME, PASSWORD),
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
            
    except Exception as e:
        print(f"获取状态失败: {e}")
        return None


def get_task_instances(dag_run_id):
    """获取任务实例状态"""
    url = f"{AIRFLOW_URL}/api/v2/dags/{DAG_ID}/dagRuns/{dag_run_id}/taskInstances"
    
    try:
        response = requests.get(
            url,
            auth=(USERNAME, PASSWORD),
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json().get('task_instances', [])
        else:
            return []
            
    except Exception as e:
        print(f"获取任务状态失败: {e}")
        return []


def get_task_log(dag_run_id, task_id, try_number=1):
    """获取任务日志"""
    url = f"{AIRFLOW_URL}/api/v2/dags/{DAG_ID}/dagRuns/{dag_run_id}/taskInstances/{task_id}/logs/{try_number}"
    
    try:
        response = requests.get(
            url,
            auth=(USERNAME, PASSWORD),
            timeout=10
        )
        
        if response.status_code == 200:
            return response.text
        else:
            return None
            
    except Exception as e:
        return None


def monitor_dag_run(dag_run_id, max_wait=600, interval=5):
    """监控 DAG 运行"""
    
    print(f"\n[监控 DAG 运行] {dag_run_id}")
    print("=" * 60)
    
    start_time = time.time()
    last_state = {}
    
    while True:
        elapsed = time.time() - start_time
        
        if elapsed > max_wait:
            print(f"\n✗ 超时: 执行时间超过 {max_wait} 秒")
            break
        
        # 获取 DAG 状态
        dag_info = get_dag_run_state(dag_run_id)
        if not dag_info:
            print(".", end="", flush=True)
            time.sleep(interval)
            continue
        
        dag_state = dag_info.get('state')
        
        # 获取任务状态
        tasks = get_task_instances(dag_run_id)
        
        # 检查是否有状态变化
        current_state = {task['task_id']: task['state'] for task in tasks}
        
        if current_state != last_state:
            print(f"\n[{int(elapsed)}s] DAG 状态: {dag_state}")
            for task in tasks:
                task_id = task['task_id']
                task_state = task['state']
                start = task.get('start_date', 'N/A')
                end = task.get('end_date', 'N/A')
                
                state_icon = {
                    'success': '✓',
                    'failed': '✗',
                    'running': '▶',
                    'queued': '○',
                    'scheduled': '◷',
                    'up_for_retry': '↻',
                }.get(task_state, '?')
                
                print(f"  {state_icon} {task_id}: {task_state}")
            
            last_state = current_state
        
        # 检查终止状态
        if dag_state in ['success', 'failed']:
            print(f"\n{'=' * 60}")
            print(f"[完成] DAG 最终状态: {dag_state}")
            print(f"总耗时: {int(elapsed)} 秒")
            
            # 显示失败任务的日志
            if dag_state == 'failed':
                print("\n[失败任务日志]")
                for task in tasks:
                    if task['state'] == 'failed':
                        task_id = task['task_id']
                        try_number = task.get('try_number', 1)
                        print(f"\n--- {task_id} (Try #{try_number}) ---")
                        log = get_task_log(dag_run_id, task_id, try_number)
                        if log:
                            # 只显示最后 50 行
                            lines = log.split('\n')
                            print('\n'.join(lines[-50:]))
            
            # 显示成功任务的关键日志（generate_report）
            if dag_state == 'success':
                print("\n[回测结果]")
                for task in tasks:
                    if task['task_id'] == 'generate_report' and task['state'] == 'success':
                        try_number = task.get('try_number', 1)
                        log = get_task_log(dag_run_id, task['task_id'], try_number)
                        if log:
                            # 提取回测结果部分
                            lines = log.split('\n')
                            in_result = False
                            for line in lines:
                                if '回测报告总结' in line or '=' * 20 in line:
                                    in_result = True
                                if in_result:
                                    print(line)
                                if in_result and line.strip() == '=' * 60:
                                    break
            
            break
        
        time.sleep(interval)
    
    return dag_state


def main():
    """主函数"""
    print("=" * 60)
    print("通用回测平台 DAG 触发器与监控器")
    print("=" * 60)
    
    # 触发 DAG
    dag_run_id = trigger_dag()
    
    if not dag_run_id:
        print("DAG 触发失败，退出")
        return
    
    # 监控执行
    final_state = monitor_dag_run(dag_run_id, max_wait=600, interval=5)
    
    print("\n" + "=" * 60)
    if final_state == 'success':
        print("✓ 回测任务执行成功")
    else:
        print("✗ 回测任务执行失败")
    print("=" * 60)


if __name__ == '__main__':
    main()
