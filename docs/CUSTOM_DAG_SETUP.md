# 🎯 自定义量化 DAG 配置完成总结

## ✅ 已完成的配置

### 1. 数据目录挂载

- **本地路径**: `D:\JoinQuant\VScode\starquant4-factor\stockdata`
- **容器路径**: `/opt/airflow/stockdata`
- **数据类型**:
  - CSV 格式日线数据: `stockdata/1d_1w_1m/`
  - CSV 格式日线数据: `stockdata/1d_1w_1m/`
  - 可选：QLib 二进制数据: `qlib_data/cn_data/`

### 2. 配置文件创建

- ✅ `configs/factors.json` - 因子定义配置
- ✅ `requirements.txt` - Python 依赖包列表
- ✅ `Dockerfile` - 自定义镜像构建文件
- ✅ `install_dependencies.ps1` - 依赖安装脚本

### 3. DAG 文件分析

- ✅ `jq_backtrader_precision.py` - Backtrader 回测系统
- ✅ `starquant_factor_pipeline.py` - 因子分析管道（支持本地 CSV / 可选 QLib）

### 4. 文档更新

- ✅ `conversation_notes.md` - 新增"问题 5:配置自定义量化 DAG 数据源"章节
- ✅ 详细记录两个 DAG 的功能、数据需求和配置方法

---

## 📊 DAG 功能对比

| 特性         | jq_backtrader_precision                                                 | starquant_factor_pipeline                                     |
| ------------ | ----------------------------------------------------------------------- | ------------------------------------------------------------- |
| **主要功能** | 策略回测                                                                | 因子分析                                                      |
| **框架**     | Backtrader                                                              | 本地 CSV (默认) / QLib (可选)                                 |
| **数据源**   | CSV (前复权日线，默认)                                                  | CSV (默认) 或 可选 QLib 二进制                                |
| **数据路径** | `/opt/airflow/stockdata/stockdata/1d_1w_1m/000001/000001_daily_qfq.csv` | `/opt/airflow/stockdata/qlib_data/cn_data` (仅在使用 QLib 时) |
| **核心依赖** | backtrader, pandas, loguru                                              | numpy, pandas (pyqlib 可选，若使用 QLib 则需安装)             |
| **A 股规则** | ✅ 佣金/印花税/手数限制                                                 | ❌ 纯因子分析                                                 |
| **输出指标** | 夏普比率、最大回撤、总收益                                              | IC、ICIR、Rank IC、年化收益                                   |
| **策略支持** | 双均线、动量等                                                          | N/A                                                           |
| **并行计算** | ✅ 多策略并行                                                           | ✅ 多因子并行                                                 |

---

## 🔧 依赖安装方法

### 方法 1: 使用 Dockerfile 构建镜像（推荐）⭐

**步骤**:

```powershell
# 1. 停止当前容器
docker compose -f docker-compose-standalone.yml down

# 2. 构建新镜像
docker build -t airflow-quant:3.1.3 .

# 3. 更新 docker-compose-standalone.yml
#    将 image: apache/airflow:3.1.3
#    改为 image: airflow-quant:3.1.3

# 4. 启动新容器
docker compose -f docker-compose-standalone.yml up -d

# 5. 获取新密码
docker logs airflow_new-airflow-standalone-1 2>&1 | Select-String "Password for user"
```

**优点**:

- ✅ 依赖永久安装在镜像中
- ✅ 容器重启不会丢失依赖
- ✅ 适合生产环境

### 方法 2: 手动安装（快速测试）

**注意**: 此方法在容器重建后会丢失依赖

```powershell
# 进入容器
docker exec -it airflow_new-airflow-standalone-1 bash

# 在容器内执行（pyqlib 为可选，仅在你使用 QLib 时安装）
python -m pip install --user backtrader pandas numpy loguru
# 若需要使用 QLib，请另外安装：
python -m pip install --user pyqlib

# 或使用 requirements.txt
python -m pip install --user -r /opt/airflow/requirements.txt

# 退出容器
exit

# 重启 Airflow（在宿主机）
docker compose -f docker-compose-standalone.yml restart
```

---

## 🧪 验证步骤

### 1. 检查数据挂载

