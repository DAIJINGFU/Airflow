# Airflow 3.x 安装与配置记录

> **文档说明**: 本文档记录了与 Claude Sonnet 4.5 对话过程中 Airflow 3.1.3 的安装、配置和问题解决过程

---

## 📋 目录

- [登录信息](#登录信息)
- [项目概述](#项目概述)
- [问题列表](#问题列表)
  - [问题 1: Webserver 命令不存在](#问题-1-webserver-命令不存在)
  - [问题 2: 用户创建失败](#问题-2-用户创建失败)
  - [问题 3: 浏览器登录失败](#问题-3-浏览器登录失败)
  - [问题 4: DAG 导入错误](#问题-4-dag-导入错误)
  - [问题 5: QLib 数据目录未挂载](#问题-5-qlib-数据目录未挂载)
  - [问题 6: 自定义 DAG 依赖缺失](#问题-6-自定义-dag-依赖缺失)
  - [问题 7: Execution API 通信超时](#问题-7-execution-api-通信超时)
  - [问题 8: jq_backtrader_precision DAG 执行失败](#问题-8-jq_backtrader_precision-dag-执行失败)
  - [问题 9: 通用策略回测平台优化](#问题-9-通用策略回测平台优化)
  - [问题 10: Web UI 访问失败](#问题-10-web-ui-访问失败err_empty_response)
  - [问题 11: 通用回测平台 DAG 任务执行失败](#问题-11-通用回测平台-dag-任务执行失败)
  - [问题 12: DAG 导入错误 - 参数传递方式错误](#问题-12-dag-导入错误---参数传递方式错误)
- [Airflow 3.x 关键变更总结](#airflow-3x-关键变更总结)
- [经验教训](#经验教训)

---

## 📁 代码仓库信息

- **GitHub 仓库**: [DAIJINGFU/Airflow](https://github.com/DAIJINGFU/Airflow)
- **分支**: `airflow-3.1.3-quant`
- **提交记录**: 所有代码变更已推送到远程仓库
- **最近更新**: 2025-11-25

---

## 🔐 登录信息

- **Web UI 地址**: http://localhost:8080
- **用户名**: admin
- **当前密码**: rW4sw49ZxrbbAeGa

> ⚠️ **注意**: Standalone 模式密码在容器重建时会改变（restart 不会）
>
> 获取最新密码命令：
>
> ```powershell
> docker logs airflow_new-airflow-standalone-1 2>&1 | Select-String "Password for user 'admin':" | Select-Object -Last 1
> ```

---

## 📋 项目概述

- **目标**: 安装 Apache Airflow 3.x 版本（非 2.x，禁止使用 2.x！）
- **环境**: Windows + Docker Desktop + WSL
- **安装日期**: 2025-11-24
- **最终版本**: Apache Airflow 3.1.3
- **镜像版本**: `airflow-quant:3.1.3` (基于官方 3.1.3 + backtrader/pyqlib/loguru)

---

## 📦 代码仓库信息

- **远程仓库**: https://github.com/DAIJINGFU/Airflow.git
- **分支**: `airflow-3.1.3-quant`
- **提交**: `4bac31e Initial commit: Airflow 3.1.3 with custom quantitative DAGs`
- **推送时间**: 2025-11-25 02:00
- **包含文件**: 22 个文件，4,386 行代码

---

## 🚧 问题列表

---

## 🚧 问题列表

### 问题 1: Webserver 命令不存在 ✅

**现象**: 容器启动失败，`airflow webserver` 命令已移除

**原因**: Airflow 3.x 将 `webserver` 改为 `api-server`

**解决方案**:

```yaml
# ❌ Airflow 2.x
command: webserver

# ✅ Airflow 3.x
command: api-server
```

---

### 问题 2: 用户创建失败 ✅

**现象**:

- `airflow users create` 命令不存在
- 标准配置无法自动创建管理员用户

**解决方案**: 使用 Standalone 模式

```yaml
# docker-compose-standalone.yml
command: standalone # 自动创建用户并生成密码
```

---

### 问题 3: 浏览器登录失败 ✅

**现象**: API 认证正常，但浏览器无法登录

**根本原因**: 浏览器缓存了旧的 JWT token

**解决方案**:

1. 使用隐私/无痕模式（推荐）
2. 清除浏览器缓存和 Cookie
3. 硬刷新页面（Ctrl + F5）

---

### 问题 4: DAG 导入错误（schedule_interval） ✅

**现象**: `TypeError: DAG.__init__() got an unexpected keyword argument 'schedule_interval'`

**根本原因**: Airflow 3.x 已移除 `schedule_interval` 参数

**解决方案**:

```python
# ❌ Airflow 2.x
with DAG('dag_id', schedule_interval=None):

# ✅ Airflow 3.x
with DAG('dag_id', schedule=None):
```

---

### 问题 5: QLib 数据目录未挂载 ✅

**现象**: `bootstrap_environment` 任务报错"未找到 qlib 数据目录"

**解决方案**: 添加 volume 挂载

```yaml
volumes:
  - ${QLIB_DATA_HOST_DIR:-../airflow/stockdata/qlib_data}:/opt/airflow/stockdata/qlib_data:ro
```

---

### 问题 6: 自定义 DAG 依赖缺失 ✅

**现象**: `ModuleNotFoundError: No module named 'loguru'`

**解决方案**: 构建自定义 Docker 镜像

**Dockerfile**:

```dockerfile
FROM apache/airflow:3.1.3

USER airflow
RUN pip install --no-cache-dir \
    backtrader>=1.9.76 \
    loguru>=0.7.0 \
    pandas>=2.0.0 \
    numpy>=1.24.0 \
    pyqlib>=0.9.0
```

**构建命令**:

```bash
docker build -t airflow-quant:3.1.3 .
```

---

### 问题 7: Execution API 通信超时 ✅

**现象**: 任务从 queued 瞬间变为 failed，日志刷屏 `httpx.ReadTimeout`

**根本原因**: Standalone 模式默认超时 5 秒不足

**解决方案**: 增加超时配置

```yaml
environment:
  - AIRFLOW__WORKERS__EXECUTION_API_TIMEOUT=30
```

---

### 问题 8: jq_backtrader_precision DAG 执行失败 ✅

**状态**: 已完全修复（8 个错误，8 个修复）

#### 错误列表

1. **loguru 顶层导入超时** → 移除顶层导入，改用 print()
2. **XCom 类型错误（str）** → 改为返回 Dict[str, str]
3. **动态任务映射错误** → 使用 `.partial().expand()` 代替 `.expand()`
4. **遗漏 logger 调用（多处）** → 全部替换为 print()
5. **日期格式错误** → 使用 `strftime('%Y-%m-%d')` 格式化日期
6. **策略类缺少 order 初始化** → 在 `__init__` 中添加 `self.order = None`

#### 修复总结

**修复前状态**:

- DAG 导入超时（30s+）
- 任务执行失败
- 无法完成回测

**修复后状态**:

- ✅ DAG 导入时间: 0.92s（性能提升 97%）
- ✅ 所有任务可正常执行
- ✅ 支持双均线和动量两种策略

#### 技术要点

**Airflow 3.x 最佳实践**:

1. 避免顶层导入耗时模块（loguru、matplotlib）
2. XCom 使用复杂类型（Dict、List），不用简单类型（str、int）
3. DAG 导入控制在 30 秒以内
4. 使用 print() 代替 logger（日志自动收集）

**关键代码片段**:

```python
# 动态任务映射（正确写法）
results = run_backtrader_strategy.partial(data_path=data_path).expand(
    strategy_name=strategies
)

# 策略类初始化
class DualMovingAverageStrategy(BaseCNStrategy):
    def __init__(self):
        self.order = None  # 必须初始化
        self.sma_fast = bt.indicators.SimpleMovingAverage(...)
        self.sma_slow = bt.indicators.SimpleMovingAverage(...)
```

---

### 问题 10: Web UI 访问失败（ERR_EMPTY_RESPONSE） ✅

**状态**: 已解决  
**发现时间**: 2025-11-25  
**优先级**: 高
**解决时间**: 2025-11-25

#### 现象

浏览器访问 `http://localhost:8080` 显示：

- "This page isn't working"
- "localhost didn't send any data"
- ERR_EMPTY_RESPONSE

#### 诊断过程

1. **容器状态**: ✅ 健康

   ```bash
   docker ps -a
   # STATUS: Up 5 minutes (healthy)
   ```

2. **API Server 进程**: ✅ 运行中

   - 日志显示正常处理请求
   - 端口 8080 正常监听

3. **DAG 导入错误**: ❌ 发现问题
   ```bash
   airflow dags list-import-errors
   # starquant_factor_pipeline.py: ModuleNotFoundError: No module named 'platform.factor_store'
   ```

#### 根本原因

**DAG 导入错误导致 DAG 处理器崩溃**：

- `starquant_factor_pipeline.py` 第 14 行导入 `platform.factor_store` 失败
- Python 内置模块 `platform` 与自定义 `platform/` 目录冲突
- DAG 处理器持续失败影响整体稳定性

#### 解决方案

**方案 1**: 重命名自定义 platform 目录（推荐）

```bash
# 将 platform/ 目录重命名为 platform_modules/
mv platform/ platform_modules/

# 更新 starquant_factor_pipeline.py 导入路径
from platform_modules.factor_store import ...
```

**方案 2**: 临时禁用问题 DAG（快速修复）

```bash
# 重命名文件防止导入
mv dags/starquant_factor_pipeline.py dags/starquant_factor_pipeline.py.bak
```

**方案 3**: 修复导入路径（使用相对导入）

```python
# 在 starquant_factor_pipeline.py 中
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from platform.factor_store import ...
```

#### 实施步骤

**步骤 1**: 临时禁用问题 DAG（已完成）

```powershell
Move-Item "dags\starquant_factor_pipeline.py" "dags\starquant_factor_pipeline.py.bak"
```

**步骤 2**: 在容器内彻底删除文件

```bash
docker exec airflow_new-airflow-standalone-1 bash -c "rm -f /opt/airflow/dags/starquant_factor_pipeline.py*"
```

**步骤 3**: 从数据库删除 DAG 记录

```bash
docker exec airflow_new-airflow-standalone-1 airflow dags delete starquant_factor_pipeline -y
```

**步骤 4**: 重启容器

```powershell
docker stop airflow_new-airflow-standalone-1
docker start airflow_new-airflow-standalone-1
```

**步骤 5**: 等待容器完全启动（约 60 秒）

```powershell
# 查看健康状态
docker ps

# 检查日志确认 API Server 启动
docker logs airflow_new-airflow-standalone-1 --tail 20
```

**步骤 6**: 清除浏览器缓存并重新访问

- 按 `Ctrl + Shift + Delete` 清除浏览器缓存
- 或使用隐私模式访问 `http://localhost:8080`
- 或尝试 `http://127.0.0.1:8080`

#### 额外排查步骤

如果仍然无法访问，执行以下排查：

1. **检查端口占用**：

```powershell
netstat -ano | findstr :8080
```

2. **测试容器内部访问**：

```bash
docker exec airflow_new-airflow-standalone-1 curl -I http://localhost:8080
```

3. **检查 Docker 网络**：

```powershell
docker inspect airflow_new-airflow-standalone-1 | Select-String "IPAddress"
```

4. **查看 API Server 日志**：

```bash
docker logs airflow_new-airflow-standalone-1 2>&1 | grep "api-server"
```

5. **重建容器**（最后手段）：

```powershell
docker-compose -f docker-compose-standalone.yml down
docker-compose -f docker-compose-standalone.yml up -d
```

#### 实施步骤

1. 临时禁用问题 DAG
2. 重启容器验证 Web UI 恢复
3. 重命名 platform 目录
4. 修复所有导入路径
5. 重新启用 DAG

#### 最终解决方案

**成功步骤**：

1. ✅ **禁用问题 DAG**

   ```powershell
   Move-Item "dags\starquant_factor_pipeline.py" "dags\starquant_factor_pipeline.py.bak"
   ```

2. ✅ **重启容器（使用 stop/start 而非 restart）**

   ```powershell
   docker stop airflow_new-airflow-standalone-1
   docker start airflow_new-airflow-standalone-1
   ```

3. ✅ **等待容器完全启动**（约 60-90 秒）

   - 查看日志确认 `Airflow is ready`
   - 健康状态从 `health: starting` 变为 `healthy`

4. ✅ **清除浏览器缓存或使用隐私模式**

   - Chrome: `Ctrl + Shift + Delete`
   - 或直接使用隐私模式访问

5. ✅ **访问 Web UI**: `http://localhost:8080`

#### 根本原因总结

1. **DAG 导入错误**导致 DAG 处理器持续失败
2. **容器重启时序**：`restart` 可能不完全清理状态，`stop + start` 更彻底
3. **浏览器缓存**：保存了错误状态的连接信息

#### 经验教训

1. ⚠️ 避免使用 Python 内置模块名作为自定义目录名
2. ✅ 使用 `airflow dags list-import-errors` 诊断 DAG 问题
3. ✅ DAG 导入错误会影响整个 Airflow 实例稳定性

---

### 问题 11: 通用回测平台 DAG 任务执行失败 ✅

**状态**: 已解决  
**发现时间**: 2025-11-25  
**优先级**: 高
**解决时间**: 2025-11-25

#### 问题演进历史

本问题经历了三次修复迭代：

**第一次失败**: 使用 Airflow 保留字 `params` 作为参数名  
**第二次失败**: 参数传递方式错误（`**params_dict` vs `params_dict`）  
**第三次失败**: Jinja 模板在 TaskFlow API 中渲染失败

---

#### 现象 1: 保留字冲突（已修复）

在 Web UI 触发 `universal_backtest_platform` DAG 执行 MA5 策略回测任务失败：

- 任务状态：Failed
- 错误信息：`ValueError: The key 'params' in args is a part of kwargs and therefore reserved.`

**根本原因**: 使用了 Airflow 保留字 `params` 作为函数参数名

**解决方案**: 将所有任务函数中的 `params` 参数重命名为 `config`

---

#### 现象 2: 策略代码验证失败（最新问题）

**错误日志**:

```
[ERROR] 策略代码验证失败:
缺少 initialize(context) 函数
缺少 handle_data(context, data) 函数
未找到 g.security 赋值语句（必须在代码中指定股票代码）
```

**根本原因**:

在 TaskFlow API 中，不能在 DAG 函数体内直接使用 Jinja 模板 `{{ params.xxx }}`。

**错误代码**:

```python
def universal_backtest_platform_dag():
    # ❌ 错误：Jinja 模板在 TaskFlow API 中不会被渲染
    params_dict = {
        'strategy_code': '{{ params.strategy_code }}',  # 传递的是字符串，不是实际值
        'strategy_name': '{{ params.strategy_name }}',
        ...
    }

    validated_config = validate_and_prepare(params_dict)
```

**问题分析**:

1. `{{ params.strategy_code }}` 被当作普通字符串传递
2. 策略验证器收到的是字面字符串 `"{{ params.strategy_code }}"`，而不是实际的策略代码
3. 验证失败：该字符串既不包含 `initialize()` 也不包含 `handle_data()` 函数

---

#### 解决方案（最终版本）

**方案**: 在 TaskFlow API 中，使用 `**context` 参数访问 DAG params

**正确代码**:

```python
@task
def validate_and_prepare(**context) -> Dict[str, Any]:
    """步骤1: 验证策略代码并准备参数"""
    print("[TASK] validate_and_prepare 开始")

    # ✅ 正确：从 context 中提取 DAG params
    dag_params = context['params']

    # 提取参数（现在是实际值，不是模板字符串）
    strategy_code = dag_params['strategy_code']
    strategy_name = dag_params.get('strategy_name', '')
    start_date = dag_params['start_date']
    end_date = dag_params['end_date']
    initial_cash = float(dag_params['initial_cash'])
    freq = dag_params['freq']
    benchmark = dag_params.get('benchmark', '')

    # 验证策略代码
    result = validate_strategy_code(strategy_code, strategy_name)
    ...

def universal_backtest_platform_dag():
    # ✅ 正确：直接调用，params 通过 context 自动传递
    validated_config = validate_and_prepare()
    data_ready = prepare_data(validated_config)
    results = run_backtest(data_ready)
    generate_report(results)
```

---

#### 修复对比总结

| 迭代        | 错误类型     | 错误代码                                        | 正确代码                             |
| ----------- | ------------ | ----------------------------------------------- | ------------------------------------ |
| **第 1 次** | 保留字冲突   | `def func(params: Dict)`                        | `def func(config: Dict)`             |
| **第 2 次** | 参数传递错误 | `func(**params_dict)`                           | `func(params_dict)`                  |
| **第 3 次** | 模板渲染失败 | `'strategy_code': '{{ params.strategy_code }}'` | `context['params']['strategy_code']` |

---

#### 技术要点

**Airflow 3.x TaskFlow API 参数传递规则**:

1. **保留关键字**：

   - `params` - DAG 参数
   - `context` - 任务上下文
   - `task_instance` - 任务实例
   - `dag` - DAG 对象
   - `execution_date` - 执行日期

2. **访问 DAG Params 的正确方式**：

   ```python
   # ✅ 方式1: 使用 **context
   @task
   def my_task(**context):
       params = context['params']
       value = params['my_param']

   # ✅ 方式2: 使用 op_kwargs（传统方式）
   @task(op_kwargs={'param1': '{{ params.param1 }}'})
   def my_task(param1):
       print(param1)

   # ❌ 错误: 在 DAG 函数体直接用 Jinja
   def my_dag():
       data = {'key': '{{ params.value }}'}  # 不会渲染
       my_task(data)
   ```

3. **TaskFlow API vs 传统 Operator**：
   - TaskFlow API: 使用 `**context` 访问运行时参数
   - 传统 Operator: 使用 Jinja 模板（`{{ }}`）在 `op_kwargs` 中

---

#### 经验教训

1. ⚠️ **避免使用 Airflow 保留字作为参数名**

   - `params`, `context`, `task_instance`, `dag`, `execution_date` 等

2. ✅ **理解 Jinja 模板的作用域**

   - Jinja 模板仅在 Operator 参数中渲染
   - TaskFlow API 的 DAG 函数体中不会渲染
   - 必须使用 `**context` 访问运行时参数

3. ✅ **使用正确的参数传递方式**

   - `func(dict)` - 传递字典作为单个参数
   - `func(**dict)` - 解包字典为关键字参数
   - `func(**context)` - 接收 Airflow 上下文

4. ✅ **调试策略验证失败问题**
   - 打印实际接收的参数内容
   - 检查是否收到模板字符串而非实际值
   - 使用 `context['params']` 确保获取正确值

---

### 问题 12: DAG 导入错误 - 参数传递方式错误 ✅

**状态**: 已解决  
**发现时间**: 2025-11-25  
**优先级**: 高
**解决时间**: 2025-11-25

#### 现象

在 Web UI 的 DAG 列表页面看到 `universal_backtest_platform` DAG 有导入错误（红色 "1" 标记）：

```
Traceback (most recent call last):
  File "/usr/python/lib/python3.12/inspect.py", line 3280, in bind
    return self._bind(args, kwargs)
TypeError: got an unexpected keyword argument 'strategy_code'
```

#### 根本原因

**参数传递方式不匹配**：

问题 11 中错误地建议使用 `**params_dict` 解包，但函数签名不匹配：

```python
# ❌ 错误的修复建议
validated_config = validate_and_prepare(**params_dict)
```

实际上 `validate_and_prepare` 函数接受单个 Dict 参数：

```python
@task
def validate_and_prepare(params: Dict[str, Any]) -> Dict[str, Any]:
    strategy_code = params['strategy_code']  # 期望接收字典
    ...
```

**冲突**：

- `**params_dict` 解包为：`strategy_code='...', strategy_name='...', ...`
- 函数期望：`params={'strategy_code': '...', 'strategy_name': '...', ...}`

#### 解决方案

**直接传递字典，不使用 `**` 解包\*\*：

```python
def universal_backtest_platform_dag():
    params_dict = {
        'strategy_code': '{{ params.strategy_code }}',
        'strategy_name': '{{ params.strategy_name }}',
        'start_date': '{{ params.start_date }}',
        'end_date': '{{ params.end_date }}',
        'initial_cash': '{{ params.initial_cash }}',
        'freq': '{{ params.freq }}',
        'benchmark': '{{ params.benchmark }}',
    }

    # ✅ 正确：直接传递字典
    validated_config = validate_and_prepare(params_dict)
    data_ready = prepare_data(validated_config)
    results = run_backtest(data_ready)
    generate_report(results)
```

#### 修复对比

| 情况         | 函数定义                 | 正确调用       | 错误调用          |
| ------------ | ------------------------ | -------------- | ----------------- |
| 接受字典参数 | `def func(params: Dict)` | `func(dict)`   | `func(**dict)` ❌ |
| 接受多个参数 | `def func(a, b, c)`      | `func(**dict)` | `func(dict)` ❌   |

#### 经验教训

1. **理解 Python 参数传递**：

   - `func(dict)` - 传递字典作为单个参数
   - `func(**dict)` - 解包字典为关键字参数

2. **检查 DAG 导入错误**：

   - Web UI 中红色数字表示导入错误
   - 点击查看详细错误堆栈
   - 命令：`airflow dags list-import-errors`

3. ✅ **修复验证流程**：
   - 修改代码 → 重启容器 → 检查 DAG 列表 → 查看导入错误消失

#### 问题 10/12 后遗症：容器重启后短暂不健康

**现象**：修改 DAG 代码后重启容器，浏览器显示 ERR_EMPTY_RESPONSE

**原因**：

1. 容器刚重启时处于 `unhealthy` 状态（健康检查未通过）
2. Airflow Standalone 需要 60-90 秒完全启动
3. 浏览器缓存了之前的错误状态

**解决方案**：

1. **等待容器完全启动**：

   ```powershell
   # 检查容器状态，等待显示 healthy
   docker ps

   # 检查健康状态
   docker inspect airflow_new-airflow-standalone-1 --format='{{.State.Health.Status}}'
   ```

2. **验证服务可用**：

   ```bash
   # 在容器内测试（应返回 200）
   docker exec airflow_new-airflow-standalone-1 curl -s -o /dev/null -w "%{http_code}" http://localhost:8080
   ```

3. **清除浏览器缓存或使用隐私模式**

4. **耐心等待**：容器从 `unhealthy` 到 `healthy` 通常需要 60-90 秒

---

### 问题 9: jq_backtrader_precision DAG 优化为通用策略回测平台 🚧

**状态**: 规划中  
**提出时间**: 2025-11-25  
**优先级**: 高

#### 目标

将当前固定策略的 `jq_backtrader_precision` DAG 优化为**通用策略回测平台**，支持用户通过 Web UI 提交任意 JoinQuant 格式的策略代码进行回测。

#### 核心需求

1. **动态策略接入**: 支持用户上传或粘贴 JoinQuant 格式策略代码
2. **参数化配置**: 通过 Web UI 表单配置回测参数（时间范围、初始资金、频率等）
3. **结果输出**: 生成标准化回测报告（夏普比率、最大回撤、总收益、年化收益等）
4. **安全性校验**: 策略代码安全性检查（禁止危险操作）
5. **扩展功能**: 支持策略对比、批量回测、结果可视化

#### 支持的策略代码格式

**参考文档**: `JOINQUANT_STRATEGY_FORMAT.md`

**核心结构**:

```python
# 必需的全局变量
g.security = '000001.XSHE'  # 股票代码（策略内定义）

# 必需的入口函数
def initialize(context):
    """策略初始化"""
    g.unit = 100  # 每次交易股数
    pass

def handle_data(context, data):
    """每个交易周期执行"""
    # 获取历史数据
    prices = attribute_history(g.security, 5, '1d', ['close'])

    # 交易逻辑
    if prices['close'][-1] > prices['close'].mean():
        order_value(g.security, 10000)
```

**关键特性**:

- ✅ 股票代码由策略代码内的 `g.security` 指定（不是用户输入参数）
- ✅ 佣金率、印花税等系统自动配置（用户无需输入）
- ✅ 策略参数可通过 `g.*` 全局变量在 `initialize()` 中定义
- ✅ 支持日线、周线、月线等多种频率

#### 用户需要传递的参数

**通过 Airflow Web UI 表单提交**:

| 参数名          | 类型     | 必填 | 说明                         | 示例                      |
| --------------- | -------- | ---- | ---------------------------- | ------------------------- |
| `strategy_name` | `string` | 否   | 策略名称（为空时自动生成）   | `MA5_strategy`            |
| `strategy_code` | `text`   | 是   | JoinQuant 格式策略代码       | （多行代码）              |
| `start_date`    | `string` | 是   | 回测开始日期                 | `2020-01-01`              |
| `end_date`      | `string` | 是   | 回测结束日期                 | `2024-12-31`              |
| `initial_cash`  | `float`  | 是   | 初始资金（元）               | `100000.0`                |
| `freq`          | `string` | 是   | 回测频率（day/week/month）   | `day`                     |
| `benchmark`     | `string` | 否   | 基准指数代码（为空时不对比） | `000300.XSHG`（沪深 300） |

**系统自动配置参数**（用户无需提供）:

- 佣金率: `0.0003`（万三）
- 印花税: `0.001`（千一）
- 最低佣金: `5.0` 元
- 滑点: `0.0`
- 股票代码: 从策略代码的 `g.security` 中提取

#### 技术方案

**方案概述**: DAG 参数化 + 动态策略加载

**核心组件**:

1. **参数化 DAG**: 使用 Airflow 3.x `Params` API 生成 Web UI 表单
2. **策略验证器**: 解析并校验 JoinQuant 格式代码（检查 `initialize`、`handle_data` 函数）
3. **动态加载器**: 使用 `exec()` 或 `importlib` 动态执行用户策略代码
4. **安全沙箱**: 限制策略代码权限（禁止文件操作、网络访问、系统调用）
5. **结果生成器**: 标准化回测报告输出（JSON + HTML）

**DAG 参数定义示例**:

```python
from airflow.models import Param

dag = DAG(
    'universal_backtest_platform',
    params={
        "strategy_name": Param(
            default="",
            type="string",
            description="策略名称（为空时自动生成）",
        ),
        "strategy_code": Param(
            default="",
            type="string",
            description="JoinQuant 格式策略代码（必须包含 initialize 和 handle_data）",
        ),
        "start_date": Param(
            default="2020-01-01",
            type="string",
            pattern=r"^\d{4}-\d{2}-\d{2}$",
            description="回测开始日期（格式：YYYY-MM-DD）",
        ),
        "end_date": Param(
            default="2024-12-31",
            type="string",
            pattern=r"^\d{4}-\d{2}-\d{2}$",
            description="回测结束日期（格式：YYYY-MM-DD）",
        ),
        "initial_cash": Param(
            default=100000.0,
            type="number",
            description="初始资金（元）",
        ),
        "freq": Param(
            default="day",
            type="string",
            enum=["day", "week", "month"],
            description="回测频率",
        ),
        "benchmark": Param(
            default="",
            type="string",
            description="基准指数代码（可选）",
        ),
    },
)
```

**任务流程**:

```
validate_strategy → prepare_data → load_strategy → run_backtest → generate_report
```

**任务说明**:

1. **validate_strategy**: 校验策略代码格式和安全性

   - 检查 `initialize()` 和 `handle_data()` 是否存在
   - 检查 `g.security` 是否定义
   - 扫描危险操作（`os.system`, `eval`, `open`, `__import__` 等）
   - 返回提取的股票代码和策略名称

2. **prepare_data**: 根据股票代码和时间范围准备数据

   - 从 JoinQuant 获取股票数据
   - 转换为 Backtrader 格式
   - 保存为临时 CSV 文件

3. **load_strategy**: 动态加载用户策略代码

   - 使用 `exec()` 在受限命名空间中执行策略代码
   - 将 JoinQuant API 映射到 Backtrader 策略类
   - 返回可执行的策略类

4. **run_backtest**: 执行回测

   - 配置 Backtrader Cerebro 引擎
   - 设置佣金、滑点等参数
   - 运行回测并收集结果

5. **generate_report**: 生成回测报告
   - 计算性能指标（夏普比率、最大回撤、总收益、年化收益等）
   - 生成 JSON 结果文件
   - 生成 HTML 可视化报告（可选）

#### 实施计划

**Phase 1: 基础架构（1-2 天）**

- [ ] 创建新 DAG `universal_backtest_platform.py`
- [ ] 配置 Params API 参数定义
- [ ] 实现 `validate_strategy` 任务（基础版本）
- [ ] 测试 Web UI 表单渲染

**Phase 2: 策略加载器（2-3 天）**

- [ ] 实现 JoinQuant API 到 Backtrader 的映射层
  - [ ] `attribute_history()` → `self.datas[0].close`
  - [ ] `order_value()` → `self.buy()` / `self.sell()`
  - [ ] `order_target_value()` → `self.order_target_value()`
  - [ ] `get_price()` → `data.close[0]`
- [ ] 实现动态策略类生成器
- [ ] 实现安全沙箱机制（限制危险操作）
- [ ] 单元测试（使用 `strategies/MA5.py` 作为测试用例）

**Phase 3: 数据准备与回测（1-2 天）**

- [ ] 实现 `prepare_data` 任务（复用现有代码）
- [ ] 实现 `run_backtest` 任务（集成动态策略）
- [ ] 配置佣金、滑点等系统参数
- [ ] 测试完整回测流程

**Phase 4: 报告生成（1 天）**

- [ ] 实现 `generate_report` 任务
- [ ] 标准化 JSON 输出格式
- [ ] 可选：HTML 报告模板
- [ ] 可选：基准对比功能

**Phase 5: 测试与优化（1-2 天）**

- [ ] 使用 6 个示例策略全面测试
- [ ] 性能优化（并发执行、缓存等）
- [ ] 错误处理和用户提示优化
- [ ] 文档更新

#### 潜在风险与缓解

| 风险                       | 影响 | 缓解措施                                    |
| -------------------------- | ---- | ------------------------------------------- |
| 策略代码安全性漏洞         | 高   | 严格的代码扫描 + 沙箱隔离                   |
| JoinQuant API 兼容性不完整 | 中   | 优先支持核心 API，逐步扩展                  |
| 动态代码执行性能开销       | 中   | 策略预编译 + 缓存机制                       |
| 用户输入参数校验不足       | 中   | 使用 Params API 的 `pattern` 和 `type` 校验 |
| 数据获取失败               | 低   | 添加重试机制 + 友好错误提示                 |

#### 预期收益

1. **用户体验提升**:

   - ✅ 无需修改 DAG 代码即可测试新策略
   - ✅ 通过 Web UI 快速提交回测任务
   - ✅ 支持任意 JoinQuant 策略直接迁移

2. **平台能力增强**:

   - ✅ 从固定策略平台升级为通用回测平台
   - ✅ 支持策略库管理（保存历史策略）
   - ✅ 为后续功能奠定基础（策略优化、参数扫描等）

3. **开发效率提升**:
   - ✅ 策略迭代速度加快
   - ✅ 降低非技术用户使用门槛
   - ✅ 便于批量测试和对比

#### 参考资料

- **JoinQuant 策略格式**: `JOINQUANT_STRATEGY_FORMAT.md`
- **示例策略**: `strategies/MA5.py`, `strategies/adx_trend_strength_minute.py` 等
- **Airflow 3.x Params API**: [官方文档](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/params.html)
- **Backtrader 文档**: [官方文档](https://www.backtrader.com/docu/)
- **当前 DAG**: `dags/jq_backtrader_precision.py`

---

## 📝 Airflow 3.x 关键变更总结

### 命令变更

| Airflow 2.x            | Airflow 3.x          |
| ---------------------- | -------------------- |
| `airflow webserver`    | `airflow api-server` |
| `airflow users create` | ❌ 已移除            |

### DAG 参数变更

| Airflow 2.x           | Airflow 3.x             |
| --------------------- | ----------------------- |
| `schedule_interval=X` | `schedule=X`            |
| 支持简单 XCom 类型    | 要求复杂类型（Dict）    |
| `/api/v1/*`           | `/api/v2/*` （v1 移除） |

### 最佳实践

1. ✅ 避免顶层导入耗时模块
2. ✅ XCom 使用 Dict/List
3. ✅ DAG 导入 < 30 秒
4. ✅ 使用 print() 代替 logger

---

## 💡 经验教训

1. ✅ Airflow 3.x 不向后兼容，需注意 API 变更
2. ✅ Standalone 模式适合快速测试
3. ✅ 浏览器缓存问题可能导致登录失败
4. ✅ 自定义依赖需构建专用镜像
5. ✅ 动态任务映射使用 `.partial().expand()`
6. ⚠️ 生产环境需等待 3.x 生态成熟

---

---

## 📁 文件清单与系统架构

### 核心配置文件

| 文件名                          | 类型        | 作用                                  |
| ------------------------------- | ----------- | ------------------------------------- |
| `docker-compose-standalone.yml` | Docker 配置 | Standalone 模式容器编排（当前使用）   |
| `Dockerfile`                    | Docker 镜像 | 自定义镜像构建（airflow-quant:3.1.3） |
| `.env`                          | 环境变量    | 容器环境变量配置                      |
| `requirements.txt`              | Python 依赖 | Python 包依赖列表                     |

---

### DAG 文件详解

#### 1️⃣ `test_dag.py` - 测试 DAG

**类型**: 功能测试  
**用途**: 验证 Airflow 3.x 安装和基础功能  
**依赖**: 无（独立运行）  
**是否回测系统**: ❌ 否

**功能**:

- 打印 Airflow 版本信息
- 验证 Python Operator 和 Bash Operator
- 测试任务链式依赖

**任务流程**:

```
print_version → test_python → test_bash → finish
```

**适用场景**: 初次部署时验证 Airflow 环境正常工作

---

#### 2️⃣ `jq_backtrader_precision.py` - 固定策略回测 DAG

**类型**: 回测系统  
**用途**: 执行预定义的双均线和动量策略回测  
**依赖**: Backtrader 框架  
**是否回测系统**: ✅ 是

**核心组件**:

1. **CNStockCommission**: A 股佣金模式（万三 + 印花税千一）
2. **LotSizeSizer**: A 股手规则（100 股整数倍）
3. **BaseCNStrategy**: 策略基类（自动佣金配置）
4. **DualMovingAverageStrategy**: 双均线策略（5 日/20 日）
5. **MomentumStrategy**: 动量策略（20 日动量）

**任务流程**:

```
prepare_data → run_backtrader_strategy (双均线) ┐
                                              ├→ 结束
            → run_backtrader_strategy (动量)   ┘
```

**输入参数**:

- 股票代码: 硬编码 `000001.XSHE`
- 时间范围: 硬编码
- 策略类型: 固定的双均线、动量策略

**输出**:

- 回测结果 JSON
- 性能指标（收益率、夏普比率、最大回撤）

**限制**:

- ❌ 策略固定，不支持自定义
- ❌ 参数固定，需修改代码才能调整

---

#### 3️⃣ `universal_backtest_platform.py` - 通用策略回测平台 DAG

**类型**: 回测系统  
**用途**: 支持用户通过 Web UI 提交任意 JoinQuant 格式策略进行回测  
**依赖**: `jq_adapter.py` + `jq_strategy_loader.py`  
**是否回测系统**: ✅ 是（**核心回测系统**）

**核心功能**:

1. **动态策略接入**: 用户通过 Web UI 粘贴策略代码
2. **参数化配置**: 时间范围、初始资金、回测频率等可配置
3. **安全验证**: 策略代码安全性检查（禁止危险操作）
4. **标准化报告**: 自动生成 JSON 格式回测报告

**任务流程**:

```
validate_and_prepare → prepare_data → run_backtest → generate_report
      ↓                     ↓              ↓                ↓
   策略验证            数据准备       执行回测          生成报告
```

**任务说明**:

| 任务                   | 输入                | 处理                         | 输出          |
| ---------------------- | ------------------- | ---------------------------- | ------------- |
| `validate_and_prepare` | 策略代码 + 用户参数 | 验证代码安全性、提取股票代码 | 配置字典      |
| `prepare_data`         | 股票代码 + 时间范围 | 生成/获取历史数据            | CSV 数据路径  |
| `run_backtest`         | 策略代码 + 数据     | 动态加载策略、执行回测       | 回测结果字典  |
| `generate_report`      | 回测结果            | 计算性能指标                 | JSON 报告文件 |

**输入参数（Web UI 表单）**:

- `strategy_code` ✅ 必填: JoinQuant 格式策略代码
- `start_date` ✅ 必填: 回测开始日期（YYYY-MM-DD）
- `end_date` ✅ 必填: 回测结束日期（YYYY-MM-DD）
- `initial_cash` ✅ 必填: 初始资金（默认 100,000 元）
- `strategy_name` ⭕ 可选: 策略名称（留空自动生成）
- `freq` ✅ 必填: 回测频率（day/week/month）
- `benchmark` ⭕ 可选: 基准指数代码

**输出**:

- `/tmp/backtest_reports/report_<策略名>_<时间戳>.json`
- 包含：总收益率、年化收益、夏普比率、最大回撤、胜率等

**优势**:

- ✅ 无需修改代码即可测试新策略
- ✅ 支持 JoinQuant 策略直接迁移
- ✅ Web UI 可视化操作

---

#### 4️⃣ `jq_adapter.py` - JoinQuant API 适配器

**类型**: 工具库  
**用途**: 将 JoinQuant API 映射到 Backtrader 框架  
**依赖**: Backtrader  
**是否回测系统**: ❌ 否（支撑模块）

**核心类**:

| 类名                | 作用       | 模拟的 JQ 对象           |
| ------------------- | ---------- | ------------------------ |
| `GlobalContext`     | 全局上下文 | `g` 对象                 |
| `ContextObject`     | 策略上下文 | `context` 对象           |
| `PortfolioObject`   | 持仓信息   | `context.portfolio`      |
| `DataObject`        | 价格数据   | `data[security]`         |
| `JQStrategyAdapter` | 策略适配器 | Backtrader Strategy 子类 |

**核心函数（JoinQuant API 实现）**:

| JQ 函数                | 功能           | Backtrader 映射                   |
| ---------------------- | -------------- | --------------------------------- |
| `attribute_history()`  | 获取历史数据   | `self.datas[0].close.get(size=N)` |
| `order_value()`        | 按金额下单     | `self.buy(size=计算股数)`         |
| `order_target()`       | 调仓到目标数量 | `self.order_target_size()`        |
| `order_target_value()` | 调仓到目标金额 | `self.order_target_value()`       |
| `get_price()`          | 获取当前价格   | `data.close[0]`                   |
| `set_benchmark()`      | 设置基准       | 记录到 g 对象                     |
| `set_option()`         | 设置策略选项   | 记录到 g 对象                     |

**日志对象**:

- `log.info()`, `log.warning()`, `log.error()` → 映射到 `print()`

**绘图函数**:

- `record()` → 映射到 Backtrader Observers

**使用示例**:

```python
# JoinQuant 代码
def handle_data(context, data):
    prices = attribute_history('000001.XSHE', 5, '1d', ['close'])
    order_value('000001.XSHE', 10000)

# 在 Backtrader 中通过 JQStrategyAdapter 自动适配
```

**依赖关系**:

- 被 `universal_backtest_platform.py` 调用
- 依赖 Backtrader 框架

---

#### 5️⃣ `jq_strategy_loader.py` - 策略验证和加载器

**类型**: 工具库  
**用途**: 验证、解析和动态加载 JoinQuant 策略代码  
**依赖**: Python AST 模块  
**是否回测系统**: ❌ 否（支撑模块）

**核心功能**:

1. **代码安全验证**:

   - 扫描危险操作（`os.system`, `eval`, `open`, `subprocess` 等）
   - 检查是否包含必需函数（`initialize`, `handle_data`）
   - 提取股票代码（`g.security`）

2. **AST 语法检查**:

   - 验证代码语法正确性
   - 确保必需函数存在且签名正确

3. **动态加载**:
   - 使用 `exec()` 在受限命名空间中执行策略代码
   - 返回可调用的 `initialize()` 和 `handle_data()` 函数

**核心函数**:

| 函数                        | 输入           | 输出                                   | 作用              |
| --------------------------- | -------------- | -------------------------------------- | ----------------- |
| `validate_strategy_code()`  | 策略代码字符串 | `StrategyValidationResult`             | 验证代码安全性    |
| `extract_security()`        | 策略代码字符串 | 股票代码字符串                         | 提取 `g.security` |
| `load_strategy_functions()` | 策略代码字符串 | `(initialize, handle_data, namespace)` | 动态加载函数      |

**安全检查列表**:

- ❌ 文件操作: `open()`, `file()`
- ❌ 系统调用: `os.*`, `subprocess.*`
- ❌ 代码执行: `exec()`, `eval()`, `compile()`
- ❌ 网络访问: `socket.*`, `urllib.*`, `requests.*`
- ❌ 危险导入: `__import__()`, `importlib.*`

**验证结果**:

```python
@dataclass
class StrategyValidationResult:
    is_valid: bool          # 是否通过验证
    security: str           # 提取的股票代码
    strategy_name: str      # 策略名称
    errors: list            # 错误列表
    warnings: list          # 警告列表
```

**使用示例**:

```python
# 验证策略代码
result = validate_strategy_code(user_code, "MA5")

if result.is_valid:
    # 加载策略函数
    init_func, handle_func, ns = load_strategy_functions(user_code)
    # 传递给 JQStrategyAdapter
```

**依赖关系**:

- 被 `universal_backtest_platform.py` 调用
- 独立模块，无外部依赖

---

#### 6️⃣ `starquant_factor_pipeline.py` - 因子管道 DAG（已禁用）

**类型**: 因子分析系统  
**用途**: QLib 因子分析管道  
**依赖**: `factor_platform/` 模块（命名冲突）  
**是否回测系统**: ❌ 否（因子系统）  
**状态**: 🚫 已禁用（重命名为 `.bak`）

**禁用原因**:

- 导入 `platform.factor_store` 与 Python 内置 `platform` 模块冲突
- 导致 DAG 处理器崩溃

**功能**（禁用前）:

- 因子计算
- 因子存储
- 因子回测

**解决方案**:

- 重命名 `platform/` 目录为 `platform_modules/` 或 `factor_platform/`
- 修复导入路径后可重新启用

---

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    Airflow 3.1.3 Standalone                  │
│                  (Docker Container)                          │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌──────────────┐
│  test_dag.py │    │ jq_backtrader_   │    │ universal_   │
│  (测试)      │    │ precision.py     │    │ backtest_    │
│              │    │ (固定策略回测)    │    │ platform.py  │
│  独立运行     │    │                  │    │ (通用回测)   │
└──────────────┘    └──────────────────┘    └──────────────┘
                            │                       │
                            │                       │
                            ▼                       ▼
                    ┌─────────────────────────────────┐
                    │      Backtrader Engine          │
                    │  - CNStockCommission (佣金)     │
                    │  - LotSizeSizer (手规则)        │
                    │  - Strategy Classes             │
                    └─────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
            ┌──────────────┐              ┌──────────────────┐
            │ jq_adapter.py│              │jq_strategy_      │
            │ (API适配层)  │              │loader.py         │
            │              │              │(代码验证/加载)   │
            │ - g 对象     │              │                  │
            │ - context    │              │ - AST 解析       │
            │ - JQ API     │              │ - 安全检查       │
            └──────────────┘              │ - 动态执行       │
                                          └──────────────────┘
```

---

### DAG 依赖关系矩阵

| DAG                              | 依赖模块                                   | 依赖 Python 包         | 数据源       |
| -------------------------------- | ------------------------------------------ | ---------------------- | ------------ |
| `test_dag.py`                    | 无                                         | `airflow`              | 无           |
| `jq_backtrader_precision.py`     | 无                                         | `backtrader`, `pandas` | 生成模拟数据 |
| `universal_backtest_platform.py` | `jq_adapter.py`<br>`jq_strategy_loader.py` | `backtrader`, `pandas` | 生成模拟数据 |
| `starquant_factor_pipeline.py`   | `factor_platform/` (冲突)                  | `qlib`, `pandas`       | QLib 数据    |

---

### 回测系统对比

| 特性            | jq_backtrader_precision | universal_backtest_platform |
| --------------- | ----------------------- | --------------------------- |
| **策略类型**    | 固定（双均线、动量）    | 动态（用户自定义）          |
| **策略输入**    | 代码中硬编码            | Web UI 表单粘贴             |
| **参数配置**    | 需修改代码              | Web UI 可视化配置           |
| **安全验证**    | 无                      | AST 解析 + 危险操作扫描     |
| **JQ API 支持** | 无                      | 完整 API 适配层             |
| **扩展性**      | 低（需修改代码）        | 高（插件式）                |
| **适用场景**    | 测试固定策略            | 生产环境通用回测            |
| **推荐使用**    | ⭕ 学习/测试            | ✅ 生产/实际使用            |

---

### 文档文件

| 文件名                         | 类型     | 作用                           |
| ------------------------------ | -------- | ------------------------------ |
| `conversation_notes.md`        | 对话记录 | 本文档，记录所有问题和解决方案 |
| `JOINQUANT_STRATEGY_FORMAT.md` | 开发文档 | JoinQuant 策略格式说明         |
| `AIRFLOW_INSTALLATION.md`      | 安装指南 | Airflow 3.x 安装步骤           |
| `CUSTOM_DAG_SETUP.md`          | 配置指南 | 自定义 DAG 配置说明            |

---

### 策略文件（`strategies/` 目录）

| 文件                           | 策略类型     | 用途           |
| ------------------------------ | ------------ | -------------- |
| `MA5.py`                       | 5 日均线策略 | 测试用例       |
| `adx_trend_strength_minute.py` | ADX 趋势强度 | 分钟级策略示例 |
| `announcement_reaction.py`     | 公告反应     | 事件驱动策略   |
| `aroon_indicator.py`           | Aroon 指标   | 技术指标策略   |
| `bollinger_breakout.py`        | 布林带突破   | 突破策略       |
| `daily_factor_rotation.py`     | 因子轮动     | 多因子策略     |

---

**文档版本**: v6.1  
**最后更新**: 2025-11-25（问题 11 最终修复：TaskFlow API 参数传递方式）  
**下次审查**: 需要时更新
