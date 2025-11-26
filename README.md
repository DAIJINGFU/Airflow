# Airflow 因子评估平台

> **基于 Airflow 3.1.3 的自动化量化因子评估系统**  
> 版本: v2.1 (生产就绪) | 发布日期: 2025-11-26

---

## 🎯 项目简介

完整的因子评估平台，支持：
- ✅ 因子注册与管理 (SQLite Registry)
- ✅ Airflow 自动化评估流水线
- ✅ 本地CSV数据源 + QLib表达式
- ✅ CLI工具集 (init/register/submit/list)
- ✅ 多维度评估指标 (IC/ICIR/收益/夏普/回撤)
- ✅ 结果聚合与报告生成

---

## 🚀 快速开始

### 1. 启动容器
```bash
docker-compose -f docker-compose-standalone.yml up -d
```

### 2. 初始化系统
```bash
# 初始化Registry数据库
docker exec -it airflow_new-airflow-standalone-1 bash -lc \
  "cd /opt/airflow && python -m factor_platform.cli init-db --seed configs/factors.json"
```

### 3. 提交评估任务
```bash
# 提交因子评估作业
docker exec -it airflow_new-airflow-standalone-1 bash -lc \
  "cd /opt/airflow && python -m factor_platform.cli submit-job alpha_mom_5 \
   --start 2020-01-01 --end 2024-12-31 --freq day --instruments 000001"
```

### 4. 触发DAG执行
```bash
# 在Airflow中触发评估流水线
docker exec -it airflow_new-airflow-standalone-1 bash -lc \
  "cd /opt/airflow && airflow dags trigger starquant_factor_pipeline"
```

### 5. 生成汇总报告
```bash
# 聚合所有成功的评估结果
docker exec -it airflow_new-airflow-standalone-1 bash -lc \
  "cd /opt/airflow && python generate_summary.py \
   --registry-db /opt/airflow/metadata/factor_platform.db \
   --output-dir /opt/airflow/.airflow_factor_pipeline"

# 复制结果到本地
docker cp airflow_new-airflow-standalone-1:/opt/airflow/.airflow_factor_pipeline/qlib_factor_summary_latest.csv ./
```

---

## 📊 评估指标

| 指标 | 说明 | 示例值 |
|------|------|--------|
| **IC** | 信息系数 | NULL (单股票) |
| **ICIR** | IC信息比率 | NULL (单股票) |
| **Rank IC** | 排序IC | NULL (单股票) |
| **Rank ICIR** | 排序ICIR | NULL (单股票) |
| **annual_return** | 年化收益率 | 0.197 (19.7%) |
| **sharpe_ratio** | 夏普比率 | 0.487 |
| **max_drawdown** | 最大回撤 | 0.874 (87.4%) |

> 注: IC/ICIR 需要多股票横截面数据才能计算

---

## 📂 项目结构

```
.
├── dags/                          # Airflow DAG定义
│   └── starquant_factor_pipeline.py  # 主评估流水线
├── factor_platform/               # 核心模块
│   ├── factor_store.py           # Registry管理
│   ├── data_adapter.py           # 数据适配
│   ├── cli.py                    # CLI工具
│   └── api_server.py             # FastAPI服务
├── configs/
│   └── factors.json              # 因子配置
├── stockdata/                     # 数据目录
│   └── 1d_1w_1m/                 # 日线数据
├── generate_summary.py            # 结果聚合脚本
├── factor_alphalens.md           # 完整技术文档 (2000+行)
├── RELEASE_v2.1.md               # 版本发布说明
└── docker-compose-standalone.yml  # Docker配置
```

---

## 📚 文档

- **完整文档**: [factor_alphalens.md](factor_alphalens.md)
- **版本说明**: [RELEASE_v2.1.md](RELEASE_v2.1.md)
- **快速参考**: factor_alphalens.md 第7节
- **问题排查**: factor_alphalens.md 第6.8节

### 关键章节速查

| 章节 | 内容 |
|------|------|
| 第5节 | Airflow前端操作指南 |
| 第6节 | DAG任务失败问题排查 (8个子节) |
| 第7节 | PowerShell/Bash命令快速参考 |
| 附录A-J | 详细设计文档 |

---

## 🔧 CLI 命令速查

```bash
# 查看所有命令帮助
python -m factor_platform.cli --help

# 初始化数据库
python -m factor_platform.cli init-db [--seed configs/factors.json]

# 注册新因子
python -m factor_platform.cli register-factor <code> "<expression>" \
  --category <category> [--name <name>]

# 提交评估任务
python -m factor_platform.cli submit-job <factor_code> \
  --start YYYY-MM-DD --end YYYY-MM-DD \
  [--freq day|week|month] [--instruments <codes>]

# 查看所有作业
python -m factor_platform.cli list-jobs
```

---

## 🐛 已知问题与解决方案

### 问题1: aggregate_results 任务未执行
**解决**: 使用独立脚本 `generate_summary.py` 绕过 Airflow 动态映射限制

### 问题2: evaluate_factor 显示失败但实际成功
**解决**: 已修复 XCom 序列化 NaN 值问题 (转换为 None)

### 问题3: PowerShell 命令续行错误
**解决**: 使用反引号 `` ` `` 而非反斜杠 `\`

详见: [factor_alphalens.md 第6.8节](factor_alphalens.md#68-常见问题排查)

---

## 🎯 验证状态

- ✅ 8个因子评估作业测试
- ✅ 7个成功，1个失败 (早期测试)
- ✅ 成功率: 87.5%
- ✅ 所有核心功能验证通过

---

## 🔄 版本历史

- **v2.1** (2025-11-26) - 生产就绪版
  - 完整功能实现
  - XCom 序列化问题修复
  - 2000+行完整文档
  - PowerShell 命令优化

---

## 📧 联系方式

- **仓库**: DAIJINGFU/Airflow
- **分支**: airflow-3.1.3-quant
- **标签**: v2.1-production

---

## 📄 许可证

MIT License

---

**最后更新**: 2025-11-26
