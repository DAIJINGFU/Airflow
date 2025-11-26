# GPT-5.1 Codex 编辑记录

> **编辑者**：GPT-5.1 Codex  
> **负责内容**：starquant_factor_pipeline 因子评估 DAG 平台化

---

## 1. starquant_factor_pipeline DAG 现状

### 1.1 角色与目标

- **定位**：基于本地数据（CSV）或可选 QLib 的因子批量评估流水线，输出 IC、ICIR、Rank IC、收益归因等指标，为研究员提供快速验证结果。
- **覆盖因子类型**：动量、价值、成长、质量、技术面与 Beta 因子，并支持 QLib-like 表达式或自定义 Python 表达式。
- **数据输入**：推荐使用本地 CSV（如 `_daily_hfq.csv`）作为默认行情源，存放于 `stockdata/`；若使用 QLib `.bin` 数据，可通过环境变量 `QLIB_DATA_PATH` 指定 `/opt/airflow/stockdata/qlib_data/cn_data`（仅在需要时启用）。
- **配置入口**：`configs/factors.json` 录入因子元信息（code、名称、表达式、分类）。

```json
[
  {
    "code": "alpha_mom_5",
    "name": "5日动量",
    "expression": "Ref($close, 5) / $close - 1",
    "category": "momentum"
  }
]
```

### 1.2 evaluate_factor 故障复盘

| 问题             | 现象                                                           | 根因                                                       | 处理方案                                                                        |
| ---------------- | -------------------------------------------------------------- | ---------------------------------------------------------- | ------------------------------------------------------------------------------- |
| 股票池解析失败   | `evaluate_factor` 任务 `status=FAILED, error=获取因子标签为空` | `FACTOR_INSTRUMENTS=csi300` 只传入指数代码，未展开真实成份 | 编写 `_parse_instruments`，当 `csi***` 时使用 `D.list_instruments` 展开成份列表 |
| QLib 初始化报错  | `aggregate_results` 提示“表达式缓存异常”                       | QLib 0.9 不再支持 `expression_cache=True`                  | 如果使用 QLib，移除该参数并使用 `qlib.init(provider_uri=qlib_path)`             |
| DAG 无法自动调度 | DAG 创建后始终暂停                                             | `is_paused_upon_creation=True`                             | 设置 `@dag(..., is_paused_upon_creation=False)` 确保新实例自动运行              |

```python
qlib.init(provider_uri=qlib_path)

def _parse_instruments(instruments_input):
    """统一处理字符串/列表股票池输入"""
    if isinstance(instruments_input, str):
        if instruments_input.startswith("csi"):
            return D.list_instruments(D.instruments(instruments_input), as_list=True)
        return [instruments_input]
    return instruments_input
```

> **验证结果**：Run ID `manual__2025-11-24T17:31:58.863016+00:00` 全链路成功，`aggregate_results` 产出 CSV，`publish_summary` 给出 Top10 因子榜单，总耗时 < 20 分钟。

---

## 2. 因子评估 DAG → 通用因子评估平台

### 2.1 平台化诉求

1. **因子注册**：摆脱 `configs/factors.json` 的手工维护，支持通过 API / Web 控制台提交表述、元信息、版本说明与负责人。
2. **任务参数化**：每次评估都能指定时间区间、股票池、频率、分组规则，系统自动拆分并调度。
3. **多频率复盘**：覆盖日/周/月/分钟等频率，自动处理复权、对齐与聚合。
4. **结果服务化**：将指标落库并提供订阅式回调，方便 Notebook、可视化或告警消费。

### 2.2 总体架构

```
Factor Registry API  →  Task Planner →  Airflow DAG(s) →  Compute Workers →  Metrics Store / Callback
           ↑                 ↓
         Metadata DB      Data Service (可选 QLib/特征缓存 或 CSV 适配层)
```

