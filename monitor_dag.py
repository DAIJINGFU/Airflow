#!/usr/bin/env python3
"""
监控 DAG 运行状态（使用 CLI）
"""

import subprocess
import time
import re
from datetime import datetime

DAG_ID = "universal_backtest_platform"
RUN_ID = "manual__2025-11-26T04:27:00.716452+00:00"

def run_command(cmd):
    """运行命令并返回输出"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout + result.stderr
    except Exception as e:
        return f"Error: {e}"

def get_task_states():
    """获取任务状态"""
    cmd = f'docker exec airflow_new-airflow-standalone-1 bash -c "airflow tasks states-for-dag-run {DAG_ID} {RUN_ID} 2>/dev/null"'
    output = run_command(cmd)
    
    tasks = {}
    for line in output.split('\n'):
        line = line.strip()
        if '|' in line and 'task_id' not in line and '===' not in line:
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 3:
                task_id = parts[0]
                state = parts[1]
                tasks[task_id] = state
    
    return tasks

def get_task_log(task_id):
    """获取任务日志"""
    cmd = f'docker exec airflow_new-airflow-standalone-1 bash -c "airflow tasks log {DAG_ID} {task_id} {RUN_ID} 2>/dev/null | tail -100"'
    return run_command(cmd)

def monitor():
    """监控 DAG 运行"""
    print("=" * 70)
    print(f"监控 DAG 运行: {DAG_ID}")
    print(f"Run ID: {RUN_ID}")
    print("=" * 70)
    
    last_states = {}
    start_time = time.time()
    
    while True:
        elapsed = int(time.time() - start_time)
        
        if elapsed > 600:  # 10分钟超时
            print(f"\n✗ 超时: 执行时间超过 10 分钟")
            break
        
        tasks = get_task_states()
        
        if not tasks:
            print(".", end="", flush=True)
            time.sleep(3)
            continue
        
        # 检查状态变化
        if tasks != last_states:
            print(f"\n\n[{elapsed}s] 任务状态更新:")
            print("-" * 70)
            
            state_icons = {
                'success': '✓',
                'failed': '✗',
                'running': '▶',
                'queued': '○',
                'scheduled': '◷',
                'up_for_retry': '↻',
                'none': '-',
            }
            
            task_order = ['validate_and_prepare', 'prepare_data', 'run_backtest', 'generate_report']
            
            for task_id in task_order:
                if task_id in tasks:
                    state = tasks[task_id].lower()
                    icon = state_icons.get(state, '?')
                    print(f"  {icon} {task_id:<25} {state}")
            
            last_states = tasks
        
        # 检查是否完成
        all_states = list(tasks.values())
        
        if all(s.lower() == 'success' for s in all_states):
            print(f"\n{'=' * 70}")
            print(f"✓ DAG 执行成功！总耗时: {elapsed} 秒")
            print("=" * 70)
            
            # 获取 generate_report 日志
            print("\n[回测结果]")
            print("=" * 70)
            log = get_task_log('generate_report')
            
            # 提取回测报告
            in_report = False
            for line in log.split('\n'):
                if '回测报告总结' in line or ('=' * 40) in line:
                    in_report = True
                if in_report:
                    print(line)
                if in_report and line.strip().endswith('=' * 60):
                    break
            
            break
        
        if any(s.lower() == 'failed' for s in all_states):
            print(f"\n{'=' * 70}")
            print(f"✗ DAG 执行失败！")
            print("=" * 70)
            
            # 找出失败的任务
            for task_id, state in tasks.items():
                if state.lower() == 'failed':
                    print(f"\n[失败任务日志] {task_id}")
                    print("-" * 70)
                    log = get_task_log(task_id)
                    lines = log.split('\n')
                    # 显示最后 50 行
                    for line in lines[-50:]:
                        print(line)
            
            break
        
        time.sleep(5)

if __name__ == '__main__':
    monitor()
