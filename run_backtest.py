#!/usr/bin/env python3
"""
完整的回测 DAG 触发和监控脚本
使用 subprocess 直接调用 docker 命令
"""

import subprocess
import time
import json
import re
from datetime import datetime

DAG_ID = "universal_backtest_platform"

def run_docker_command(cmd, timeout=30):
    """运行 Docker 命令"""
    try:
        result = subprocess.run(
            f"docker exec airflow_new-airflow-standalone-1 bash -c \"{cmd}\"",
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.stdout, result.stderr
    except Exception as e:
        return "", str(e)

def trigger_dag():
    """触发 DAG"""
    print("=" * 70)
    print("触发回测 DAG")
    print("=" * 70)
    
    cmd = f"airflow dags trigger {DAG_ID}"
    stdout, stderr = run_docker_command(cmd, timeout=60)
    
    output = stdout + stderr
    
    # 提取 Run ID
    match = re.search(r'(manual__[\d\-T:+\.]+)', output)
    if match:
        run_id = match.group(1)
        print(f"✓ DAG 触发成功")
        print(f"  Run ID: {run_id}")
        return run_id
    else:
        print("✗ 无法提取 Run ID")
        print(f"输出: {output[:500]}")
        return None

def wait_for_completion(run_id, max_wait=600):
    """等待 DAG 完成"""
    print(f"\n监控 DAG 执行: {run_id}")
    print("=" * 70)
    
    start_time = time.time()
    check_count = 0
    
    while True:
        elapsed = int(time.time() - start_time)
        
        if elapsed > max_wait:
            print(f"\n✗ 超时: 执行时间超过 {max_wait} 秒")
            return False
        
        # 等待一会儿再检查
        time.sleep(10)
        check_count += 1
        
        # 检查日志文件
        print(f"\n[检查 #{check_count}] 已等待 {elapsed} 秒...")
        
        # 查找日志目录
        cmd = f"find /opt/airflow/logs/dag_id={DAG_ID} -type d -name 'run_id={run_id}*' 2>/dev/null | head -1"
        stdout, _ = run_docker_command(cmd)
        
        log_dir = stdout.strip()
        if not log_dir:
            print("  日志目录尚未创建，继续等待...")
            continue
        
        print(f"  找到日志目录: {log_dir}")
        
        # 检查所有任务的日志
        cmd = f"ls {log_dir}/ 2>/dev/null"
        stdout, _ = run_docker_command(cmd)
        
        tasks = [t.strip() for t in stdout.split('\n') if t.strip()]
        print(f"  已创建的任务: {', '.join(tasks)}")
        
        # 检查 generate_report 任务（最后一个任务）
        if 'generate_report' in tasks:
            print("\n  检测到 generate_report 任务，检查执行状态...")
            
            cmd = f"find {log_dir}/generate_report -name '*.log' 2>/dev/null | head -1"
            stdout, _ = run_docker_command(cmd)
            
            log_file = stdout.strip()
            if log_file:
                # 读取日志检查是否完成
                cmd = f"tail -100 {log_file}"
                stdout, _ = run_docker_command(cmd, timeout=10)
                
                if '回测报告总结' in stdout:
                    print("\n✓ DAG 执行成功！")
                    return True, stdout
                elif 'ERROR' in stdout or 'FAILED' in stdout:
                    print("\n✗ DAG 执行失败！")
                    return False, stdout
        
        # 检查是否有失败的任务
        for task in tasks:
            cmd = f"find {log_dir}/{task} -name '*.log' -exec grep -l 'ERROR\\|FAILED' {{}} \\; 2>/dev/null | head -1"
            stdout, _ = run_docker_command(cmd, timeout=10)
            
            if stdout.strip():
                print(f"\n✗ 任务 {task} 失败！")
                # 读取失败日志
                cmd = f"tail -50 {stdout.strip()}"
                log_stdout, _ = run_docker_command(cmd, timeout=10)
                return False, log_stdout
        
        if elapsed > 120 and len(tasks) == 0:
            print("\n警告: 2分钟后仍无任务日志，可能存在问题")

def get_report():
    """获取回测报告"""
    print("\n查找回测报告...")
    
    cmd = "ls -lt /tmp/backtest_reports/ 2>/dev/null | head -5"
    stdout, _ = run_docker_command(cmd)
    
    if not stdout.strip():
        print("  未找到报告文件")
        return None
    
    # 提取最新的报告文件
    lines = stdout.strip().split('\n')
    for line in lines:
        if '.json' in line:
            parts = line.split()
            if len(parts) >= 9:
                filename = parts[-1]
                print(f"  找到报告: {filename}")
                
                # 读取报告内容
                cmd = f"cat /tmp/backtest_reports/{filename}"
                stdout, _ = run_docker_command(cmd, timeout=10)
                
                try:
                    report = json.loads(stdout)
                    return report
                except:
                    print("  报告格式错误")
                    return None
    
    return None

def print_report(report):
    """打印回测报告"""
    if not report:
        print("\n无法获取报告内容")
        return
    
    print("\n" + "=" * 70)
    print("回测报告总结".center(70))
    print("=" * 70)
    print(f"策略名称: {report.get('strategy_name', 'N/A')}")
    print(f"股票代码: {report.get('security', 'N/A')}")
    print(f"回测时间: {report.get('start_date', 'N/A')} ~ {report.get('end_date', 'N/A')}")
    print(f"回测频率: {report.get('freq', 'N/A')}")
    if report.get('benchmark'):
        print(f"基准指数: {report['benchmark']}")
    print(f"初始资金: ¥{report.get('start_value', 0):,.2f}")
    print(f"最终资金: ¥{report.get('end_value', 0):,.2f}")
    print(f"总收益率: {report.get('total_return_pct', 0):.2f}%")
    print(f"年化收益: {report.get('annual_return', 0):.2f}%")
    print(f"夏普比率: {report.get('sharpe_ratio', 0):.4f}")
    print(f"最大回撤: {report.get('max_drawdown_pct', 0):.2f}%")
    print(f"交易次数: {report.get('total_trades', 0)}")
    print(f"胜率: {report.get('win_rate', 0):.2f}%")
    
    if 'avg_win' in report and 'avg_loss' in report:
        print(f"平均盈利: ¥{report['avg_win']:,.2f}")
        print(f"平均亏损: ¥{report['avg_loss']:,.2f}")
        print(f"盈亏比: {report.get('profit_loss_ratio', 0):.2f}")
    
    print("=" * 70)

def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("通用回测平台 DAG 执行器".center(70))
    print("=" * 70)
    print()
    
    # 1. 触发 DAG
    run_id = trigger_dag()
    if not run_id:
        print("\nDAG 触发失败，退出")
        return
    
    # 2. 等待完成
    print(f"\n等待 DAG 执行完成（最长等待 10 分钟）...")
    result = wait_for_completion(run_id, max_wait=600)
    
    if isinstance(result, tuple):
        success, log = result
        
        if success:
            # 从日志中提取回测结果
            print("\n" + "=" * 70)
            print("回测结果（从日志）".center(70))
            print("=" * 70)
            
            # 提取回测报告部分
            in_report = False
            for line in log.split('\n'):
                if '回测报告总结' in line or '=' * 40 in line:
                    in_report = True
                if in_report:
                    print(line)
                if in_report and '=' * 60 in line:
                    break
        else:
            print("\n执行失败，显示错误日志:")
            print("-" * 70)
            print(log)
    
    # 3. 尝试获取 JSON 报告
    time.sleep(2)
    report = get_report()
    if report:
        print_report(report)
    
    print("\n" + "=" * 70)
    print("执行完成")
    print("=" * 70)

if __name__ == '__main__':
    main()
