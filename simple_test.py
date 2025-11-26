import subprocess
import time

# 触发 DAG
print("触发 DAG...")
result = subprocess.run(
    "docker exec airflow_new-airflow-standalone-1 airflow dags trigger universal_backtest_platform",
    shell=True,
    capture_output=True,
    text=True
)
print(result.stdout)
print(result.stderr)

# 等待60秒
print("\n等待60秒让任务执行...")
for i in range(6):
    time.sleep(10)
    print(f"  已等待 {(i+1)*10} 秒...")

# 检查报告
print("\n检查回测报告...")
result = subprocess.run(
    "docker exec airflow_new-airflow-standalone-1 ls -lt /tmp/backtest_reports/",
    shell=True,
    capture_output=True,
    text=True
)
print(result.stdout)

# 读取最新报告
result = subprocess.run(
    'docker exec airflow_new-airflow-standalone-1 bash -c "cat $(ls -t /tmp/backtest_reports/*.json 2>/dev/null | head -1)"',
    shell=True,
    capture_output=True,
    text=True
)
if result.stdout:
    import json
    report = json.loads(result.stdout)
    print("\n=== 回测结果 ===")
    print(f"策略: {report['strategy_name']}")
    print(f"股票: {report['security']}")
    print(f"总收益率: {report['total_return_pct']:.2f}%")
    print(f"夏普比率: {report['sharpe_ratio']:.2f}")
    print(f"最大回撤: {report['max_drawdown_pct']:.2f}%")
