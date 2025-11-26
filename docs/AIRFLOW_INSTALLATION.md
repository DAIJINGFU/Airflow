# ⚠️ 重要提醒：Airflow 版本要求

## 🔴 必须安装 Apache Airflow 3.x 版本！

**切勿安装 Airflow 2.x 版本！**

本项目要求使用 **Apache Airflow 3.x** 版本。请确保：

1. ✅ Docker Compose 配置文件中使用的镜像版本为 `apache/airflow:3.x`
2. ✅ 在安装或升级时始终指定 3.x 版本
3. ❌ 不要使用 `apache/airflow:2.x` 或更早版本

---

## 安装步骤

### 前置要求

- Docker Desktop 已安装并运行
- WSL 2 已启用（Windows 系统）
- 足够的磁盘空间（至少 10GB）

### 快速启动

1. **初始化环境**

   ```bash
   echo -e "AIRFLOW_UID=$(id -u)" > .env
   ```

2. **初始化数据库**

   ```bash
   docker-compose up airflow-init
   ```

3. **启动所有服务**

   ```bash
   docker-compose up -d
   ```

4. **访问 Web UI**
   - URL: http://localhost:8080
   - 默认用户名: `airflow`
   - 默认密码: `airflow`

### 验证安装

运行以下命令验证 Airflow 版本：

```bash
docker-compose exec airflow-webserver airflow version
```

输出应显示 `3.x.x` 版本号。

---

## ✅ 安装验证结果

### 已安装版本

- **Airflow 版本**: 3.1.3 ✅
- **安装日期**: 2025-11-24
- **安装方式**: Docker Compose

### 运行中的服务

所有核心服务已成功启动：

- ✅ **API Server** (端口 8080) - 正常运行
- ✅ **Scheduler** - 正常运行
- ✅ **Worker** (Celery) - 正常运行
- ✅ **Triggerer** - 正常运行
- ✅ **PostgreSQL 13** - 正常运行
- ✅ **Redis** - 正常运行

### Web UI 访问

- **URL**: http://localhost:8080
- **用户名**: airflow
- **密码**: airflow
- **状态**: ✅ 可访问

### 重要提醒

⚠️ Airflow 3.x 将 `webserver` 命令更改为 `api-server`

- 旧命令: `airflow webserver`
- 新命令: `airflow api-server`

---

## 常用命令

### 服务管理

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### Airflow 命令

```bash
# 查看版本
docker exec airflow_new-airflow-scheduler-1 airflow version

# 列出 DAG
docker exec airflow_new-airflow-scheduler-1 airflow dags list

# 触发 DAG
docker exec airflow_new-airflow-scheduler-1 airflow dags trigger <dag_id>
```

---

## 当前安装时间

- 安装日期: 2025-11-24
- Airflow 版本: 3.1.3 ✅