- **Factor Registry API**：提供 factor CRUD、版本管理与表达式校验，支持回滚。
- **Task Planner**：根据用户提交的任务生成“时间 × 股票池 × 因子”批次，并写入 Airflow 可消费的配置。
- **Data Service**：统一封装行情与特征访问，优先使用本地 CSV 缓存/适配层；如需可选 QLib 支持，可接入 QLib 数据与特征缓存。
- **Compute Workers**：容器化运行 evaluate/aggregate/publish，支持弹性扩缩与失败重试。
- **Metrics Store**：将 IC、ICIR、收益曲线、样本明细写入 TSDB + OLAP（如 Timescale + ClickHouse），对外提供 API/报表。
- **Callback & 通知**：Webhook、邮件、IM 推送运行状态与指标变化。

### 2.3 核心能力设计

| 能力              | 说明                                                  | 实现要点                                                                                              |
| ----------------- | ----------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| 因子元数据 & 权限 | 因子 code、表达式、分类、版本、责任人、依赖、审批状态 | `factor_registry` 表 + 入库校验（语法 parse、预热样本），审批通过后才能提交任务                       |
| 参数化调度        | “时间窗口 × 股票池 × 频率” 组合切片                   | Planner 将请求写入 `factor_job`，Airflow 动态生成 task group，支持多个股票池和批次                    |
| 多频率复盘        | 日 / 周 / 月 / 5min 等                                | 数据层提供频率转换与缺口填补，评估逻辑按频率调整回溯长度、分位数区间、IC 窗口                         |
| 结果落库与回调    | 指标持久化 & 通知                                     | 统一 schema（factor_code、freq、window、instrument、ic、icir、return_curve…），完成后写 Kafka/Webhook |
| 监控与治理        | 运行可观测、数据可信                                  | Airflow + Prometheus 监控耗时、重试；质量检查覆盖样本量、缺失率、IC 漂移；提供 Dashboard              |

### 2.4 里程碑（建议）

| 阶段                | 时间      | 目标                                                  |
| ------------------- | --------- | ----------------------------------------------------- |
| P0 稳定性补丁       | 第 1 周   | 固化 evaluate_factor 修复 & 自动回归任务              |
| P1 因子注册 API     | 第 2-3 周 | 上线 REST API + DB schema，提供校验与审批             |
| P2 参数化调度       | 第 4-5 周 | 实现 Planner + DAG 动态任务，支持多股票池/时间窗/批次 |
| P3 多频率与指标落库 | 第 6-7 周 | 完成多频率复盘、统一结果 schema、ClickHouse 自助查询  |
| P4 通知与可视化     | 第 8 周   | Webhook/IM 通知、仪表盘、指标订阅                     |

---

## 3. 因子评估最佳实践

### 3.1 准备阶段

- 若使用 QLib，请确认 QLib 数据目录 `/opt/airflow/stockdata/qlib_data/cn_data` 已按最新交易日同步；否则推荐使用本地 CSV（`stockdata/`）并通过 CSV 适配层验证数据可用性。
- 在因子注册 API 中填写 `code`、中文名以及因子 `expression`（支持 QLib-like 或 Python 表达式），并补充类别、负责人、股票池范围、标签等元信息。
- 提交前可在 Notebook 中用本地 CSV 或 QLib（可选）做快速取数与小规模验证，确保表达式不会产生 NaN/除零或异常值。

### 3.2 运行阶段

- 评估任务按“因子 × 股票池 × 频率 × 时间窗口”组合提交，默认 `FACTOR_BATCH_SIZE=8`，可依据资源自动调整。
- 建议开启多进程映射、表达式 AST 缓存、行情窗口预取等优化，降低重复 IO。
- 保持幂等：所有中间结果写入 `factor_run_id` 命名空间，支持安全重跑和回滚。

### 3.3 结果解读

