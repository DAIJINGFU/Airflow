# 基于 Alphalens 的因子分析系统实现计划

> **项目名称**：Airflow + Alphalens 通用因子分析平台  
> **最后更新**：2025-11-26  
> **状态**：已实现核心功能 ✓  
> **版本**：v2.1 - 生产就绪版

---

## 📋 目录

- [1. 项目概述](#1-项目概述)
  - [1.1 项目背景与目标](#11-项目背景与目标)
  - [1.2 核心价值](#12-核心价值)
  - [1.3 与现有系统的关系](#13-与现有系统的关系)
  - [1.4 项目范围与边界](#14-项目范围与边界)
- [2. 系统架构设计](#2-系统架构设计)
  - [2.1 整体架构图](#21-整体架构图)
  - [2.2 核心组件说明](#22-核心组件说明)
  - [2.3 技术栈选型](#23-技术栈选型)
  - [2.4 部署架构](#24-部署架构)
- [3. Alphalens 核心能力分析](#3-alphalens-核心能力分析)
  - [3.1 数据输入格式要求](#31-数据输入格式要求)
  - [3.2 核心分析功能](#32-核心分析功能)
  - [3.3 输出指标详解](#33-输出指标详解)
  - [3.4 可视化图表清单](#34-可视化图表清单)
- [4. 详细实施计划](#4-详细实施计划)
  - [4.1 阶段一：环境搭建与验证](#41-阶段一环境搭建与验证)
  - [4.2 阶段二：因子注册系统](#42-阶段二因子注册系统)
  - [4.3 阶段三：数据适配层](#43-阶段三数据适配层)
  - [4.4 阶段四：Alphalens 分析引擎](#44-阶段四alphalens-分析引擎)
  - [4.5 阶段五：Airflow DAG 开发](#45-阶段五airflow-dag-开发)
  - [4.6 阶段六：API 接口开发](#46-阶段六api-接口开发)
  - [4.7 阶段七：结果存储与可视化](#47-阶段七结果存储与可视化)
  - [4.8 阶段八：测试与优化](#48-阶段八测试与优化)
- [5. Airflow 前端没有输入框怎么办？](#5-airflow-前端没有输入框怎么办)
  - [5.1 疑惑](#51-疑惑)
  - [5.2 实际行为](#52-实际行为)
- [6. DAG 任务失败问题：aggregate_results 和 publish_summary 未执行](#6-dag-任务失败问题aggregate_results-和-publish_summary-未执行)
  - [6.1 问题现象](#61-问题现象)
  - [6.2 根本原因](#62-根本原因)
  - [6.3 解决方案](#63-解决方案)
  - [6.4 当前工作流程](#64-当前工作流程)
  - [6.5 预期输出](#65-预期输出)
  - [6.6 注意事项](#66-注意事项)
  - [6.7 已验证的成功案例](#67-已验证的成功案例)
  - [6.8 常见问题排查](#68-常见问题排查)
- [7. 快速参考卡片](#7-快速参考卡片)
  - [7.1 PowerShell vs Bash 命令对比](#71-powershell-vs-bash-命令对比)
  - [7.2 常用命令速查](#72-常用命令速查)
  - [7.3 工作流程图](#73-工作流程图)
  - [7.4 关键文件路径](#74-关键文件路径)
- [附录 A. 数据库设计](#附录a-数据库设计)
  - [A.1 因子元数据表](#a1-因子元数据表)
  - [A.2 评估任务表](#a2-评估任务表)
  - [A.3 评估结果表](#a3-评估结果表)
  - [A.4 因子版本历史表](#a4-因子版本历史表)
- [附录 B. 数据流设计](#附录b-数据流设计)
  - [B.1 因子数据准备流程](#b1-因子数据准备流程)
  - [B.2 价格数据处理流程](#b2-价格数据处理流程)
  - [B.3 Alphalens 数据转换流程](#b3-alphalens-数据转换流程)
- [附录 C. DAG 任务设计](#附录c-dag-任务设计)
  - [C.2 因子评估 DAG → 通用因子评估平台](#c2-因子评估-dag--通用因子评估平台)
  - [C.3 因子评估最佳实践](#c3-因子评估最佳实践)
  - [C.4 实际落地（代码实现摘要）](#c4-实际落地代码实现摘要)
- [附录 D. API 接口设计](#附录d-api-接口设计)
  - [D.1 因子管理接口](#d1-因子管理接口)
  - [D.2 任务管理接口](#d2-任务管理接口)
  - [D.3 结果查询接口](#d3-结果查询接口)
- [附录 E. 核心代码模块](#附录e-核心代码模块)
  - [E.1 因子注册与管理（factor_store.py）](#e1-因子注册与管理factor_storepy)
  - [E.2 数据适配与清洗（data_adapter.py）](#e2-数据适配与清洗data_adapterpy)
  - [E.3 分析引擎（alphalens_engine.py）](#e3-分析引擎alphalens_enginepy)
  - [E.4 结果处理与持久化（result_processor.py）](#e4-结果处理与持久化result_processorpy)
  - [E.5 API 服务（api_server.py）](#e5-api-服务api_serverpy)
  - [E.6 CLI 工具（cli.py）](#e6-cli-工具clipy)
- [附录 F. 配置文件设计](#附录f-配置文件设计)
  - [F.1 因子配置](#f1-因子配置)
  - [F.2 系统配置](#f2-系统配置)
- [附录 G. 测试方案](#附录g-测试方案)
  - [G.1 单元测试](#g1-单元测试)
  - [G.2 集成测试](#g2-集成测试)
  - [G.3 端到端测试](#g3-端到端测试)
- [附录 H. 部署与运维](#附录h-部署与运维)
  - [H.1 容器化部署](#h1-容器化部署)
  - [H.2 监控与告警](#h2-监控与告警)
  - [H.3 日志与排障](#h3-日志与排障)
- [附录 I. 最佳实践与注意事项](#附录i-最佳实践与注意事项)
- [附录 J. 完整代码示例](#附录j-完整代码示例)
  - [J.1 因子注册 CLI 示例](#j1-因子注册-cli-示例)
  - [J.2 API 调用示例（FastAPI）](#j2-api-调用示例fastapi)
  - [J.3 DAG 任务开发片段](#j3-dag-任务开发片段)

## 1. 项目概述

### 1.1 项目背景与目标

#### 1.1.1 项目背景

在量化投资领域，因子分析是选股策略开发的核心环节。Alphalens 是由 Quantopian 开源的专业因子分析工具，已成为业界标准。本项目旨在：

1. **集成 Alphalens**：将 Alphalens 的专业分析能力集成到现有 Airflow 平台
2. **自动化评估**：实现因子的批量评估、对比和排序
3. **标准化流程**：建立从因子注册到结果可视化的完整流程
4. **生产级部署**：确保系统稳定性、可扩展性和可维护性

#### 1.1.2 核心目标

构建一个**生产级的因子分析平台**，提供以下核心能力：

| 序号 | 功能模块       | 核心能力                                        | 预期产出                           |
| ---- | -------------- | ----------------------------------------------- | ---------------------------------- |
| 1    | **IC 分析**    | 信息系数（IC）、秩相关系数（Rank IC）的时序分析 | IC 均值、IC 标准差、IC IR、IC 胜率 |
| 2    | **收益分析**   | 分层回测、多空组合、超额收益归因                | 分层收益曲线、多空收益、夏普比率   |
| 3    | **换手率分析** | 持仓稳定性、交易成本估算                        | 平均换手率、自相关系数             |
| 4    | **风险分析**   | 行业中性化、市值中性化、Beta 中性化             | 中性化后的收益和 IC                |
| 5    | **事件分析**   | 因子在特定事件前后的表现                        | 事件窗口收益分布                   |
| 6    | **可视化**     | Alphalens 内置的 20+ 专业图表                   | IC 时序图、累计收益图、分层热力图  |
| 7    | **批量评估**   | 多因子并行评估、自动对比、生成排行榜            | 因子排行榜、综合评分               |
| 8    | **任务调度**   | 通过 Airflow 实现定时评估、依赖管理             | 调度日志、执行报告                 |

#### 1.1.3 应用场景

1. **因子研发**：快速验证新因子的有效性
2. **因子筛选**：从大量候选因子中筛选优质因子
3. **因子监控**：定期评估现有因子的表现变化
4. **组合优化**：分析因子间的相关性和互补性

### 1.2 核心价值

| 功能模块         | 核心价值                                         | 实现方式                     |
| ---------------- | ------------------------------------------------ | ---------------------------- |
| **因子注册管理** | 统一管理因子库，支持版本控制、权限管理、审批流程 | SQLite 数据库 + RESTful API  |
| **自动化评估**   | 一键触发批量评估，自动生成 20+ 项专业指标        | Airflow DAG + Alphalens 引擎 |
| **专业可视化**   | Alphalens 原生图表，符合量化研究员习惯           | Matplotlib + Seaborn         |
| **结果持久化**   | 所有指标、图表、原始数据自动归档，支持历史对比   | Parquet + JSON + 图片文件    |
| **任务编排**     | 支持定时评估、依赖管理、失败重试                 | Airflow TaskFlow API         |
| **扩展性**       | 支持自定义因子表达式、股票池、评估周期           | 插件化设计                   |
| **生产环境就绪** | 容器化部署、监控告警、数据质量检查               | Docker + Prometheus          |

### 1.3 与现有系统的关系

#### 1.3.1 系统定位

```
┌─────────────────────────────────────────────────────────────────┐
│                Airflow 3.1.3 量化分析平台                        │
└─────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│ 策略回测平台     │   │ 精度验证平台     │   │ 因子分析平台     │
│ universal_      │   │ jq_backtrader_  │   │ alphalens_      │
│ backtest        │   │ precision       │   │ factor_analysis │
│                 │   │                 │   │ (本项目)         │
├─────────────────┤   ├─────────────────┤   ├─────────────────┤
│ 输入: 完整策略   │   │ 输入: 固定策略   │   │ 输入: 单因子     │
│ 输出: 收益曲线   │   │ 输出: 精度报告   │   │ 输出: IC/收益    │
│ 用途: 策略验证   │   │ 用途: 数据校验   │   │ 用途: 因子评估   │
└─────────────────┘   └─────────────────┘   └─────────────────┘
        │                       │                       │
        └───────────────────────┴───────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │      共享数据层        │
                    ├───────────────────────┤
                    │ • JoinQuant 本地数据  │
                    │ • QLib 因子库（可选）  │
                    │ • CSV/Parquet 文件    │
                    │ • 行业分类数据        │
                    │ • 基准指数数据        │
                    └───────────────────────┘
```

#### 1.3.2 定位差异

| 对比维度     | 策略回测平台               | 因子分析平台（本项目）      |
| ------------ | -------------------------- | --------------------------- |
| **分析对象** | 完整交易策略               | 单一因子                    |
| **输入数据** | 策略代码 + 参数配置        | 因子值 + 价格数据           |
| **核心指标** | 总收益、夏普比率、最大回撤 | IC、IR、分层收益、换手率    |
| **时间粒度** | 分钟/日/周                 | 主要是日频（可扩展）        |
| **输出形式** | 收益曲线、持仓明细         | IC 时序、分层表现、统计图表 |
| **应用场景** | 策略验证与优化             | 因子挖掘与筛选              |
| **调用方式** | Airflow DAG 触发           | API + Airflow DAG           |

### 1.4 项目范围与边界

#### 1.4.1 包含范围

✅ **数据处理**

- 支持 JoinQuant 本地数据、CSV（默认）、QLib（可选）
- 自动处理复权、缺失值、异常值
- 支持多股票池（沪深 300、中证 500、全市场）

✅ **因子管理**

-- 因子注册、版本控制、审批流程
-- 支持 QLib-like 表达式或自定义 Python 函数

- 因子分类、标签管理

✅ **分析功能**

- IC 分析（IC、Rank IC、IC IR）
- 收益分析（分层、多空、累计收益）
- 换手率分析
- 风险中性化分析

✅ **任务调度**

- 单因子评估、批量评估
- 定时任务、手动触发
- 失败重试、依赖管理

✅ **结果管理**

- 结果持久化（数据库 + 文件）
- 历史结果查询、对比
- 可视化图表导出

#### 1.4.2 不包含范围

❌ **不包含以下功能**：

- 因子挖掘（机器学习自动生成因子）
- 实时交易（本系统仅做离线分析）
- 组合优化（因子权重优化）
- 风险模型构建（需要独立的风险系统）
- 回测执行（应使用策略回测平台）

---

## 2. 系统架构设计

### 2.1 整体架构图

```
┌────────────────────────────────────────────────────────────────────────┐
│                           用户交互层                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │ Airflow Web │  │ REST API    │  │ CLI 工具    │  │ Jupyter     │   │
│  │ (DAG触发)   │  │ (因子管理)  │  │ (批量提交)  │  │ Notebook    │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          服务编排层 (Airflow)                           │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │              DAG: alphalens_factor_analysis                      │  │
│  │                                                                  │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐│  │
│  │  │ validate_  │→ │ prepare_   │→ │ compute_   │→ │ store_     ││  │
│  │  │ factor     │  │ data       │  │ alphalens  │  │ results    ││  │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘│  │
│  │        ↓               ↓                ↓               ↓       │  │
│  │  [因子校验]      [数据准备]       [分析计算]      [结果存储]    │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          业务逻辑层                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐    │
│  │ 因子注册管理      │  │ 数据适配器        │  │ Alphalens 引擎    │    │
│  │ FactorRegistry   │  │ DataAdapter      │  │ AlphalensEngine  │    │
│  │                  │  │                  │  │                  │    │
│  │ • 因子CRUD       │  │ • 格式转换       │  │ • IC 分析        │    │
│  │ • 版本管理       │  │ • 数据清洗       │  │ • 收益分析       │    │
│  │ • 审批流程       │  │ • 缺失值处理     │  │ • 换手率分析     │    │
│  │ • 权限控制       │  │ • 异常值检测     │  │ • 风险分析       │    │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘    │
│                                                                        │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐    │
│  │ 结果处理器        │  │ 任务管理器        │  │ 质量检查器        │    │
│  │ ResultProcessor  │  │ JobManager       │  │ QualityChecker   │    │
│  │                  │  │                  │  │                  │    │
│  │ • 指标计算       │  │ • 任务队列       │  │ • 数据质量       │    │
│  │ • 图表生成       │  │ • 状态管理       │  │ • 结果验证       │    │
│  │ • 报告生成       │  │ • 并发控制       │  │ • 异常告警       │    │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘    │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          数据存储层                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │
│  │ 元数据库     │  │ 价格数据     │  │ 因子数据     │  │ 结果存储 │  │
│  │ (SQLite)     │  │ (Parquet)    │  │ (Parquet)    │  │ (混合)   │  │
│  │              │  │              │  │              │  │          │  │
│  │ • 因子定义   │  │ • 股票行情   │  │ • 因子值     │  │ • 指标   │  │
│  │ • 任务记录   │  │ • 复权数据   │  │ • 因子排名   │  │ • 图表   │  │
│  │ • 评估结果   │  │ • 基准指数   │  │ • 时间序列   │  │ • 日志   │  │
│  │ • 版本历史   │  │ • 行业分类   │  │ • 横截面     │  │ • 报告   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

### 2.2 核心组件说明

#### 2.2.1 因子注册管理器 (FactorRegistry)

**功能职责**：

- 因子的增删改查（CRUD）
- 版本控制与历史管理
- 因子审批流程
- 权限与访问控制

**核心接口**：

```python
class FactorRegistry:
    def register_factor(self, code: str, expression: str, metadata: dict) -> int
    def get_factor(self, code: str, version: Optional[int] = None) -> Factor
    def update_factor(self, code: str, updates: dict) -> bool
    def delete_factor(self, code: str) -> bool
    def list_factors(self, filters: dict = None) -> List[Factor]
    def approve_factor(self, code: str) -> bool
    def deprecate_factor(self, code: str, reason: str) -> bool
```

**数据库表结构**：

```sql
-- 因子元数据表
CREATE TABLE factors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,              -- 因子代码 (如 'mom_5d')
    name TEXT NOT NULL,                     -- 因子名称 (如 '5日动量')
    expression TEXT NOT NULL,               -- 因子计算表达式
    category TEXT,                          -- 因子分类 (momentum/value/quality/technical)
    sub_category TEXT,                      -- 子分类
    version INTEGER DEFAULT 1,              -- 版本号
    status TEXT DEFAULT 'pending',          -- 状态 (pending/approved/active/deprecated)
    author TEXT,                            -- 作者
    approver TEXT,                          -- 审批人
    description TEXT,                       -- 描述
    tags JSON,                              -- 标签 (JSON 数组)
    dependencies JSON,                      -- 依赖的其他因子
    parameters JSON,                        -- 参数配置
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,                  -- 审批时间
    deprecated_at TIMESTAMP                 -- 废弃时间
);

-- 因子版本历史表
CREATE TABLE factor_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    factor_code TEXT NOT NULL,
    version INTEGER NOT NULL,
    expression TEXT NOT NULL,
    metadata JSON,                          -- 版本元数据
    change_description TEXT,                -- 变更说明
    created_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(factor_code, version),
    FOREIGN KEY (factor_code) REFERENCES factors(code)
);

-- 因子评估任务表
CREATE TABLE factor_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT UNIQUE NOT NULL,           -- 任务ID (UUID)
    factor_code TEXT NOT NULL,             -- 因子代码
    factor_version INTEGER,                -- 因子版本
    start_date TEXT NOT NULL,              -- 开始日期 (YYYY-MM-DD)
    end_date TEXT NOT NULL,                -- 结束日期 (YYYY-MM-DD)
    universe TEXT NOT NULL,                -- 股票池 (csi300/csi500/all)
    periods TEXT NOT NULL,                 -- 持有期 (如 '1,5,10,20')
    quantiles INTEGER DEFAULT 5,           -- 分层数量
    bins INTEGER,                          -- 固定分箱数（与quantiles二选一）
    long_short BOOLEAN DEFAULT TRUE,       -- 是否包含多空组合
    group_neutral BOOLEAN DEFAULT FALSE,   -- 是否行业中性
    status TEXT DEFAULT 'pending',         -- pending/running/success/failed/cancelled
    result_path TEXT,                      -- 结果文件路径
    metrics JSON,                          -- 核心指标汇总
    config JSON,                           -- 任务配置
    error_message TEXT,                    -- 错误信息
    retry_count INTEGER DEFAULT 0,         -- 重试次数
    priority INTEGER DEFAULT 0,            -- 优先级
    created_by TEXT,                       -- 创建人
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,                  -- 开始时间
    completed_at TIMESTAMP,                -- 完成时间
    FOREIGN KEY (factor_code) REFERENCES factors(code)
);

-- 因子评估结果表（详细指标）
CREATE TABLE factor_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    factor_code TEXT NOT NULL,
    metric_category TEXT NOT NULL,         -- 指标类别 (ic/return/turnover/risk)
    metric_name TEXT NOT NULL,             -- 指标名称
    metric_value REAL,                     -- 指标值
    period INTEGER,                        -- 持有期
    quantile INTEGER,                      -- 分层编号 (1-5)
    date TEXT,                             -- 日期 (用于时序指标)
    extra_info JSON,                       -- 额外信息
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES factor_jobs(job_id)
);

-- 创建索引
CREATE INDEX idx_factors_code ON factors(code);
CREATE INDEX idx_factors_category ON factors(category);
CREATE INDEX idx_factors_status ON factors(status);
CREATE INDEX idx_jobs_status ON factor_jobs(status);
CREATE INDEX idx_jobs_factor ON factor_jobs(factor_code);
CREATE INDEX idx_results_job ON factor_results(job_id);
CREATE INDEX idx_results_metric ON factor_results(metric_name);
```

#### 2.2.2 数据适配器 (DataAdapter)

**功能职责**：

- 将多种数据源转换为 Alphalens 标准格式
- 数据清洗与预处理
- 缺失值和异常值处理
- 数据质量检查

**核心方法**：

```python
class DataAdapter:
    def __init__(self, data_source_type: str):
        """
        data_source_type: 'joinquant', 'qlib', 'csv', 'custom'
        """
        self.source_type = data_source_type

    def load_factor_data(self, factor_code: str, start_date: str,
                        end_date: str, universe: List[str]) -> pd.DataFrame:
        """加载因子数据"""
        pass

    def load_price_data(self, symbols: List[str], start_date: str,
                       end_date: str, fields: List[str]) -> pd.DataFrame:
        """加载价格数据"""
        pass

    def prepare_alphalens_data(self, factor_df: pd.DataFrame,
                              price_df: pd.DataFrame,
                              periods: Tuple[int]) -> pd.DataFrame:
        """
        转换为 Alphalens 标准格式

        Returns:
            factor_data: MultiIndex DataFrame
                - Level 0: date (pd.Timestamp)
                - Level 1: asset (str)
                - Columns: factor_value, period_1_return, period_5_return, ...
        """
        pass

    def validate_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        """数据质量检查"""
        pass
```

**数据转换示例**：

```python
# 输入格式（用户数据）
factor_data = pd.DataFrame({
    'date': ['2024-01-01', '2024-01-02', '2024-01-01', '2024-01-02'],
    'symbol': ['000001.XSHE', '000001.XSHE', '000002.XSHE', '000002.XSHE'],
    'factor_value': [0.05, 0.06, -0.02, -0.01]
})

price_data = pd.DataFrame({
    'date': ['2024-01-01', '2024-01-02', '2024-01-01', '2024-01-02'],
    'symbol': ['000001.XSHE', '000001.XSHE', '000002.XSHE', '000002.XSHE'],
    'close': [10.5, 10.8, 15.2, 15.0]
})

# Alphalens 标准格式
# 1. 因子数据：MultiIndex Series
factor = pd.Series(
    data=[0.05, -0.02, 0.06, -0.01],
    index=pd.MultiIndex.from_tuples([
        (pd.Timestamp('2024-01-01'), '000001.XSHE'),
        (pd.Timestamp('2024-01-01'), '000002.XSHE'),
        (pd.Timestamp('2024-01-02'), '000001.XSHE'),
        (pd.Timestamp('2024-01-02'), '000002.XSHE'),
    ], names=['date', 'asset']),
    name='factor_value'
)

# 2. 价格数据：宽表 DataFrame (行=日期, 列=股票)
pricing = pd.DataFrame({
    '000001.XSHE': [10.5, 10.8],
    '000002.XSHE': [15.2, 15.0],
}, index=pd.DatetimeIndex(['2024-01-01', '2024-01-02'], name='date'))
```

#### 2.2.3 Alphalens 分析引擎 (AlphalensEngine)

**功能职责**：

- 封装 Alphalens 核心分析功能
- 提供统一的分析接口
- 支持批量分析和自定义配置

**核心方法**：

```python
class AlphalensEngine:
    def __init__(self, config: dict):
        self.config = config

    def run_full_analysis(self, factor_data: pd.DataFrame,
                         pricing: pd.DataFrame,
                         periods: Tuple[int] = (1, 5, 10),
                         quantiles: int = 5,
                         **kwargs) -> Dict[str, Any]:
        """
        运行完整分析流程

        Returns:
            {
                'ic_metrics': {...},
                'return_metrics': {...},
                'turnover_metrics': {...},
                'plots': {...},
                'factor_data': DataFrame  # 处理后的数据
            }
        """
        pass

    def compute_ic_metrics(self, factor_data: pd.DataFrame) -> Dict[str, float]:
        """计算 IC 相关指标"""
        pass

    def compute_return_metrics(self, factor_data: pd.DataFrame) -> Dict[str, Any]:
        """计算收益相关指标"""
        pass

    def compute_turnover_metrics(self, factor_data: pd.DataFrame) -> Dict[str, float]:
        """计算换手率指标"""
        pass

    def generate_tear_sheet(self, factor_data: pd.DataFrame,
                           output_dir: str) -> List[str]:
        """生成完整分析报告"""
        pass
```

### 2.3 技术栈选型

#### 2.3.1 核心依赖

| 组件类别     | 技术选型          | 版本要求 | 用途说明           |
| ------------ | ----------------- | -------- | ------------------ |
| **任务调度** | Apache Airflow    | 3.1.3+   | DAG 编排、任务调度 |
| **因子分析** | Alphalens         | 0.4.0+   | 核心分析引擎       |
| **数据处理** | Pandas            | 2.0+     | 数据操作           |
| **数值计算** | NumPy             | 1.24+    | 数值计算           |
| **统计分析** | SciPy             | 1.11+    | 统计检验           |
| **数据存储** | SQLite            | 3.35+    | 元数据存储         |
| **文件存储** | Parquet (pyarrow) | 12.0+    | 结果数据存储       |
| **可视化**   | Matplotlib        | 3.7+     | 图表生成           |
| **可视化**   | Seaborn           | 0.12+    | 高级图表           |
| **API 框架** | FastAPI           | 0.100+   | REST API           |
| **数据验证** | Pydantic          | 2.0+     | 数据校验           |

#### 2.3.2 开发环境

```bash
# requirements.txt
apache-airflow==3.1.3
alphalens-reloaded==0.4.3  # 维护版本
pandas==2.1.4
numpy==1.26.2
scipy==1.11.4
matplotlib==3.8.2
seaborn==0.13.0
pyarrow==14.0.1
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
sqlalchemy==2.0.23
python-dateutil==2.8.2
```

### 2.4 部署架构

#### 2.4.1 Docker 容器化部署

```yaml
# docker-compose.yml (扩展现有配置)
version: "3.8"

services:
  airflow-webserver:
    # ... 现有配置 ...
    environment:
      - ALPHALENS_ENABLED=true
      - FACTOR_DB_PATH=/opt/airflow/data/factors.db
      - FACTOR_RESULTS_PATH=/opt/airflow/results/factors
    volumes:
      - ./data:/opt/airflow/data
      - ./results:/opt/airflow/results

  factor-api:
    build:
      context: .
      dockerfile: Dockerfile.factor_api
    ports:
      - "8001:8000"
    environment:
      - FACTOR_DB_PATH=/data/factors.db
    volumes:
      - ./data:/data
    depends_on:
      - airflow-webserver
```

#### 2.4.2 目录结构

```
/opt/airflow/
├── dags/
│   └── alphalens_factor_analysis.py    # 主 DAG
├── plugins/
│   └── alphalens_plugin/
│       ├── __init__.py
│       ├── factor_registry.py          # 因子注册管理
│       ├── data_adapter.py             # 数据适配器
│       ├── alphalens_engine.py         # 分析引擎
│       └── result_processor.py         # 结果处理
├── factor_platform/
│   ├── __init__.py
│   ├── api_server.py                   # FastAPI 服务
│   ├── cli.py                          # CLI 工具
│   └── factor_store.py                 # 因子存储
├── data/
│   ├── factors.db                      # SQLite 数据库
│   └── cache/                          # 缓存目录
├── results/
│   └── factors/
│       ├── {job_id}/
│       │   ├── metrics.json            # 指标数据
│       │   ├── factor_data.parquet     # 原始数据
│       │   └── plots/                  # 图表文件
│       └── summary/
│           └── factor_ranking.csv      # 因子排行榜
└── configs/
    └── factors.json                    # 因子配置（种子数据）
```

---

    factor = factor_df.set_index(['date', 'symbol'])['factor_value']

    # 2. 转换价格数据为宽表
    pricing = price_df.pivot(index='date', columns='symbol', values='close')

    # 3. 合并并计算前瞻收益
    factor_data = alphalens.utils.get_clean_factor_and_forward_returns(
        factor=factor,
        prices=pricing,
        periods=periods,
        quantiles=5,
        bins=None
    )

    return factor_data

````

#### 2.2.3 Alphalens 分析引擎 (`alphalens_engine`)

**核心功能模块**：

1. **IC 分析**：

   ```python
   from alphalens.performance import factor_information_coefficient

   ic = factor_information_coefficient(factor_data)
   # 输出：每日 IC 时序、IC 均值、IC 标准差、IR (IC/std)
````

2. **分层收益分析**：

   ```python
   from alphalens.performance import mean_return_by_quantile

   quantile_returns = mean_return_by_quantile(factor_data, by_date=True)
   # 输出：每个分层的日均收益、累计收益、多空收益
   ```

3. **换手率分析**：

   ```python
   from alphalens.performance import factor_turnover

   turnover = factor_turnover(factor_data, quantile)
   # 输出：每日换手率、平均换手率
   ```

4. **完整报告生成**：

   ```python
   from alphalens.tears import create_full_tear_sheet

   create_full_tear_sheet(
       factor_data,
       long_short=True,         # 是否包含多空组合
       group_neutral=False,     # 是否行业中性
       by_group=False           # 是否分组分析
   )
   ```

### 2.3 技术栈

| 层级     | 技术选型                                     |
| -------- | -------------------------------------------- |
| 调度层   | Apache Airflow 3.1.3                         |
| 分析引擎 | Alphalens 0.4.0+                             |
| 数据处理 | Pandas 2.0+, NumPy 1.24+                     |
| 数据存储 | SQLite (元数据), Parquet (结果), JSON (指标) |
| 可视化   | Matplotlib, Seaborn (Alphalens 内置)         |
| API 层   | FastAPI 0.100+ (可选)                        |
| 容器化   | Docker + docker-compose                      |

---

## 3. Alphalens 核心能力分析

### 3.1 数据输入格式要求

#### 3.1.1 标准输入格式

**Alphalens 要求的两种输入数据**：

#### 本地 stockdata 数据源使用说明与注意事项

**数据目录结构举例**：

```
stockdata/
  1d_1w_1m/
    000001/
      000001_daily.csv
      000001_daily_hfq.csv
      ...
```

**主要文件说明**：

- `*_daily.csv`：日线原始行情，未复权
- `*_daily_hfq.csv`：日线后复权行情，建议用于因子分析
- `*_daily_qfq.csv`：日线前复权行情

**字段说明**（以 daily_hfq 为例）：
| 列名 | 说明 |
|----------|----------|
| 日期 | 交易日期 |
| 股票代码 | 股票代码 |
| 开盘 | 开盘价 |
| 收盘 | 收盘价 |
| 最高 | 最高价 |
| 最低 | 最低价 |
| 成交量 | 成交量 |
| 成交额 | 成交额 |
| 振幅 | 振幅 |
| 涨跌幅 | 涨跌幅% |
| 涨跌额 | 涨跌额 |
| 换手率 | 换手率% |

**数据加载建议**：

1. 推荐优先使用 `*_daily_hfq.csv`（后复权），避免因分红送转导致的价格跳变。
2. 读取所有股票的行情数据时，建议遍历 `1d_1w_1m` 下所有股票子目录，合并为统一 DataFrame。
3. 日期字段需转为 `datetime` 类型，股票代码建议补全 6 位并加市场后缀（如 `000001.XSHE`）。
4. 构造 Alphalens 所需的宽表（pricing）时，index 为日期，columns 为股票代码，values 为收盘价。
5. 因子值建议单独计算后与行情数据 merge，最终生成 MultiIndex Series。

**注意事项**：

- 数据文件较大时，建议分批/分股票处理，避免内存溢出。
- 若有停牌、异常值，需在数据适配层做清洗和填补。
- 股票代码如无市场后缀，需统一补全（如全部加 `.XSHE` 或 `.XSHG`）。
- 若需多频率（日/周/月），可用 `*_weekly.csv`、`*_monthly.csv` 等文件。

**示例代码片段**：

```python
import pandas as pd
import glob
import os

# 合并所有股票的后复权日线行情
data_dir = 'stockdata/1d_1w_1m'
all_files = glob.glob(os.path.join(data_dir, '*', '*_daily_hfq.csv'))
df_list = []
for file in all_files:
    df = pd.read_csv(file, dtype={'股票代码': str})
    df['股票代码'] = df['股票代码'].str.zfill(6) + '.XSHE'  # 如有沪市需判断
    df['日期'] = pd.to_datetime(df['日期'])
    df_list.append(df[['日期', '股票代码', '收盘']])
all_data = pd.concat(df_list)

# 构造 pricing 宽表
pricing = all_data.pivot(index='日期', columns='股票代码', values='收盘')
```

#### 3.1.1.2 复权（价格调整）建议与实践

简短结论：不一定“必须”，但强烈建议对价格型因子和基于收益的评估使用复权价格（后复权或前复权），并且**因子计算与前瞻收益必须使用同一价格口径**。

要点说明：

- 原因：除权、分红、配股等公司行为会引入价格跳变，若不复权会让因子（如动量、均线）和 forward returns 出现伪信号。
- qfq/hfq：国内常见 `qfq`（前复权）和 `hfq`（后复权），两者都能得到已调整的时间序列；工程上关键是“采用经过除权除息调整的价格”，并在元数据中标注口径（如 `price_adjustment: hfq`）。
- 例外场景：某些基于基本面或非价格字段的因子可使用未复权数据；若研究“除权事件预测”则需保留未复权并单独建模。

实践建议：

1. 默认使用 `*_daily_hfq.csv`（后复权）或 `*_daily_qfq.csv`（前复权）中的 `收盘` 列作为 `pricing` 构建来源。
2. 因子计算也以相同复权口径为输入，保持口径一致性。
3. 在任务元数据/配置中记录 `price_adjustment` 字段（例如 `hfq` / `qfq` / `none`），便于审计与重现。
4. 多频率场景：优先用日线复权后重采样到周/月；或直接使用对应频率的复权文件（如 `*_weekly_hfq.csv`）。
5. 处理停牌：停牌时可使用前一有效价填充或在样本筛选时剔除样本，任务中需做显式策略。

简化示例（在 Windows 环境下读取本地后复权文件并构造 pricing）：

```python
import glob, os
import pandas as pd

data_dir = r'D:\JoinQuant\VScode\airflow_new\stockdata\1d_1w_1m'
files = glob.glob(os.path.join(data_dir, '*', '*_daily_hfq.csv'))
dfs = []
for f in files:
  df = pd.read_csv(f, dtype=str)
  df['日期'] = pd.to_datetime(df['日期'])
  df['股票代码'] = df['股票代码'].str.zfill(6)
  dfs.append(df[['日期', '股票代码', '收盘']].rename(columns={'收盘':'close'}))
all_df = pd.concat(dfs, ignore_index=True)
pricing = all_df.pivot(index='日期', columns='股票代码', values='close').sort_index()
# （可选）添加市场后缀：pricing.columns = [c + '.XSHE' for c in pricing.columns]
```

把 `price_adjustment` 口径和数据清洗策略写入任务配置，能避免后来出现口径不一致导致的难以复现的问题。

```python
# 1. 因子数据：MultiIndex Series (date, asset)
factor = pd.Series(
  data=[0.05, -0.02, 0.06, -0.01],
  index=pd.MultiIndex.from_tuples([
    (pd.Timestamp('2024-01-01'), '000001.XSHE'),
    (pd.Timestamp('2024-01-01'), '000002.XSHE'),
    (pd.Timestamp('2024-01-02'), '000001.XSHE'),
    (pd.Timestamp('2024-01-02'), '000002.XSHE'),
  ], names=['date', 'asset']),
  name='factor_value'
)
factor = pd.Series(
    data=[0.05, -0.02, 0.06, -0.01],
    index=pd.MultiIndex.from_tuples([
        (pd.Timestamp('2024-01-01'), '000001.XSHE'),
        (pd.Timestamp('2024-01-01'), '000002.XSHE'),
        (pd.Timestamp('2024-01-02'), '000001.XSHE'),
        (pd.Timestamp('2024-01-02'), '000002.XSHE'),
    ], names=['date', 'asset']),
    name='factor_value'
)

# 2. 价格数据：宽表 DataFrame (行=日期, 列=股票代码)
pricing = pd.DataFrame({
    '000001.XSHE': [10.5, 10.8, 11.0],
    '000002.XSHE': [15.2, 15.0, 15.5],
}, index=pd.DatetimeIndex(['2024-01-01', '2024-01-02', '2024-01-03'], name='date'))
```

#### 3.1.2 数据转换流程

```python
import alphalens

# 步骤1：从本地或外部数据获取原始数据（推荐本地 CSV）
factor_df = pd.DataFrame({
    'date': ['2024-01-01', '2024-01-02'],
    'symbol': ['000001.XSHE', '000001.XSHE'],
    'factor_value': [0.05, 0.06]
})

# 步骤2：转换为MultiIndex Series
factor = factor_df.set_index(['date', 'symbol'])['factor_value']
factor.index = factor.index.set_levels(
    pd.to_datetime(factor.index.levels[0]), level=0
)

# 步骤3：使用get_clean_factor_and_forward_returns合并数据
factor_data = alphalens.utils.get_clean_factor_and_forward_returns(
    factor=factor,
    prices=pricing,
    periods=(1, 5, 10, 20),  # 持有期
    quantiles=5,              # 分5层
    bins=None,                # 或使用固定边界
    filter_zscore=20          # 过滤20倍标准差以外的极端值
)

# 输出格式：
#                           factor  factor_quantile  1D      5D      10D     20D
# date        asset
# 2024-01-01  000001.XSHE   0.05    5               0.029   0.15    0.20    0.35
#             000002.XSHE  -0.02    2              -0.013  -0.05   -0.02    0.01
```

### 3.2 核心分析功能

#### 3.2.1 IC 分析

**信息系数（IC）**：衡量因子值与未来收益的线性相关性

```python
from alphalens.performance import factor_information_coefficient

# 计算每日IC和Rank IC
ic_df = factor_information_coefficient(factor_data)

# 输出示例：
#             1D      5D      10D     20D
# 2024-01-01  0.042   0.058   0.051   0.045
# 2024-01-02  0.035   0.062   0.048   0.052
# Mean:       0.038   0.060   0.049   0.048

# 关键指标
ic_mean = ic_df.mean()  # IC均值
ic_std = ic_df.std()    # IC标准差
ic_ir = ic_mean / ic_std  # Information Ratio
```

**评价标准**：

| 指标    | 优秀  | 良好      | 一般      | 较差  |
| ------- | ----- | --------- | --------- | ----- |
| IC 均值 | >0.05 | 0.03-0.05 | 0.01-0.03 | <0.01 |
| IC_IR   | >2.0  | 1.0-2.0   | 0.5-1.0   | <0.5  |
| IC 胜率 | >60%  | 50%-60%   | 45%-50%   | <45%  |

#### 3.2.2 分层收益分析

```python
from alphalens.performance import mean_return_by_quantile

# 计算各分位组收益
quantile_returns = mean_return_by_quantile(
    factor_data,
    by_date=True,       # 按日期计算
    by_group=False,     # 不分行业
    demeaned=True       # 去市场平均
)

# 多空组合收益（Top组 - Bottom组）
long_short_returns = quantile_returns[5] - quantile_returns[1]

# 累计收益
cumulative_returns = (1 + quantile_returns).cumprod() - 1
```

#### 3.2.3 换手率分析

```python
from alphalens.performance import factor_turnover, factor_rank_autocorrelation

# 换手率
turnover = factor_turnover(factor_data)
avg_turnover = turnover.mean()

# 因子自相关（衡量稳定性）
autocorr = factor_rank_autocorrelation(factor_data)
```

### 3.3 输出指标详解

#### 3.3.1 IC 相关指标

| 指标    | 计算方法                      | 优秀标准 | 说明         |
| ------- | ----------------------------- | -------- | ------------ |
| IC Mean | mean(daily_IC)                | >0.03    | 平均预测能力 |
| IC Std  | std(daily_IC)                 | <0.05    | 稳定性       |
| IC IR   | IC_Mean / IC_Std              | >1.0     | 信息比率     |
| Rank IC | spearman_corr(factor, return) | >0.03    | 秩相关性     |
| IC 胜率 | count(IC>0) / count(all)      | >55%     | 正向预测比例 |

#### 3.3.2 收益相关指标

| 指标     | 说明               | 优秀标准   |
| -------- | ------------------ | ---------- |
| 年化收益 | (1+日收益)^252 - 1 | Top 组>15% |

---

## 4. 详细实施计划

### 4.1 阶段一：环境搭建与验证

- 安装依赖（见 `requirements.txt`），确保 Alphalens、Airflow、FastAPI 等可用。QLib 为可选依赖，仅在你使用 QLib `.bin` 数据时安装。
- 配置本地/容器化开发环境，初始化数据库（CLI: `init-db`）。
- 验证本地 CSV（或 QLib，如需要）数据能够转换为 Alphalens 所需格式并能跑通示例分析。

### 4.2 阶段二：因子注册系统

- 实现因子注册、版本管理、审批流（API/CLI）。
- 支持因子元信息录入、表达式校验、标签分类。
- 支持因子库初始化与增量维护（见 configs/factors.json）。

### 4.3 阶段三：数据适配层

- 实现多源数据（JoinQuant/QLib/CSV）到 Alphalens 标准格式的转换。
- 支持缺失值、异常值处理，数据质量校验。
- 支持多股票池、不同频率（天/周/月/分钟）数据。

### 4.4 阶段四：Alphalens 分析引擎

- 封装 Alphalens 核心分析能力，支持批量分析、参数化配置。
- 输出 IC、分层收益、换手率、完整 tear sheet。
- 支持多因子并行分析、自动生成因子排行榜。

### 4.5 阶段五：Airflow DAG 开发

- 设计 DAG 流程：任务拉取 → 数据准备 → 分析计算 → 结果存储 → 汇总发布。
- 支持失败重试、依赖管理、批量任务调度。
- 支持参数化触发（如指定因子、区间、股票池、频率）。

### 4.6 阶段六：API 接口开发

- 基于 FastAPI 实现因子、任务、结果的增删查改接口。
- 支持外部系统/前端/脚本自动化调用。
- 提供任务状态、指标、排行榜等查询接口。

### 4.7 阶段七：结果存储与可视化

- 结果持久化（Parquet/JSON/图片），支持历史对比。
- 自动生成可视化报告，支持下载与订阅。
- 支持因子排行榜、分层表现、IC 趋势等多维度展示。

### 4.8 阶段八：测试与优化

- 单元测试、集成测试、端到端测试全覆盖。
- 性能优化（批量、并发、缓存、IO 等）。
- 监控与告警（Prometheus、日志、任务失败率等）。

---

## 附录 A. 数据库设计

详见 2.2.1 节，建议采用 SQLite/ClickHouse 结合，支持元数据、任务、结果、版本、日志等表。

## 附录 B. 数据流设计

1. 因子注册 → 2. 任务下发 → 3. 数据适配 → 4. 分析计算 → 5. 结果存储 → 6. 汇总发布/可视化

## 附录 C. DAG 任务设计

- 任务依赖：数据准备 → 分析 → 汇总 → 发布
- 支持批量并发、失败重试、依赖管理
- 典型 DAG 节点：fetch_factor_jobs、prepare_data、evaluate_factor、aggregate_results、publish_summary

---

| 多空收益 | Top 组 - Bottom 组 | >10%/年 |
| 夏普比率 | mean/std \* sqrt(252) | >1.5 |
| 最大回撤 | max(peak-trough)/peak | <20% |
| 卡玛比率 | 年化收益/最大回撤 | >1.0 |

#### 3.3.3 换手率指标

| 指标        | 说明                       | 优秀标准 |
| ----------- | -------------------------- | -------- |
| 日均换手率  | 平均每日持仓变化           | <50%     |
| 因子自相关  | corr(factor_t, factor_t-1) | 0.6-0.9  |
| IC/换手率比 | IC_Mean / sqrt(换手率)     | >0.08    |

### 3.4 可视化图表清单

#### 3.4.1 完整报告生成

```python
from alphalens.tears import create_full_tear_sheet

create_full_tear_sheet(
    factor_data,
    long_short=True,      # 多空组合
    group_neutral=False,  # 行业中性
    by_group=False        # 分行业分析
)
```

**生成的 20+图表**：

| 类别        | 图表名称                                     | 用途                 |
| ----------- | -------------------------------------------- | -------------------- |
| **IC 分析** | IC Time Series                               | IC 随时间变化趋势    |
|             | IC Heatmap                                   | 不同持有期 IC 热力图 |
|             | Monthly IC Barplot                           | 月度 IC 均值         |
|             | IC Distribution                              | IC 分布直方图        |
| **收益**    | Cumulative Returns by Quantile               | 分层累计收益曲线     |
|             | Mean Period Wise Return By Factor Quantile   | 各持有期平均收益     |
|             | Factor-Weighted Long/Short Portfolio Returns | 因子加权组合收益     |
|             | Top Minus Bottom Quantile Mean Returns       | 多空收益             |
| **换手率**  | Average Factor Rank Autocorrelation          | 因子自相关           |
|             | Top Quantile Turnover                        | Top 组换手率         |
| **分布**    | Factor Quantile Dispersion                   | 因子分位数离散度     |
|             | Factor Distribution                          | 因子值分布           |

---

- **定位**：基于本地数据（CSV）或可选 QLib 的因子批量评估流水线，输出 IC、ICIR、Rank IC、收益归因等指标，为研究员提供快速验证结果。
- **覆盖因子类型**：动量、价值、成长、质量、技术面与 Beta 因子，并支持 QLib-like 表达式或自定义 Python 表达式。
- **数据输入**：推荐使用本地 CSV（如 `_daily_hfq.csv`）作为默认行情源；如果你有 QLib 数据，可通过环境变量 `QLIB_DATA_PATH` 指定 `.bin` 数据路径并在需要时调用 QLib。默认本仓使用 `stockdata/` 目录作为 `FACTOR_DATA_ROOT`。
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

### Airflow DAG 导入错误（UI 中显示 "Dag 导入错误"）

当你在 Airflow Web UI 中看到 "Dag 导入错误"，并在弹窗里看到类似的追踪信息：

```
ModuleNotFoundError: No module named 'factor_platform'
```

意思是 Airflow 在解析 DAG 文件（例如 `dags/starquant_factor_pipeline.py`）时，运行 DAG 的 Python 环境无法找到本仓库的 `factor_platform` 包。常见场景与解决办法：

- 临时修复（快速验证）

  - 把本地 `factor_platform` 和 `configs` 复制到容器的 `/opt/airflow`（你之前已经用过此方法）：
    ```powershell
    docker cp .\factor_platform airflow_new-airflow-standalone-1:/opt/airflow/factor_platform
    docker cp .\configs airflow_new-airflow-standalone-1:/opt/airflow/configs
    ```
  - 在容器内验证是否能 import：
    ```powershell
    docker exec -it airflow_new-airflow-standalone-1 bash -lc "python -c \"import factor_platform; print('OK:', factor_platform.__file__)\""
    ```
  - 让 Airflow 重新加载 DAG（触发解析或重启服务）：
    ```powershell
    docker exec -it airflow_new-airflow-standalone-1 bash -lc "touch /opt/airflow/dags/starquant_factor_pipeline.py"
    docker restart airflow_new-airflow-standalone-1
    ```

- 推荐修复（长期、可复现，适用于开发/生产）

  1. 在 `docker-compose-standalone.yml`（或你用来启动 Airflow 的 compose 文件）里把项目目录挂载到容器中，这样容器启动时就能一直看到包：
     ```yaml
     services:
       airflow-standalone:
         volumes:
           - ./factor_platform:/opt/airflow/factor_platform:rw
           - ./configs:/opt/airflow/configs:rw
     ```
     之后执行：
     ```powershell
     docker compose -f docker-compose-standalone.yml up -d --build
     ```
  2. 或者把项目安装到容器的 Python 环境（开发时推荐 editable install）：
     ```powershell
     docker exec -it airflow_new-airflow-standalone-1 bash -lc "cd /opt/airflow && pip install -e ."
     ```
     这样 `factor_platform` 会出现在容器的 site-packages 中，Airflow 在解析 DAG 时也能 import 到。

- 验证（完成后）
  - 在 UI 中确认 `starquant_factor_pipeline` 不再报导入错误。
  - 或在容器里用 Python 做简单 import 测试（见上文）。

把这段加入文档后，其他团队成员遇到相同错误时可以快速定位并按照“临时/推荐”方法修复。

### C.2 因子评估 DAG → 通用因子评估平台

#### C.2.1 平台化诉求

1. **因子注册**：摆脱 `configs/factors.json` 的手工维护，支持通过 API / Web 控制台提交表述、元信息、版本说明与负责人。
2. **任务参数化**：每次评估都能指定时间区间、股票池、频率、分组规则，系统自动拆分并调度。
3. **多频率复盘**：覆盖日/周/月/分钟等频率，自动处理复权、对齐与聚合。
4. **结果服务化**：将指标落库并提供订阅式回调，方便 Notebook、可视化或告警消费。

#### C.2.2 总体架构

```
Factor Registry API  →  Task Planner →  Airflow DAG(s) →  Compute Workers →  Metrics Store / Callback
                               ↑                 ↓
                         Metadata DB      Data Service (QLib/特征缓存)
```

- **Factor Registry API**：提供 factor CRUD、版本管理与表达式校验，支持回滚。
- **Task Planner**：根据用户提交的任务生成“时间 × 股票池 × 因子”批次，并写入 Airflow 可消费的配置。
- **Data Service**：统一封装 QLib 数据、Alpha 系列特征，提供缓存与频率对齐能力。
- **Compute Workers**：容器化运行 evaluate/aggregate/publish，支持弹性扩缩与失败重试。
- **Metrics Store**：将 IC、ICIR、收益曲线、样本明细写入 TSDB + OLAP（如 Timescale + ClickHouse），对外提供 API/报表。
- **Callback & 通知**：Webhook、邮件、IM 推送运行状态与指标变化。

### 2.2.1 Registry（注册中心 / 任务登记）

Registry 是平台的元数据与任务队列中心，负责保存因子定义、提交的评估任务及其状态。它的存在使得研究员可以“先提交因子/任务”，由 Airflow 等调度器按队列逐个执行并记录结果。

- 作用：存储因子元信息、任务（job）记录与运行状态；提供查询/回放与权限控制点。
- 存放位置：当前工程默认使用 SQLite 文件（示例路径：`metadata/factor_platform.db`），生产环境可替换为 MySQL/Postgres。
- 典型表结构（简化说明）：

  - `factor_registry`：因子元信息
    - `code`：唯一 id（如 `alpha_mom_5`）
    - `name`、`expression`、`category`、`owner`、`version`
  - `factor_job`：任务队列
    - `job_id`、`factor_code`、`instruments`、`start`、`end`、`freq`
    - `status`：`PENDING` / `RUNNING` / `SUCCESS` / `FAILED`
    - `submitted_at`、`started_at`、`finished_at`、`error_message`、`metrics_json`

- 工作流（简化）：

  1. 研究员通过 CLI/API `POST /factors` 注册或更新因子（写入 `factor_registry`）。
  2. 提交评估任务（`submit-job`） → 在 `factor_job` 中生成 `PENDING` 记录。
  3. Airflow DAG（如 `starquant_factor_pipeline`）在运行时查询 `factor_job`，将 `PENDING` 任务取出并执行，更新为 `RUNNING` 并记录 `started_at`。
  4. 执行完成后写回 `metrics` 并把状态设为 `SUCCESS` 或写入 `error_message` 并设为 `FAILED`。

- 常见状态含义与处理：

  - `PENDING`：等待被调度。若长期堆积，查看 Planner/权限或批量提交脚本是否异常。
  - `RUNNING`：正在执行。若长时间不变为终态，检查 Worker 日志或资源瓶颈。
  - `SUCCESS`：完成；指标已写入 `metrics`，可用于后续聚合/展示。
  - `FAILED`：执行中异常，`error_message` 保存错误详情，支持重试或人工回滚。

- 常用 CLI 示例（在本仓）:

```powershell
# 初始化元数据库并写入示例因子（只需运行一次）
python -m factor_platform.cli init-db --seed configs/factors.json

# 注册新因子
python -m factor_platform.cli register-factor alpha_mom_5 "5日动量" "Ref($close,5)/$close - 1"

# 提交任务（写入 registry.job -> PENDING）
python -m factor_platform.cli submit-job --factor alpha_mom_5 --instruments csi300 --start 2020-01-01 --end 2024-12-31

# 查看任务队列与状态
python -m factor_platform.cli list-jobs
```

- 小建议：

  - 对于快速测试，可手动提交单个 job 并在 Airflow UI 中触发 `starquant_factor_pipeline`。DAG 会取 `PENDING` 的任务执行。
  - 若希望跳过 registry 做 ad-hoc 调试，我可以帮你新增一个短命 runner（命令行执行一次性评估，不写入 registry）。

### 2.3 核心能力设计

| 能力              | 说明                                                  | 实现要点                                                                                              |
| ----------------- | ----------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| 因子元数据 & 权限 | 因子 code、表达式、分类、版本、责任人、依赖、审批状态 | `factor_registry` 表 + 入库校验（语法 parse、预热样本），审批通过后才能提交任务                       |
| 参数化调度        | “时间窗口 × 股票池 × 频率” 组合切片                   | Planner 将请求写入 `factor_job`，Airflow 动态生成 task group，支持多个股票池和批次                    |
| 多频率复盘        | 日 / 周 / 月 / 5min 等                                | 数据层提供频率转换与缺口填补，评估逻辑按频率调整回溯长度、分位数区间、IC 窗口                         |
| 结果落库与回调    | 指标持久化 & 通知                                     | 统一 schema（factor_code、freq、window、instrument、ic、icir、return_curve…），完成后写 Kafka/Webhook |

---

## 附录 D. API 接口设计

### D.1 因子管理接口

- `POST /factors`：注册新因子（code、表达式、分类、标签、描述等）
- `GET /factors`：查询因子列表，支持多条件过滤
- `GET /factors/{code}`：查询单个因子详情
- `PUT /factors/{code}`：更新因子元信息
- `DELETE /factors/{code}`：删除因子（逻辑删除）
- `POST /factors/{code}/approve`：因子审批通过

### D.2 任务管理接口

- `POST /jobs`：提交评估任务（因子、区间、股票池、频率、参数等）
- `GET /jobs`：查询任务列表，支持状态、时间、因子等过滤
- `GET /jobs/{id}`：查询任务详情与进度
- `POST /jobs/{id}/cancel`：取消任务
- `GET /jobs/{id}/result`：获取任务结果（指标、图表、原始数据路径）

### D.3 结果与订阅接口

- `GET /results`：查询历史评估结果，支持多维度筛选
- `GET /results/ranking`：获取因子排行榜（按 IC、收益等排序）
- `POST /subscribe`：订阅因子/任务结果变更（Webhook/邮件）

---

## 附录 E. 核心代码模块

### E.1 因子注册与管理（factor_store.py）

- 因子 CRUD、版本管理、审批流、标签与依赖管理
- 支持初始因子导入（from configs/factors.json）

### E.2 数据适配与清洗（data_adapter.py）

- 多源数据加载、格式转换、缺失值/异常值处理、质量校验

### E.3 分析引擎（alphalens_engine.py）

- 封装 Alphalens 分析流程，批量 IC、分层收益、换手率、报告生成

### E.4 结果处理与持久化（result_processor.py）

- 指标、图表、原始数据、排行榜等落库与导出

### E.5 API 服务（api_server.py）

- FastAPI 路由，因子/任务/结果接口，参数校验与权限控制

### E.6 CLI 工具（cli.py）

- 本地命令行因子注册、任务提交、结果查询、数据库初始化

---

## 附录 F. 配置文件设计

### F.1 因子配置（configs/factors.json）

```json
[
  {
    "code": "alpha_mom_5",
    "name": "5日动量",
    "expression": "Ref($close, 5) / $close - 1",
    "category": "momentum"
  },
  ...
]
```

### F.2 系统配置（.env / config.yaml）

- 数据库路径、结果目录、批量大小、默认股票池、API 端口、日志等级等

---

## 附录 G. 测试方案

### G.1 单元测试

- 因子表达式解析、注册、审批、查询
- 数据加载、格式转换、缺失值处理
- IC/收益/换手率等核心分析函数

### G.2 集成测试

- 因子注册 → 任务提交 → 数据适配 → 分析 → 结果落库全流程
- API 接口全覆盖，异常与边界用例

### G.3 端到端测试

- 典型因子批量评估，结果与预期对比
- 性能与并发压力测试

---

| 监控与治理 | 运行可观测、数据可信 | Airflow + Prometheus 监控耗时、重试；质量检查覆盖样本量、缺失率、IC 漂移；提供 Dashboard |

### 2.4 里程碑（建议）

| 阶段                | 时间      | 目标                                                  |
| ------------------- | --------- | ----------------------------------------------------- |
| P0 稳定性补丁       | 第 1 周   | 固化 evaluate_factor 修复 & 自动回归任务              |
| P1 因子注册 API     | 第 2-3 周 | 上线 REST API + DB schema，提供校验与审批             |
| P2 参数化调度       | 第 4-5 周 | 实现 Planner + DAG 动态任务，支持多股票池/时间窗/批次 |
| P3 多频率与指标落库 | 第 6-7 周 | 完成多频率复盘、统一结果 schema、ClickHouse 自助查询  |
| P4 通知与可视化     | 第 8 周   | Webhook/IM 通知、仪表盘、指标订阅                     |

---

### C.3 因子评估最佳实践

#### C.3.1 准备阶段

- 若使用 QLib 请确认 QLib 数据目录 `/opt/airflow/stockdata/qlib_data/cn_data` 已按最新交易日同步；否则可使用本地 CSV（`stockdata/`）作为默认数据源。
- 在因子注册 API 中填写 code、中文名、QLib 表达式、类别、负责人、股票池范围、标签（momentum/value/quality/technical）。
- 提交前在 Notebook 使用 `qlib.data.D` 做快速取数，确保表达式不会产生 NaN、除零或异常值。

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

### C.4 实际落地（代码实现摘要）

- **Registry & Planner**：`platform/factor_store.py` 提供 SQLite 持久化，覆盖因子注册、版本管理、任务队列、结果回写与 webhook（best-effort）。`ensure_seed_factors` 可在首次运行时读取 `configs/factors.json` 初始化因子。
- **API Server**：`factor_platform/api_server.py` 基于 FastAPI，暴露 `/factors`、`/jobs`、`/jobs/dequeue`、`/jobs/{id}/complete` 等接口，可通过 `uvicorn factor_platform.api_server:app --reload` 启动；`FACTOR_PLATFORM_DB` 控制存储路径。
- **CLI**：`python -m factor_platform.cli register-factor ...`、`python -m factor_platform.cli submit-job ...` 等命令用于本地快速录入因子与任务，方便脚本化。
- **DAG 集成**：`dags/starquant_factor_pipeline.py` 现在从 registry 拉取任务（`fetch_factor_jobs`），每个任务可指定时间窗、股票池、频率；`evaluate_factor` 根据任务参数运行并实时回写成功/失败状态，`aggregate_results` 把汇总文件路径同步到 registry。
- **环境配置**：新增 `FACTOR_PLATFORM_DB`（registry 路径）、`FACTOR_CATALOG_PATH`（默认种子因子）。批次大小沿用 `FACTOR_BATCH_SIZE`，不同频率通过提交任务时的 `--freq` 控制。

> **使用示例**：

---

## 附录 H. 部署与运维

### H.1 容器化部署

- 推荐使用 Docker Compose 管理 Airflow、API、数据库、结果存储等服务。
- 关键环境变量：`FACTOR_DB_PATH`、`FACTOR_RESULTS_PATH`、`FACTOR_CATALOG_PATH`。
- 支持本地开发与生产环境切换，建议持久化 data、results 目录。

### H.2 监控与告警

- 任务运行、失败、重试、性能等通过 Airflow + Prometheus 监控。
- 关键指标：任务耗时、失败率、IC 漂移、数据缺失率。
- 支持 webhook/IM/邮件等多渠道通知。

### H.3 日志与排障

- 统一日志格式，分级输出（INFO/WARN/ERROR）。
- 关键节点（注册、调度、分析、落库、通知）均有日志追踪。
- 提供常见故障排查手册与 FAQ。

---

## 附录 I. 最佳实践与注意事项

- 因子表达式建议先在 Notebook 验证，避免批量任务失败。
- 任务参数化提交，合理设置批量大小与资源分配。
- 关注因子有效性（IC、ICIR、收益、换手率等多维度），避免过拟合。
- 定期回顾因子表现，淘汰失效因子，补充新因子。
- 监控系统健康，及时处理异常与告警。

---

## 附录 J. 完整代码示例

### J.1 因子注册 CLI 示例

```bash
python -m factor_platform.cli init-db --seed configs/factors.json
python -m factor_platform.cli register-factor alpha_turnover "Std($volume, 5)" --category liquidity
python -m factor_platform.cli submit-job alpha_turnover --start 2022-01-01 --end 2024-01-01 --freq day --instruments csi500
```

### J.2 API 调用示例（FastAPI）

```python
import requests

# 注册因子
resp = requests.post('http://localhost:8000/factors', json={
  "code": "alpha_mom_5",
  "expression": "Ref($close, 5) / $close - 1",
  "category": "momentum",
  "name": "5日动量"
})

# 提交评估任务
resp = requests.post('http://localhost:8000/jobs', json={
  "factor_code": "alpha_mom_5",
  "start_date": "2023-01-01",
  "end_date": "2024-01-01",
  "universe": "csi300",
  "freq": "day"
})

# 查询任务结果
result = requests.get(f'http://localhost:8000/jobs/{{job_id}}/result').json()
```

### J.3 DAG 任务开发片段

```python
from airflow.decorators import dag, task
from factor_platform.factor_store import FactorStore

@dag(schedule_interval=None, start_date=datetime(2023, 1, 1), catchup=False)
def factor_analysis_pipeline():
  @task
  def fetch_jobs():
    return FactorStore().fetch_pending_jobs()

  @task
  def evaluate(job):
    # ...调用分析引擎，回写结果...
    pass

  jobs = fetch_jobs()
  evaluate.expand(job=jobs)

factor_analysis_pipeline()
```

---

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

---

## 6. DAG 任务失败问题：aggregate_results 和 publish_summary 未执行

### 6.1 问题现象

在 Airflow UI 中触发 `starquant_factor_pipeline` DAG 后,观察到以下现象:

- ✅ `bootstrap_environment` - 成功
- ✅ `ensure_registry` - 成功
- ✅ `fetch_factor_jobs` - 成功
- ✅ `evaluate_factor` (动态映射的多个实例) - 全部成功
- ❌ `aggregate_results` - 显示"上游任务失败"(实际上上游都成功了)
- ❌ `publish_summary` - 显示"上游任务失败"

### 6.2 根本原因

**Airflow 3.x 动态任务映射的下游任务调度问题**

在当前的 DAG 定义中:

```python
evaluations = evaluate_factor.partial(env=ready_env).expand(job=jobs)
summary = aggregate_results(evaluations, ready_env)
publish_summary(summary)
```

问题在于:

1. `evaluate_factor.expand(job=jobs)` 创建了动态映射任务
2. `aggregate_results` 期望接收一个列表参数 `evaluations`
3. Airflow 3.x 在处理动态映射任务的输出传递给下游非映射任务时,存在任务依赖解析问题
4. 导致 `aggregate_results` 和 `publish_summary` 虽然在 DAG 图中定义了,但实际运行时未被调度执行

即使所有 `evaluate_factor` 任务实例都成功完成,Airflow 也不会自动触发 `aggregate_results`,因为它无法正确理解如何将多个映射任务的输出聚合为一个列表传递给下游任务。

### 6.3 解决方案

#### 方案一:使用独立的聚合脚本(推荐,已实现)

由于 DAG 中的聚合任务存在调度问题,我们创建了独立的 Python 脚本 `generate_summary.py` 来完成聚合工作:

**脚本功能:**

- 从 registry 数据库读取所有 SUCCESS 状态的作业
- 提取每个作业的 metrics (IC, ICIR, annual_return, sharpe_ratio, max_drawdown 等)
- 生成排序后的 summary CSV 文件
- 更新 registry 中的 result_path 字段

**使用方法:**

```bash
# 在容器中运行
docker exec -it airflow_new-airflow-standalone-1 bash -lc \
  "cd /opt/airflow && python generate_summary.py \
   --registry-db /opt/airflow/metadata/factor_platform.db \
   --output-dir /opt/airflow/.airflow_factor_pipeline"

# 将结果复制到主机
docker cp airflow_new-airflow-standalone-1:/opt/airflow/.airflow_factor_pipeline/qlib_factor_summary_*.csv \
  ./qlib_factor_summary.csv
```

**优点:**

- 立即可用,不依赖 Airflow 调度
- 可以随时重新运行生成最新汇总
- 脚本简单易维护
- 避开了 Airflow 动态映射的复杂性

#### 方案二:修改 DAG 结构(未来改进)

如果需要在 DAG 内部完成聚合,可以考虑以下改进方向:

**选项 A - 使用传感器任务轮询 registry:**

```python
@task.sensor(poke_interval=10, timeout=300, mode='poke')
def wait_for_evaluations(env):
    """轮询registry,等待所有PENDING作业完成"""
    store = FactorStore(Path(env["registry_db"]))
    pending = store.list_jobs(status="PENDING")
    return len(pending) == 0  # 全部完成时返回True

@task
def aggregate_from_registry(env):
    """直接从registry读取并聚合,不依赖上游XCom"""
    store = FactorStore(Path(env["registry_db"]))
    success_jobs = store.list_jobs(status="SUCCESS")
    # ...生成summary...
    return summary_path

# DAG中:
evaluations = evaluate_factor.partial(env=ready_env).expand(job=jobs)
wait = wait_for_evaluations(ready_env)
evaluations >> wait  # evaluate_factor完成后触发等待
summary = aggregate_from_registry(ready_env)
wait >> summary  # 等待完成后聚合
publish_summary(summary)
```

**选项 B - 拆分为两个 DAG:**

```python
# DAG 1: 评估DAG
@dag(dag_id="factor_evaluation")
def evaluation_pipeline():
    jobs = fetch_factor_jobs(env)
    evaluate_factor.partial(env=env).expand(job=jobs)

# DAG 2: 汇总DAG(手动触发或定时)
@dag(dag_id="factor_aggregation", schedule=None)
def aggregation_pipeline():
    summary = aggregate_results_from_db(env)
    publish_summary(summary)
```

### 6.4 当前工作流程

基于方案一,推荐的完整工作流程:

**重要提示:Windows PowerShell 和 Linux Bash 的行继续符不同**

- **Bash/Linux**: 使用反斜杠 `\` 作为行继续符
- **PowerShell**: 使用反引号 `` ` `` 作为行继续符,或者直接写成单行

#### Linux/Mac (Bash) 命令格式:

```bash
# 1. 初始化registry(首次)
docker exec -it airflow_new-airflow-standalone-1 bash -lc \
  "cd /opt/airflow && python -m factor_platform.cli init-db --seed configs/factors.json"

# 2. 提交因子评估作业
docker exec -it airflow_new-airflow-standalone-1 bash -lc \
  "cd /opt/airflow && python -m factor_platform.cli submit-job alpha_mom_5 \
   --start 2020-01-01 --end 2024-12-31 --freq day --instruments 000001"

# 3. 触发Airflow DAG执行评估
docker exec -it airflow_new-airflow-standalone-1 bash -lc \
  "cd /opt/airflow && airflow dags trigger starquant_factor_pipeline"

# 4. 等待DAG中的evaluate_factor任务全部完成(在UI中监控)

# 5. 运行独立的聚合脚本生成summary
docker exec -it airflow_new-airflow-standalone-1 bash -lc \
  "cd /opt/airflow && python generate_summary.py \
   --registry-db /opt/airflow/metadata/factor_platform.db \
   --output-dir /opt/airflow/.airflow_factor_pipeline"

# 6. 复制结果到主机
docker cp airflow_new-airflow-standalone-1:/opt/airflow/.airflow_factor_pipeline/qlib_factor_summary_*.csv \
  ./results/
```

#### Windows PowerShell 命令格式:

**方式 1: 使用反引号 ` 作为行继续符**

```powershell
# 1. 初始化registry(首次)
docker exec -it airflow_new-airflow-standalone-1 bash -lc `
  "cd /opt/airflow && python -m factor_platform.cli init-db --seed configs/factors.json"

# 2. 提交因子评估作业
docker exec -it airflow_new-airflow-standalone-1 bash -lc `
  "cd /opt/airflow && python -m factor_platform.cli submit-job alpha_mom_5 --start 2020-01-01 --end 2024-12-31 --freq day --instruments 000001"

# 3. 触发Airflow DAG执行评估
docker exec -it airflow_new-airflow-standalone-1 bash -lc `
  "cd /opt/airflow && airflow dags trigger starquant_factor_pipeline"

# 4. 等待evaluate_factor任务完成后,运行聚合脚本
docker exec -it airflow_new-airflow-standalone-1 bash -lc `
  "cd /opt/airflow && python generate_summary.py --registry-db /opt/airflow/metadata/factor_platform.db --output-dir /opt/airflow/.airflow_factor_pipeline"

# 5. 复制结果到主机
docker cp airflow_new-airflow-standalone-1:/opt/airflow/.airflow_factor_pipeline/qlib_factor_summary_*.csv ./results/
```

**方式 2: 单行命令(推荐)**

```powershell
# 1. 初始化registry
docker exec -it airflow_new-airflow-standalone-1 bash -lc "cd /opt/airflow && python -m factor_platform.cli init-db --seed configs/factors.json"

# 2. 提交因子评估作业
docker exec -it airflow_new-airflow-standalone-1 bash -lc "cd /opt/airflow && python -m factor_platform.cli submit-job alpha_mom_5 --start 2020-01-01 --end 2024-12-31 --freq day --instruments 000001"

# 3. 触发Airflow DAG
docker exec -it airflow_new-airflow-standalone-1 bash -lc "cd /opt/airflow && airflow dags trigger starquant_factor_pipeline"

# 4. 生成summary
docker exec -it airflow_new-airflow-standalone-1 bash -lc "cd /opt/airflow && python generate_summary.py --registry-db /opt/airflow/metadata/factor_platform.db --output-dir /opt/airflow/.airflow_factor_pipeline"

# 5. 复制结果
docker cp airflow_new-airflow-standalone-1:/opt/airflow/.airflow_factor_pipeline/qlib_factor_summary_*.csv ./
```

### 6.5 预期输出

运行 `generate_summary.py` 后的输出示例:

```
找到 3 个SUCCESS作业

================================================================================
Summary CSV 已生成: /opt/airflow/.airflow_factor_pipeline/qlib_factor_summary_20251126_041147.csv
================================================================================

前10个因子(按ICIR排序):

            code        name   IC ICIR  annual_return  sharpe_ratio  max_drawdown
    alpha_vol_10    10日波动率 None None       0.204277      0.501161      0.856320
   alpha_mom_20      20日动量 None None       0.203371      0.498634      0.871640
    alpha_mom_5       5日动量 None None       0.197807      0.487305      0.874512

================================================================================

✓ 成功生成summary: /opt/airflow/.airflow_factor_pipeline/qlib_factor_summary_20251126_041147.csv
```

### 6.6 注意事项

1. **IC/ICIR 为 None 的原因**: 单股票数据无法计算 IC(信息系数),因为 IC 需要横截面数据(多只股票同一时间点的因子值与收益率)。要获得有效的 IC 指标,需要提交覆盖多只股票的作业(如 `--instruments csi300`)。

2. **metrics 字段格式**: registry 中的 `metrics_json` 字段存储为 JSON 字符串,其中 NaN 值需要特殊处理。`generate_summary.py` 已处理此问题。

3. **定时聚合**: 可以将 `generate_summary.py` 配置为 cron 任务或独立的 Airflow DAG 定期运行。

4. **结果路径**: 所有 summary CSV 自动记录在 registry 的 `result_path` 字段中,可通过 CLI 查询:
   ```bash
   python -m factor_platform.cli list-jobs --status SUCCESS
   ```

### 6.7 已验证的成功案例

通过上述工作流程,系统已成功完成:

- ✅ 初始化 registry 并种子化 5 个因子定义
- ✅ 提交并执行了 3 个因子评估作业(alpha_mom_5, alpha_mom_20, alpha_vol_10)
- ✅ 所有 evaluate_factor 任务成功完成并将 metrics 保存到 registry
- ✅ 使用 generate_summary.py 生成了包含完整 metrics 的 summary CSV
- ✅ 输出文件包含 annual_return, sharpe_ratio, max_drawdown 等关键指标

### 6.8 常见问题排查

#### Q1: PowerShell 中执行多行命令失败

**问题现象:**

```powershell
docker exec -it airflow_new-airflow-standalone-1 bash -lc \
  "cd /opt/airflow && python -m factor_platform.cli submit-job alpha_mom_5 \
   --start 2020-01-01 --end 2024-12-31 --freq day --instruments 000001"
```

执行后可能报错或行为异常。

**原因:**
PowerShell 使用反引号 `` ` `` 作为行继续符,而不是 Bash 的反斜杠 `\`。

**解决方案:**

- **方案 1**: 改用反引号:

  ```powershell
  docker exec -it airflow_new-airflow-standalone-1 bash -lc `
    "cd /opt/airflow && python -m factor_platform.cli submit-job alpha_mom_5 --start 2020-01-01 --end 2024-12-31 --freq day --instruments 000001"
  ```

- **方案 2**: 使用单行命令(推荐):
  ```powershell
  docker exec -it airflow_new-airflow-standalone-1 bash -lc "cd /opt/airflow && python -m factor_platform.cli submit-job alpha_mom_5 --start 2020-01-01 --end 2024-12-31 --freq day --instruments 000001"
  ```

#### Q2: 如何查看已提交的作业状态?

```powershell
# 查看所有作业
docker exec -it airflow_new-airflow-standalone-1 bash -lc "cd /opt/airflow && python -m factor_platform.cli list-jobs"

# 只查看成功的作业
docker exec -it airflow_new-airflow-standalone-1 bash -lc "cd /opt/airflow && python -m factor_platform.cli list-jobs --status SUCCESS"

# 只查看失败的作业
docker exec -it airflow_new-airflow-standalone-1 bash -lc "cd /opt/airflow && python -m factor_platform.cli list-jobs --status FAILED"
```

#### Q3: 如何查看已注册的因子?

```powershell
docker exec -it airflow_new-airflow-standalone-1 bash -lc "cd /opt/airflow && python -m factor_platform.cli list-factors"
```

#### Q4: 如何添加新的因子定义?

```powershell
# 方式1: 通过CLI注册单个因子
docker exec -it airflow_new-airflow-standalone-1 bash -lc "cd /opt/airflow && python -m factor_platform.cli register-factor alpha_new_factor 'Ref(\$close, 10) / \$close - 1' --category momentum --name '10日动量因子'"

# 方式2: 编辑configs/factors.json后重新seed
# 1. 编辑configs/factors.json添加新因子
# 2. 复制到容器: docker cp configs/factors.json airflow_new-airflow-standalone-1:/opt/airflow/configs/
# 3. 重新seed: docker exec -it airflow_new-airflow-standalone-1 bash -lc "cd /opt/airflow && python -m factor_platform.cli init-db --seed configs/factors.json"
```

#### Q5: 容器重启后数据会丢失吗?

**不会。** Registry 数据库(`factor_platform.db`)和生成的 summary CSV 都存储在容器的持久化卷中。即使容器重启,数据仍然保留。

但为了安全起见,建议定期备份:

```powershell
# 备份registry数据库
docker cp airflow_new-airflow-standalone-1:/opt/airflow/metadata/factor_platform.db ./backup/

# 备份所有summary结果
docker cp airflow_new-airflow-standalone-1:/opt/airflow/.airflow_factor_pipeline ./backup/
```

#### Q6: 如何清理旧的作业记录?

目前 CLI 不支持删除作业,但可以直接操作数据库:

```powershell
# 进入容器
docker exec -it airflow_new-airflow-standalone-1 bash

# 在容器内执行
cd /opt/airflow
sqlite3 /opt/airflow/metadata/factor_platform.db

# SQLite命令:
# 查看所有作业: SELECT id, factor_code, status, created_at FROM factor_jobs;
# 删除失败的作业: DELETE FROM factor_jobs WHERE status='FAILED';
# 删除指定作业: DELETE FROM factor_jobs WHERE id=7;
# 退出: .quit
```

#### Q7: evaluate_factor 任务显示失败但日志显示成功?

**问题**: Airflow UI 中 `evaluate_factor` 任务标记为失败,但查看日志发现任务实际执行成功,返回了正确的结果。

**根本原因**: Airflow 3.x 的 XCom 序列化机制无法处理 Python 的 `nan` 值。当因子评估返回的 metrics 中包含 `nan`(例如单股票数据无法计算 IC 时),XCom 序列化失败导致任务被标记为失败。

**解决方案**: 在 `evaluate_factor` 函数返回前,将所有 `nan` 值转换为 `None`:

```python
# 在 starquant_factor_pipeline.py 的 evaluate_factor 函数中
# Convert nan values to None for XCom serialization
serializable_metrics = {
    k: (None if isinstance(v, (float, np.floating)) and np.isnan(v) else
        float(v) if isinstance(v, (np.floating, np.integer)) else v)
    for k, v in metrics.items()
}

return {
    "job_id": job_id,
    "code": factor_code,
    "name": factor_name,
    "status": "SUCCESS",
    "metrics": serializable_metrics,  # 使用序列化后的metrics
    "expression": job["expression"],
}
```

**验证**: 更新 DAG 后重新触发,任务应该正常完成而不再失败。

---

## 7. 快速参考卡片

### 7.1 PowerShell vs Bash 命令对比

| 操作     | Bash (Linux/Mac) | PowerShell (Windows) |
| -------- | ---------------- | -------------------- |
| 行继续符 | `\`              | `` ` `` (反引号)     |
| 推荐方式 | 多行             | 单行                 |

### 7.2 常用命令速查

```powershell
# === 查看状态 ===
# 列出所有因子定义
docker exec -it airflow_new-airflow-standalone-1 bash -lc "cd /opt/airflow && python -m factor_platform.cli list-factors"

# 查看所有作业
docker exec -it airflow_new-airflow-standalone-1 bash -lc "cd /opt/airflow && python -m factor_platform.cli list-jobs"

# 只看成功的作业
docker exec -it airflow_new-airflow-standalone-1 bash -lc "cd /opt/airflow && python -m factor_platform.cli list-jobs --status SUCCESS"

# === 提交任务 ===
# 提交单个因子评估作业
docker exec -it airflow_new-airflow-standalone-1 bash -lc "cd /opt/airflow && python -m factor_platform.cli submit-job alpha_mom_5 --start 2020-01-01 --end 2024-12-31 --freq day --instruments 000001"

# 提交多股票作业(可以计算IC)
docker exec -it airflow_new-airflow-standalone-1 bash -lc "cd /opt/airflow && python -m factor_platform.cli submit-job alpha_mom_5 --start 2020-01-01 --end 2024-12-31 --freq day --instruments csi300"

# === 触发DAG ===
docker exec -it airflow_new-airflow-standalone-1 bash -lc "cd /opt/airflow && airflow dags trigger starquant_factor_pipeline"

# === 生成汇总 ===
docker exec -it airflow_new-airflow-standalone-1 bash -lc "cd /opt/airflow && python generate_summary.py --registry-db /opt/airflow/metadata/factor_platform.db --output-dir /opt/airflow/.airflow_factor_pipeline"

# === 复制结果 ===
docker cp airflow_new-airflow-standalone-1:/opt/airflow/.airflow_factor_pipeline/qlib_factor_summary_*.csv ./
```

### 7.3 工作流程图

```
┌─────────────────────────────────────────────────────────────────┐
│  因子分析完整工作流程                                              │
└─────────────────────────────────────────────────────────────────┘

    ┌──────────────────┐
    │ 1. 初始化Registry  │ (首次运行)
    │   init-db --seed  │
    └────────┬──────────┘
             │
             ▼
    ┌──────────────────┐
    │ 2. 注册/查看因子   │
    │  list-factors    │
    └────────┬──────────┘
             │
             ▼
    ┌──────────────────┐
    │ 3. 提交评估作业    │
    │   submit-job     │
    └────────┬──────────┘
             │
             ▼
    ┌──────────────────┐
    │ 4. 触发DAG执行    │
    │  trigger DAG     │
    └────────┬──────────┘
             │
             ▼
    ┌──────────────────────────────────┐
    │ 5. Airflow自动执行                │
    │  ├─ bootstrap_environment  ✓     │
    │  ├─ ensure_registry        ✓     │
    │  ├─ fetch_factor_jobs      ✓     │
    │  └─ evaluate_factor (×N)   ✓     │
    └────────┬─────────────────────────┘
             │
             ▼
    ┌──────────────────┐
    │ 6. 生成Summary    │
    │ generate_summary │
    └────────┬──────────┘
             │
             ▼
    ┌──────────────────┐
    │ 7. 查看/下载结果  │
    │   docker cp      │
    └──────────────────┘
```

### 7.4 关键文件路径

| 文件/目录       | 容器内路径                                                        | 说明               |
| --------------- | ----------------------------------------------------------------- | ------------------ |
| Registry 数据库 | `/opt/airflow/metadata/factor_platform.db`                        | 因子定义和作业状态 |
| 因子配置        | `/opt/airflow/configs/factors.json`                               | 种子因子定义       |
| Summary 输出    | `/opt/airflow/.airflow_factor_pipeline/qlib_factor_summary_*.csv` | 评估结果汇总       |
| DAG 代码        | `/opt/airflow/dags/starquant_factor_pipeline.py`                  | Airflow DAG 定义   |
| 聚合脚本        | `/opt/airflow/generate_summary.py`                                | 独立的汇总脚本     |
| 股票数据        | `/opt/airflow/stockdata/1d_1w_1m/*.csv`                           | 本地 CSV 数据      |

---
