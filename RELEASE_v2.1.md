# 因子评估平台 v2.1 - 生产就绪版

**发布日期**: 2025-11-26  
**版本状态**: 生产就绪 (Production Ready)  
**提交哈希**: 820f76a

---

## 📦 版本概述

这是因子评估平台的第一个生产就绪版本，完整实现了基于 Airflow 的自动化因子评估流水线，支持本地CSV数据源和QLib表达式因子定义。

---

## ✨ 核心功能

### 1. 因子注册与管理系统
- ✅ **FactorStore**: SQLite Registry 数据库管理因子元数据
- ✅ **版本控制**: 支持因子多版本管理
- ✅ **状态追踪**: PENDING/RUNNING/SUCCESS/FAILED 全流程状态管理

### 2. Airflow 自动化评估流水线
- ✅ **DAG**: `starquant_factor_pipeline` 完整评估流程
- ✅ **动态任务映射**: 支持批量因子并行评估
- ✅ **容器化部署**: Airflow 3.1.3 standalone Docker 环境

### 3. 本地数据适配器
- ✅ **CSV数据源**: 支持 `stockdata/1d_1w_1m` 本地行情数据
- ✅ **QLib兼容**: 支持 QLib 表达式语法
- ✅ **多股票支持**: 可处理单股票或多股票组合

### 4. CLI 工具集
```bash
# 初始化数据库
python -m factor_platform.cli init-db --seed configs/factors.json

# 注册因子
python -m factor_platform.cli register-factor alpha_mom_5 "Ref($close, 5) / $close - 1"

# 提交评估任务
python -m factor_platform.cli submit-job alpha_mom_5 --start 2020-01-01 --end 2024-12-31

# 查看作业列表
python -m factor_platform.cli list-jobs
```

### 5. 因子评估指标
- ✅ **IC/ICIR**: 信息系数及其信息比率
- ✅ **Rank IC/ICIR**: 基于排序的IC指标
- ✅ **annual_return**: 年化收益率
- ✅ **sharpe_ratio**: 夏普比率
- ✅ **max_drawdown**: 最大回撤

### 6. 结果聚合与报告
- ✅ **generate_summary.py**: 独立聚合脚本
- ✅ **CSV导出**: 生成汇总报告 `qlib_factor_summary_latest.csv`
- ✅ **按指标排序**: 支持多维度结果对比

---

## 🔧 关键问题修复

### 问题1: Airflow 3.x 动态任务映射下游调度失败
**现象**: `aggregate_results` 和 `publish_summary` 任务虽然定义在DAG中但从未被调度执行

**根因**: Airflow 3.x 无法正确处理动态映射任务 (`.expand()`) 的输出传递给下游非映射任务

**解决方案**: 
- 创建独立的 `generate_summary.py` 脚本直接从 Registry 读取数据
- 绕过 Airflow 的任务依赖链，手动触发聚合逻辑

**文档位置**: `factor_alphalens.md` 第6节

### 问题2: XCom 序列化 NaN 值导致任务失败
**现象**: `evaluate_factor` 任务执行成功但 Airflow UI 显示失败

**根因**: 单股票数据无法计算横截面 IC，返回 `nan` 值，Airflow 3.x 的 JSON 序列化无法处理 Python 的 `float('nan')`

**解决方案**:
```python
# 将 nan 转换为 None (JSON null)
serializable_metrics = {
    k: (None if isinstance(v, (float, np.floating)) and np.isnan(v) else 
        float(v) if isinstance(v, (np.floating, np.integer)) else v)
    for k, v in metrics.items()
}
```

**文档位置**: `factor_alphalens.md` 第 6.8 节 Q7

### 问题3: PowerShell 命令行交互优化
**现象**: 用户在 PowerShell 中使用 Bash 风格的反斜杠续行符导致命令执行失败

**解决方案**: 
- 在文档中添加 PowerShell vs Bash 命令对比表
- 提供两种shell的示例命令
- 创建快速参考卡片

**文档位置**: `factor_alphalens.md` 第 7.1 节

---

## 📚 文档更新

### 完整技术文档: `factor_alphalens.md` (2000+ 行)

**主要章节 (1-7)**:
1. 项目概述
2. 系统架构设计
3. Alphalens 核心能力分析
4. 详细实施计划
5. Airflow 前端没有输入框怎么办？
6. DAG 任务失败问题 (8个子节)
7. 快速参考卡片 (4个子节)

**附录 (A-J)**:
- A. 数据库设计
- B. 数据流设计
- C. DAG 任务设计
- D. API 接口设计
- E. 核心代码模块
- F. 配置文件设计
- G. 测试方案
- H. 部署与运维
- I. 最佳实践与注意事项
- J. 完整代码示例

**新增内容**:
- ✅ PowerShell vs Bash 命令对比表
- ✅ 常见问题 FAQ (7个问题)
- ✅ 工作流程图
- ✅ 关键文件路径速查
- ✅ 已验证的成功案例

