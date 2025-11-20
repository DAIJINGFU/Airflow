# Apache Airflow 3.1.3 安装成功！

## 🎉 安装完成

恭喜！您已经成功安装了最新版本的 Apache Airflow (3.1.3)。

## 📋 登录信息

- **Web UI 地址**: http://localhost:8080
- **用户名**: `airflow`
- **密码**: `airflow`

## 🚀 快速开始

### 访问 Airflow Web 界面

在浏览器中打开 http://localhost:8080，使用上面的用户名和密码登录。

### 管理 Airflow 服务

#### 启动所有服务

```powershell
docker compose up -d
```

#### 停止所有服务

```powershell
docker compose down
```

#### 查看服务状态

```powershell
docker compose ps
```

#### 查看日志

```powershell
# 查看所有服务日志
docker compose logs

# 查看特定服务日志
docker compose logs airflow-apiserver
docker compose logs airflow-scheduler
```

#### 重启服务

```powershell
docker compose restart
```

## 📁 项目结构

```
airflow/
├── dags/              # 存放您的 DAG 文件（工作流定义）
├── logs/              # Airflow 日志文件
├── plugins/           # 自定义插件
├── config/            # 配置文件
├── .env               # 环境变量
└── docker-compose.yaml # Docker Compose 配置
```

## 📝 创建您的第一个 DAG

在 `dags/` 目录下创建一个 Python 文件，例如 `my_first_dag.py`：

```python
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 11, 20),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'my_first_dag',
    default_args=default_args,
    description='我的第一个 DAG',
    schedule_interval=timedelta(days=1),
    catchup=False,
) as dag:

    task1 = BashOperator(
        task_id='print_hello',
        bash_command='echo "Hello from Airflow 3.1.3!"',
    )

    task2 = BashOperator(
        task_id='print_date',
        bash_command='date',
    )

    task1 >> task2  # task1 完成后执行 task2
```

保存文件后，Airflow 会自动检测并加载新的 DAG（可能需要几秒钟）。

## 🔧 运行中的容器

当前运行的服务包括：

- **airflow-apiserver**: Web UI 和 API 服务器 (端口 8080)
- **airflow-scheduler**: 调度器，负责调度任务
- **airflow-dag-processor**: DAG 处理器
- **airflow-triggerer**: 触发器，处理延迟任务
- **airflow-worker**: Celery Worker，执行任务（按需启动）
- **postgres**: PostgreSQL 数据库
- **redis**: Redis 消息队列

## 📚 更多资源

- [Airflow 官方文档](https://airflow.apache.org/docs/apache-airflow/stable/)
- [Airflow 教程](https://airflow.apache.org/docs/apache-airflow/stable/tutorial/index.html)
- [DAG 编写指南](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html)

## ⚠️ 注意事项

1. 这是开发环境配置，不建议直接用于生产环境
2. 默认用户名和密码应该在生产环境中更改
3. DAG 文件会被自动监控，修改后会自动重新加载
4. 日志文件会存储在 `logs/` 目录下

## 🛑 完全清理（如需重新开始）

```powershell
# 停止并删除所有容器和数据卷
docker compose down -v

# 清理本地文件
Remove-Item -Recurse -Force logs/*
Remove-Item -Recurse -Force dags/*
Remove-Item -Recurse -Force plugins/*
Remove-Item -Recurse -Force config/*
```

---

**安装日期**: 2025 年 11 月 20 日  
**Airflow 版本**: 3.1.3  
**Python 版本**: 3.12
