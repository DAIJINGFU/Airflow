"""
示例 DAG - 演示基本的 Airflow 功能
这个 DAG 会每天运行一次，执行几个简单的任务
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

def print_context(**context):
    """打印任务执行上下文信息"""
    print(f"执行日期: {context['ds']}")
    print(f"任务实例: {context['task_instance']}")
    print(f"DAG 运行: {context['dag_run']}")
    return "任务执行成功！"

def calculate_sum():
    """计算1到100的和"""
    result = sum(range(1, 101))
    print(f"1到100的和是: {result}")
    return result

# 默认参数
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 11, 20),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# 创建 DAG
with DAG(
    dag_id='example_hello_world',
    default_args=default_args,
    description='一个简单的示例 DAG',
    schedule=timedelta(days=1),  # Airflow 3.x 使用 schedule 代替 schedule_interval
    start_date=datetime(2025, 11, 20),
    catchup=False,
    tags=['example', 'tutorial'],
) as dag:

    # 任务 1: 打印 Hello World
    task_hello = BashOperator(
        task_id='say_hello',
        bash_command='echo "Hello from Airflow 3.1.3!"',
    )

    # 任务 2: 打印当前日期和时间
    task_date = BashOperator(
        task_id='print_date',
        bash_command='date',
    )

    # 任务 3: 使用 Python 函数打印上下文信息
    task_context = PythonOperator(
        task_id='print_context',
        python_callable=print_context,
    )

    # 任务 4: 计算数学运算
    task_calculate = PythonOperator(
        task_id='calculate_sum',
        python_callable=calculate_sum,
    )

    # 任务 5: 打印完成消息
    task_finish = BashOperator(
        task_id='finish',
        bash_command='echo "所有任务执行完成！"',
    )

    # 定义任务依赖关系
    # task_hello 和 task_date 可以并行执行
    # 它们完成后执行 task_context
    # task_context 完成后执行 task_calculate
    # 最后执行 task_finish
    [task_hello, task_date] >> task_context >> task_calculate >> task_finish
