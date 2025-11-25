"""
测试 DAG - 验证 Airflow 3.x 功能
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 11, 24),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def print_airflow_version():
    """打印 Airflow 版本信息"""
    import airflow
    print(f"Airflow 版本: {airflow.__version__}")
    print("✅ Airflow 3.x 运行正常！")

def test_task():
    """测试任务"""
    print("这是一个测试任务")
    print("Airflow 3.x 功能验证成功！")
    return "Success"

with DAG(
    'test_airflow_3x',
    default_args=default_args,
    description='测试 Airflow 3.x 安装',
    schedule=None,  # 手动触发 (Airflow 3.x 使用 schedule 而非 schedule_interval)
    catchup=False,
    tags=['test', 'airflow-3x'],
) as dag:

    # 任务 1: 打印版本信息
    version_task = PythonOperator(
        task_id='print_version',
        python_callable=print_airflow_version,
    )

    # 任务 2: 测试 Bash 操作
    bash_task = BashOperator(
        task_id='test_bash',
        bash_command='echo "Bash operator 工作正常！"',
    )

    # 任务 3: 测试 Python 操作
    python_task = PythonOperator(
        task_id='test_python',
        python_callable=test_task,
    )

    # 设置任务依赖
    version_task >> bash_task >> python_task