```powershell
docker exec airflow_new-airflow-standalone-1 ls -la /opt/airflow/stockdata

# 应该看到：
# qlib_data
# qlib_generated
# stockdata
# tmp_clean
```

### 2. 检查 DAG 加载状态

```powershell
# 登录并获取 token
$body = @{username='admin'; password='KWNvFq7e4eY5raW6'} | ConvertTo-Json
$response = Invoke-RestMethod -Uri 'http://localhost:8080/auth/token' -Method POST -Body $body -ContentType 'application/json'
$headers = @{Authorization = "Bearer $($response.access_token)"}

# 查看所有 DAG
$dags = Invoke-RestMethod -Uri 'http://localhost:8080/api/v2/dags' -Headers $headers
$dags.dags | Select-Object dag_id, is_paused | Format-Table

# 检查导入错误
$errors = Invoke-RestMethod -Uri 'http://localhost:8080/api/v2/importErrors' -Headers $headers
if ($errors.import_errors) {
    $errors.import_errors | Format-List
} else {
    Write-Host "✅ 无导入错误"
}
```

### 3. 检查依赖安装

```powershell
docker exec airflow_new-airflow-standalone-1 python -c "import backtrader; print(f'backtrader {backtrader.__version__}')"
docker exec airflow_new-airflow-standalone-1 python -c "import pandas; print(f'pandas {pandas.__version__}')"
docker exec airflow_new-airflow-standalone-1 python -c "import numpy; print(f'numpy {numpy.__version__}')"
docker exec airflow_new-airflow-standalone-1 python -c "import loguru; print('loguru installed')"
# 如果你使用 QLib，请单独检查：
docker exec airflow_new-airflow-standalone-1 python -c "import importlib,sys
try:
  q=importlib.import_module('qlib'); print('qlib', q.__version__)
except Exception as e:
  print('qlib not installed or import failed:', e); sys.exit(0)"
```

---

## 📝 下一步操作

### 立即执行

1. **选择依赖安装方法**: 推荐使用 Dockerfile 方法
2. **重建容器**: 应用新的镜像配置
3. **验证 DAG 加载**: 确保两个 DAG 都无导入错误

### 测试 DAG

1. **启用 DAG**: 在 Web UI 中取消暂停
2. **手动触发**:
   - `jq_backtrader_precision` - 测试回测功能
   - `starquant_factor_pipeline` - 测试因子计算
3. **查看日志**: 确认数据读取和计算正常

### 可选优化

1. **性能调优**: 调整 `FACTOR_BATCH_SIZE` 控制并行度
2. **日期范围**: 通过环境变量设置 `FACTOR_START_DATE` 和 `FACTOR_END_DATE`
3. **股票池**: 修改 `FACTOR_INSTRUMENTS` (如 csi300, csi500)
4. **策略扩展**: 在 `jq_backtrader_precision.py` 中添加新策略

---

## 🎯 当前系统状态

| 组件         | 状态        | 备注                           |
| ------------ | ----------- | ------------------------------ |
| Docker 容器  | ✅ 运行中   | Standalone 模式                |
| 数据挂载     | ✅ 成功     | stockdata 目录已映射           |
| Configs 目录 | ✅ 创建     | factors.json 已配置            |
| DAG 文件     | ✅ 存在     | 3 个 DAG (1 个测试 + 2 个量化) |
| DAG 加载     | ⚠️ 部分错误 | 需安装依赖                     |
| 依赖安装     | ⏳ 待执行   | 参考上述安装方法               |
| 文档更新     | ✅ 完成     | conversation_notes.md 已更新   |

**当前密码**: `KWNvFq7e4eY5raW6`  
**访问地址**: http://localhost:8080

---

## 💡 关键要点

1. ✅ **数据已准备**: 本地 stockdata 目录包含完整的股票数据
2. ✅ **DAG 已配置**: 两个量化 DAG 适配 Airflow 3.x 语法
3. ⚠️ **依赖待安装**: backtrader 和 pyqlib 需要手动安装
4. 🎯 **生产建议**: 使用 Dockerfile 方法确保依赖持久化
5. 📊 **功能互补**: 回测系统 + 因子分析形成完整量化研究流程

---

**配置完成！** 🎉  
按照上述步骤安装依赖后，两个量化 DAG 即可正常运行！
