# PLAN.md

本文件是 `tsforecasting` 的可执行开发计划，来源于 `docs/unified-ts-framework-plan-v1.md`。后续开发以本文件的计划项为执行入口。

## 维护规则

- `docs/unified-ts-framework-plan-v1.md` 是 v1 架构方案基线，只记录方案设计、设计决策和方案调整记录。
- 架构、范围、MVP 目标或模块边界发生变化时，基于最新方案版本生成新的方案文档，例如 `docs/unified-ts-framework-plan-v2.md`，再同步本计划。
- 每次实施后更新本文件的“计划项实现记录”，记录已完成内容、验证命令、产物路径和下一步。
- 开发过程日志写入 `docs/LOG.md`，不要把日志混入方案文档。

## MVP 成功标准

- ETT 小数据能通过 StatsForecast、MLForecast、NeuralForecast 三类后端运行。
- UtilsForecast 统一产出至少 `mae / rmse / mape / smape`。
- TourismSmall 示例能产出 base forecasts、reconciled forecasts 和 coherence diagnostics。
- 统一输出 `predictions.csv`、`backtest_predictions.csv`、`metrics.json`、`metrics.csv`、`runtime_metrics.csv`、`model_comparison.csv`、`manifest.json`。
- `manifest.json` 记录配置来源、运行命令、日志路径、报告路径、关键环境变量摘要和 artifact 路径。
- `reports/{run_id}/` 能生成 Jupyter Lab 可打开的模型对比 notebook。
- TimeGPT、legacy adapter、本地 foundation model 不进入 MVP。

## 计划项实现记录

状态值：`not_started`、`in_progress`、`partial`、`done`、`blocked`。

| id | phase | task | status | source | done | evidence | next | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P0 | docs | 文档拆分、治理规则与知识入口整理 | done | `docs/unified-ts-framework-plan-v1.md` 第 8、11、12 节 | 新增 `docs/LOG.md`、`docs/PLAN.md`，将方案文档固化为 v1 基线，并同步 README/AGENTS/CLAUDE 当前项目状态 | `README.md`、`AGENTS.md`、`CLAUDE.md`、`docs/LOG.md`、`docs/PLAN.md`、`docs/unified-ts-framework-plan-v1.md` | 从 P1 开始工程脚手架实施 | 2026-06-22 |
| P1 | mvp | 工程脚手架与依赖 | not_started | 方案第 5、8 节 | 尚未创建 `src/tsforecasting/`、`configs/examples/`、`tests/` 或 CLI 入口 | 无 | 创建基础包结构，加入 Nixtla MVP 依赖并刷新 `uv.lock` | 2026-06-22 |
| P2 | mvp | YAML 配置与 CLI 入口 | not_started | 方案第 10.1、10.2、10.3 节 | 尚未实现配置 schema、配置校验和 CLI 命令 | 无 | 实现 `validate-config`、`run`、`backtest`、`predict`、`hierarchical`、`report` 命令骨架 | 2026-06-22 |
| P3 | mvp | canonical data contract 与 feature spec | not_started | 方案第 5.1、5.2、10.2 节 | 尚未实现长表转换、频率校验、外生变量声明 | 无 | 实现 `unique_id / ds / y` 转换、字段映射和 feature spec 解析 | 2026-06-22 |
| P4 | mvp | Nixtla model catalog / registry | not_started | 方案第 6.1、6.2 节 | 尚未实现 catalog 数据结构、模型目录和 MVP preset | 无 | 实现 registry 字段、Stats/ML/Neural/Hierarchical/Utils 目录和 status 管理 | 2026-06-22 |
| P5 | mvp | StatsForecast backend | not_started | 方案第 6.3、8 节 | 尚未实现 `models/nixtla/stats.py` | 无 | 接入 SeasonalNaive、AutoETS、轻量 AutoARIMA，并复用原生预测和 cross-validation API | 2026-06-22 |
| P6 | mvp | MLForecast backend | not_started | 方案第 6.4、8 节 | 尚未实现 `models/nixtla/ml.py` | 无 | 接入 sklearn preset，映射 lags、date features、target transforms 和 exogenous | 2026-06-22 |
| P7 | mvp | NeuralForecast backend | not_started | 方案第 6.5、8 节 | 尚未实现 `models/nixtla/neural.py` | 无 | 接入 CPU smoke 的 NHITS 或 NBEATS，并复用原生训练、预测、cross-validation、save/load | 2026-06-22 |
| P8 | mvp | backtesting、evaluation、runtime metrics、artifact | not_started | 方案第 5.3、5.7、5.8、10.6、10.7 节 | 尚未实现统一回测输出、UtilsForecast 评估、运行耗时和 artifact writer | 无 | 输出 predictions、backtest_predictions、metrics、runtime_metrics、model_comparison 和 manifest | 2026-06-22 |
| P9 | mvp | TourismSmall hierarchical reconciliation | not_started | 方案第 5.5、6.6、10.3、10.5 节 | 尚未实现层级数据加载、base forecast 和 reconciliation artifacts | 无 | 使用 TourismSmall 加载 `Y_df / S_df / tags`，调用 HierarchicalForecast reconciliation | 2026-06-22 |
| P10 | mvp | Jupyter Lab reporting | not_started | 方案第 5.12、10.7 节 | 尚未实现 reporting 模块和 notebook 模板 | 无 | 读取 run artifacts，生成 `reports/{run_id}/model_comparison.ipynb` 和可选 HTML | 2026-06-22 |
| P11 | mvp | smoke tests、文档同步和收尾验证 | not_started | 方案第 8、10 节 | 尚未建立测试结构和 smoke 验收命令 | 无 | 补齐文档检查、CLI smoke、ETT 示例、TourismSmall 示例和最终验证记录 | 2026-06-22 |

## MVP 开发顺序

1. P1：先补齐工程脚手架、依赖和基础目录，不实现复杂业务逻辑。
2. P2-P4：先固定配置、数据契约和 model catalog，避免后端实现时字段漂移。
3. P5-P7：分三类后端接入 StatsForecast、MLForecast、NeuralForecast，每个后端只做适配和输出标准化。
4. P8：统一 backtesting、evaluation、runtime metrics 和 artifact。
5. P9：独立实现 TourismSmall 层级验证，不把 ETT 强行改造成层级数据。
6. P10：实现报告输入和 notebook 输出。
7. P11：跑通 smoke 验收，更新 `docs/LOG.md` 和本计划的实现记录。

## 后续阶段 Roadmap

- 阶段 2：扩展更多 Nixtla 模型，按 catalog status 从 `cataloged` 推进到 `validated`，并形成自有四个项目的架构诊断报告。
- 阶段 3：接入 AIDC demand_load 等业务数据，增加 business profile、业务指标和更完整的复盘 artifact。
- 阶段 4：单独设计 TimeGPT、legacy adapter 和本地 foundation model 接入，不反向污染 MVP 核心契约。