- 关注 IC > 0.03、ICIR > 1.0 的因子，同时查看 Rank IC、收益曲线、行业中性结果。
- 配置运行监控：任务耗时超过历史 P95、单批失败率 >5%、IC 均值骤降 >0.02 需要告警。
- 指标落库后，可通过报表/API 拉取 TopN 因子、区间表现、显著性变化，为调仓和风控提供输入。

---

> **下一步**：按照里程碑推进因子注册 API、参数化调度、多频率支持，并补齐监控与通知链路，让单一 DAG 演进为通用因子评估平台。

---

## 4. 实际落地（代码实现摘要）

- **Registry & Planner**：`platform/factor_store.py` 提供 SQLite 持久化，覆盖因子注册、版本管理、任务队列、结果回写与 webhook（best-effort）。`ensure_seed_factors` 可在首次运行时读取 `configs/factors.json` 初始化因子。
- **API Server**：`factor_platform/api_server.py` 基于 FastAPI，暴露 `/factors`、`/jobs`、`/jobs/dequeue`、`/jobs/{id}/complete` 等接口，可通过 `uvicorn factor_platform.api_server:app --reload` 启动；`FACTOR_PLATFORM_DB` 控制存储路径。
- **CLI**：`python -m factor_platform.cli register-factor ...`、`python -m factor_platform.cli submit-job ...` 等命令用于本地快速录入因子与任务，方便脚本化。
- **DAG 集成**：`dags/starquant_factor_pipeline.py` 现在从 registry 拉取任务（`fetch_factor_jobs`），每个任务可指定时间窗、股票池、频率；`evaluate_factor` 根据任务参数运行并实时回写成功/失败状态，`aggregate_results` 把汇总文件路径同步到 registry。
- **环境配置**：新增 `FACTOR_PLATFORM_DB`（registry 路径）、`FACTOR_CATALOG_PATH`（默认种子因子）。批次大小沿用 `FACTOR_BATCH_SIZE`，不同频率通过提交任务时的 `--freq` 控制。

> **使用示例**：
>
> 1. `python -m factor_platform.cli init-db --seed configs/factors.json`
> 2. `python -m factor_platform.cli register-factor alpha_turnover "Std($volume, 5)" --category liquidity`
> 3. `python -m factor_platform.cli submit-job alpha_turnover --start 2022-01-01 --end 2024-01-01 --freq day --instruments csi500`
> 4. 触发 Airflow `starquant_factor_pipeline` DAG，自动拾取并执行任务；完成后可用 `python -m factor_platform.cli list-jobs --status SUCCESS` 查看指标与汇总路径。

---

## 5. Airflow 前端没有输入框怎么办？

### 5.1 疑惑

对 Airflow 完全陌生时，Web UI 好像只有“Trigger DAG”按钮，没有地方填写因子表达式、股票池、评估区间等业务参数，似乎无法自助配置。

### 5.2 实际行为

- **Airflow 负责调度，不负责采集业务参数**：Web UI 只是触发 DAG。所有参数在触发前已通过因子注册/任务 API（或 CLI）写入 registry（SQLite），并携带状态管理。
- **用户提交流程**：研究员可在脚本、CLI 或 Web 表单中调用 `platform.cli` / FastAPI（`POST /factors`、`POST /jobs`），提交时一次性指定表达式、时间窗、股票池、频率、批处理大小。
- **DAG 运行闭环**：`fetch_factor_jobs` 从 registry 中挑选 status=PENDING 的任务，将参数传给 `evaluate_factor`；任务完成后用 `mark_job_succeeded/failed` 写回指标或错误，并触发 webhook。
- **可选界面**：若希望为非技术用户提供“所见即所得”，可以在内部 Portal 上封装表单或 Bot，背后调用现有 REST API，Airflow UI 依然保持“点一下就调度”的角色。

> **结论**：Airflow 是“执行器”，业务参数通过因子注册/任务 API（或 CLI）提前入库。用户仍可自助选择因子、数据集、评估区间，只是入口不在 Airflow Web，而在我们提供的 CLI/API/前端表单。
