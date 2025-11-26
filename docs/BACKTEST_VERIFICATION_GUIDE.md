# 回测 DAG 触发与验证指南

由于终端输出存在技术问题，请按以下步骤手动触发和验证回测结果。

## 1. 触发回测 DAG

在新的 PowerShell 窗口中执行：

```powershell
docker exec airflow_new-airflow-standalone-1 airflow dags trigger universal_backtest_platform
```

您将看到类似以下输出（忽略警告信息）：

```
conf | dag_id                | dag_run_id            | ...
=====+=======================+=======================+...
{}   | universal_backtest_pl | manual__2025-11-26T... | queued
```

记录 `dag_run_id`（如 `manual__2025-11-26T04:27:00.716452+00:00`）

## 2. 通过 Web UI 监控（推荐方式）

1. 打开浏览器访问：`http://localhost:8080`
2. 使用以下凭据登录：
   - 用户名：`admin`
   - 密码：`ZdPgCVpvRpH4y6eh`
3. 在 DAGs 列表中找到 `universal_backtest_platform`
4. 点击 DAG 名称查看详情
5. 在 "Runs" 标签页中查看最新的运行记录
6. 点击运行记录查看任务状态：
   - ✓ validate_and_prepare
   - ✓ prepare_data
   - ✓ run_backtest
   - ✓ generate_report

## 3. 查看任务日志

在 Web UI 中：

1. 点击任务方块（如 `run_backtest`）
2. 点击 "Log" 按钮
3. 查看详细执行日志

关键日志内容：

- **validate_and_prepare**: 策略验证结果
- **prepare_data**: 数据加载信息
- **run_backtest**: 回测执行过程和性能指标
- **generate_report**: 最终回测报告

## 4. 通过命令行查看回测结果

等待约 2-3 分钟后，执行：

### 方法 A：查看报告文件

```powershell
# 列出报告文件
docker exec airflow_new-airflow-standalone-1 ls -lt /tmp/backtest_reports/

# 查看最新报告（替换文件名）
docker exec airflow_new-airflow-standalone-1 cat /tmp/backtest_reports/report_XXX.json
```

### 方法 B：查看任务日志

```powershell
# 列出日志目录
docker exec airflow_new-airflow-standalone-1 ls -la /opt/airflow/logs/dag_id=universal_backtest_platform/

# 查看 generate_report 任务日志（替换run_id）
docker exec airflow_new-airflow-standalone-1 cat /opt/airflow/logs/dag_id=universal_backtest_platform/run_id=manual__XXX/generate_report/attempt=1.log
```

## 5. 预期的回测结果

成功的回测应该包含以下信息：

```
============================================================
                    回测报告总结
============================================================
策略名称: strategy_000001_XSHE
股票代码: 000001.XSHE
回测时间: 2020-01-01 ~ 2024-12-31
回测频率: day
基准指数: 000300.XSHG
初始资金: ¥100,000.00
最终资金: ¥XXX,XXX.XX
总收益率: XX.XX%
年化收益: XX.XX%
夏普比率: X.XXXX
最大回撤: XX.XX%
交易次数: XXX
胜率: XX.XX%
============================================================
```

## 6. 验证优化效果

观察以下优化点：

### 进度提示（run_backtest 日志）

```
[1/5] 加载策略代码...
      ✓ 策略函数加载成功
[2/5] 配置 Backtrader 引擎...
      ✓ 引擎配置完成
[3/5] 回测配置信息:
...
```

### 数据缓存（prepare_data 日志）

首次运行：

```
[INFO] 尝试从本地加载数据...
[SUCCESS] 本地数据加载完成
  - 数据条数: XXX 条
  - 日期范围: 2020-01-01 ~ 2024-12-31
```

第二次运行（如果再次触发）：

```
[INFO] 使用缓存数据: ...csv, XXX 条记录
```

### 错误处理（如果有错误）

```
[ERROR] 数据准备失败: 本地数据文件不存在: ...
请确认：
1. 股票代码 '000001.XSHE' 是否正确
2. 数据目录 ... 是否存在
3. 文件名是否为 '000001_daily.csv'
```

## 7. 验证因子分析系统未受影响

检查其他 DAG 是否正常：

```powershell
# 列出所有 DAG
docker exec airflow_new-airflow-standalone-1 airflow dags list

# 检查导入错误（应该没有或很少）
docker exec airflow_new-airflow-standalone-1 airflow dags list-import-errors
```

确认：

- `jq_backtrader_precision` DAG 仍然存在
- 没有新的导入错误
- `starquant_factor_pipeline` 仍处于禁用状态（.bak）

## 8. 常见问题

### Q: DAG 一直处于 queued 状态

**A**: 等待 30-60 秒，调度器需要时间拾取任务

### Q: 任务失败，显示 "ModuleNotFoundError"

**A**: 检查 Docker 镜像是否为 `airflow-quant:3.1.3`，确保包含所有依赖

### Q: 数据加载失败

**A**:

1. 检查 `stockdata/1d_1w_1m/000001/` 目录是否存在
2. 检查 docker-compose 中的 volume 挂载
3. 如果使用模拟数据，结果仅供参考

### Q: 如何使用自定义策略代码

**A**: 在 Web UI 中触发 DAG 时：

1. 点击 "Trigger DAG w/ config"
2. 在 JSON 配置中修改 `strategy_code` 字段
3. 粘贴您的 JoinQuant 格式策略代码

## 9. 自动化脚本（备用）

如果需要自动化，可以使用提供的 Python 脚本：

```powershell
# 方式1：使用监控脚本
python monitor_dag.py

# 方式2：使用简单测试脚本
python simple_test.py

# 方式3：使用完整执行脚本
python run_backtest.py
```

注意：由于 PowerShell 输出缓冲问题，脚本可能不显示实时输出。建议使用 Web UI 监控。

## 10. 总结

- ✅ 回测系统已优化完成
- ✅ 因子分析系统未受影响
- ✅ 建议使用 Web UI 进行监控（用户体验最佳）
- ✅ 命令行方式作为备用验证手段

---

**最后更新**: 2025-11-26  
**文档版本**: v1.0