---

## 🧪 验证状态

### 测试环境
- **容器**: `airflow_new-airflow-standalone-1`
- **Airflow版本**: 3.1.3
- **Python版本**: 3.12
- **数据源**: `stockdata/1d_1w_1m/`

### 已完成测试
- ✅ 因子注册: 5个默认因子成功注册
- ✅ 任务提交: 8个评估作业
- ✅ DAG执行: 多次成功运行
- ✅ 结果聚合: CSV报告生成正常
- ✅ 指标计算: 所有指标正确计算
  - annual_return: ~0.19-0.20
  - sharpe_ratio: ~0.48-0.50
  - max_drawdown: ~0.85-0.87
  - IC/ICIR: NULL (单股票数据，符合预期)

### 作业统计
- **总作业数**: 8
- **成功**: 7
- **失败**: 1 (早期测试，已修复)
- **成功率**: 87.5%

---

## 📂 项目结构

```
airflow_new/
├── dags/
│   ├── starquant_factor_pipeline.py   # 主评估DAG
│   ├── jq_adapter.py                  # JoinQuant适配器
│   ├── jq_strategy_loader.py          # 策略加载器
│   └── universal_backtest_platform.py # 通用回测平台
├── factor_platform/
│   ├── __init__.py
│   ├── factor_store.py                # 因子存储管理
│   ├── data_adapter.py                # 数据适配器
│   ├── api_server.py                  # FastAPI服务
│   └── cli.py                         # CLI工具
├── configs/
│   └── factors.json                   # 因子配置
├── stockdata/
│   ├── 1d_1w_1m/                      # 日线数据
│   ├── 1min/                          # 分钟数据
│   └── qlib_data/                     # QLib数据
├── strategies/                        # 策略目录
├── docs/                              # 文档目录
├── generate_summary.py                # 结果聚合脚本
├── factor_alphalens.md                # 完整技术文档
├── docker-compose-standalone.yml      # Docker配置
├── requirements.txt                   # Python依赖
└── setup.py                           # 安装配置
```

---

## 🚀 快速开始

### 1. 启动容器
```powershell
docker-compose -f docker-compose-standalone.yml up -d
```

### 2. 初始化Registry
```powershell
docker exec -it airflow_new-airflow-standalone-1 bash -lc `
  "cd /opt/airflow && python -m factor_platform.cli init-db --seed configs/factors.json"
```

### 3. 提交评估任务
```powershell
docker exec -it airflow_new-airflow-standalone-1 bash -lc `
  "cd /opt/airflow && python -m factor_platform.cli submit-job alpha_mom_5 `
   --start 2020-01-01 --end 2024-12-31 --freq day --instruments 000001"
```

### 4. 触发DAG
```powershell
docker exec -it airflow_new-airflow-standalone-1 bash -lc `
  "cd /opt/airflow && airflow dags trigger starquant_factor_pipeline"
```

### 5. 生成汇总报告
```powershell
docker exec -it airflow_new-airflow-standalone-1 bash -lc `
  "cd /opt/airflow && python generate_summary.py `
   --registry-db /opt/airflow/metadata/factor_platform.db `
   --output-dir /opt/airflow/.airflow_factor_pipeline"
```

### 6. 复制结果到本地
```powershell
docker cp airflow_new-airflow-standalone-1:/opt/airflow/.airflow_factor_pipeline/qlib_factor_summary_latest.csv ./
```

---

## 🔗 相关资源

- **完整文档**: `factor_alphalens.md`
- **快速参考**: `factor_alphalens.md` 第7节
- **问题排查**: `factor_alphalens.md` 第6.8节
- **代码示例**: `factor_alphalens.md` 附录J

---

## 📝 下一步计划

### 短期优化 (v2.2)
- [ ] 支持多股票横截面IC计算
- [ ] 添加行业中性化处理
- [ ] 实现因子组合优化
- [ ] 增加更多评估指标 (turnover, decay等)

### 中期功能 (v2.5)
- [ ] Web UI 因子管理界面
- [ ] 实时因子监控
- [ ] 因子性能归因分析
- [ ] 自动化报告生成

### 长期规划 (v3.0)
- [ ] 分布式计算支持
- [ ] 机器学习因子挖掘
- [ ] 因子组合策略回测
- [ ] 生产环境部署优化

---

## 👥 贡献者

- **主要开发**: DAIJINGFU
- **技术顾问**: GitHub Copilot (Claude Sonnet 4.5)
- **发布日期**: 2025-11-26

---

## 📄 许可证

本项目遵循 MIT 许可证。

---

## 🎉 致谢

感谢所有为这个项目做出贡献的工具和库：
- Apache Airflow 3.1.3
- QLib
- Alphalens
- Pandas / NumPy
- FastAPI
- SQLite

---

**版本标签**: `v2.1-production`  
**Git分支**: `airflow-3.1.3-quant`  
**仓库**: DAIJINGFU/Airflow
