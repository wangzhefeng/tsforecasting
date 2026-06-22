# PLAN.md

本文件是 `tsforecasting` 的可执行开发计划，当前来源于 `docs/unified-ts-framework-plan-v2.md`。后续开发以本文件的计划项为执行入口。

## 维护规则

- `docs/unified-ts-framework-plan-v1.md` 是 v1 历史基线，不直接覆盖。
- `docs/unified-ts-framework-plan-v2.md` 是当前实施基线，记录优化后的阶段边界、MVP 验收和方案调整。
- 架构、范围、MVP 目标或模块边界再次发生变化时，基于最新方案版本生成新的方案文档，例如 `docs/unified-ts-framework-plan-v3.md`，再同步本计划。
- 每次实施后更新本文件的“计划项实现记录”，记录已完成内容、验证命令、产物路径和下一步。
- 开发过程日志写入 `docs/LOG.md`，不要把日志混入方案文档。

## MVP 成功标准

### MVP-0：StatsForecast 可运行纵切面

- 工程包结构、CLI entrypoint、`pytest` 和基础测试目录已建立。
- 单一 YAML 配置可通过 `validate-config` 校验。
- CSV 数据能转换为 Nixtla long table：`unique_id / ds / y`。
- 数据契约测试覆盖无 `id_col`、重复时间戳、频率缺失或不可推断。
- StatsForecast `SeasonalNaive` / `AutoETS` smoke 可运行（示例数据用小时级 `ETTh1.csv`，与 `freq: 1h` / `season_length: 24` 一致；不要用 15 分钟的 `ETTm1.csv` 配 `freq: 1h`）。
- UtilsForecast 统一产出至少 `mae / rmse / mape / smape`。
- 统一输出 `predictions.csv`、`backtest_predictions.csv`、`metrics.csv`、`runtime_metrics.csv`、`model_comparison.csv`、`manifest.json`（`metrics.json` 推迟到 MVP-0b）。
- `manifest.json` 记录配置来源、运行命令、输入数据、字段映射、模型参数、`seed`、`run_id`、日志路径、关键环境变量摘要和 artifact 路径。

### MVP-1：Nixtla 后端扩展与层级验证

- MLForecast sklearn preset smoke 可运行，并进入统一 metrics / comparison。
- NeuralForecast `NHITS` 或 `NBEATS` CPU smoke 可运行，训练步数受控。
- TourismSmall 示例能产出 base forecasts、reconciled forecasts 和 coherence diagnostics。

### 非 MVP 阻塞项

- Full Nixtla model catalog、Jupyter notebook reporting、更多模型、TimeGPT、legacy adapter、本地 foundation model 不阻塞 MVP-0/MVP-1。

## 计划项实现记录

状态值：`not_started`、`in_progress`、`partial`、`done`、`blocked`。

| id | phase | task | status | source | done | evidence | next | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P0 | docs | 文档拆分、治理规则与知识入口整理 | done | `docs/unified-ts-framework-plan-v1.md` 第 8、11、12 节 | 新增 `docs/LOG.md`、`docs/PLAN.md`，将方案文档固化为 v1 基线，并同步 README/AGENTS/CLAUDE 当前项目状态 | `README.md`、`AGENTS.md`、`CLAUDE.md`、`docs/LOG.md`、`docs/PLAN.md`、`docs/unified-ts-framework-plan-v1.md` | 从 v2 优化计划继续推进 P1 | 2026-06-22 |
| P0.1 | docs | 方案与计划优化为 v2 | done | 方案评审结论 | 新增 `docs/unified-ts-framework-plan-v2.md`，将 MVP 拆成 MVP-0/MVP-1，并同步本计划 | `docs/unified-ts-framework-plan-v2.md`、`docs/PLAN.md`、`docs/LOG.md` | 从 P1 开始 MVP-0 工程脚手架实施 | 2026-06-22 |
| P0.2 | docs | v2 知识入口同步 | done | `docs/unified-ts-framework-plan-v2.md`、`docs/PLAN.md` | 同步 README、AGENTS、CLAUDE 的当前方案入口、MVP-0/MVP-1 边界和日志工具包边界 | `README.md`、`AGENTS.md`、`CLAUDE.md`、`docs/PLAN.md`、`docs/LOG.md` | 从 P1 开始 MVP-0 工程脚手架实施 | 2026-06-22 |
| P0.3 | docs | v2 评审修订 | done | v2/v1/PLAN 评审结论 | 修示例数据 ETTm1→ETTh1、MiddleOut 参数取值、补 extras 分组/CLI 语义/输出契约派生规则/seed-run_id、v1 加 SUPERSEDED banner、metrics.json 推迟 MVP-0b、P1 增 dependency spike + logging vendor | `docs/unified-ts-framework-plan-v2.md`、`docs/unified-ts-framework-plan-v1.md`、`docs/PLAN.md`、`docs/LOG.md` | 从 P1 开始 MVP-0 工程脚手架实施 | 2026-06-23 |
| P1 | mvp-0 | 工程脚手架、依赖与测试基础 | not_started | v2 第 3、4、9、10 节 | 尚未创建 `src/tsforecasting/`、`configs/examples/`、`tests/`、CLI entrypoint 或 `pytest` 配置 | 无 | 先做 dependency spike（验证 statsforecast/utilsforecast 在当前 pandas pin 下可解析并 import；若与 pandas 3.x 不兼容则 MVP-0 pin `pandas<3`），再创建基础包结构、按 §4 extras 加入 base+dev 依赖、将 `log_util` vendor 进 `src/tsforecasting/utils/logging.py`（改 lazy handler，包内禁 import 顶层 `utils/`）、建立最小 CLI（`validate-config` + `run`）与 `pytest` 测试目录 | 2026-06-23 |
| P2 | mvp-0 | YAML schema、CLI 骨架与配置校验 | not_started | v2 第 5.2、5.3 节 | 尚未实现配置 schema、`validate-config`、运行级 override 或配置测试 | 无 | 实现单一 YAML schema，支持 `validate-config`、`run`、`backtest` 骨架和 schema 单元测试 | 2026-06-22 |
| P3 | mvp-0 | canonical data contract 与 artifact schema | not_started | v2 第 5.1、7 节 | 尚未实现 long table 转换、频率校验、重复时间戳检查或 artifact schema | 无 | 实现 `unique_id / ds / y` 转换、字段映射、频率校验、artifact 字段契约和单元测试 | 2026-06-22 |
| P4 | mvp-0 | MVP preset registry | not_started | v2 第 6 节 | 尚未实现 registry 数据结构或 MVP preset | 无 | 只注册 `SeasonalNaive`、`AutoETS` 等 MVP-0 StatsForecast smoke 模型，不做 full catalog | 2026-06-22 |
| P5 | mvp-0 | StatsForecast backend | not_started | v2 第 3.1、6、7 节 | 尚未实现 `models/nixtla/stats.py` | 无 | 接入 `SeasonalNaive`、`AutoETS`，复用原生 `forecast` / `cross_validation` 并标准化输出 | 2026-06-22 |
| P6 | mvp-0 | backtesting、UtilsForecast evaluation 与 artifacts | not_started | v2 第 5.2、7、9 节 | 尚未实现统一回测输出、UtilsForecast 评估、运行耗时、artifact writer 或 manifest writer | 无 | 输出 predictions、backtest_predictions、metrics、runtime_metrics、model_comparison 和 manifest，并补 smoke 测试 | 2026-06-22 |
| P7 | mvp-1 | MLForecast backend | not_started | v2 第 3.2、6、9 节 | 尚未实现 `models/nixtla/ml.py` | 无 | 接入 sklearn preset，映射 lags、date features、target transforms，并进入统一评估与 artifact | 2026-06-22 |
| P8 | mvp-1 | NeuralForecast backend | not_started | v2 第 3.2、6、9 节 | 尚未实现 `models/nixtla/neural.py` | 无 | 接入 CPU smoke 的 NHITS 或 NBEATS，限制训练步数，并处理 NeuralForecast 验证语义 | 2026-06-22 |
| P9 | mvp-1 | TourismSmall hierarchical reconciliation | not_started | v2 第 3.2、8、9 节 | 尚未实现层级数据加载、base forecast、reconciliation artifacts 或 diagnostics | 无 | 使用 TourismSmall 加载 `Y_df / S_df / tags`，调用 HierarchicalForecast reconciliation，并保存 diagnostics | 2026-06-22 |
| P10 | phase-2 | Jupyter Lab reporting | not_started | v2 第 3.3、7、9 节 | reporting 不再阻塞 MVP；尚未实现 notebook 模板 | 无 | MVP-1 稳定后，读取 run artifacts 生成 `reports/{run_id}/model_comparison.ipynb` 和可选 HTML | 2026-06-22 |
| P11 | continuous | smoke tests、文档同步和阶段验收 | not_started | v2 第 9、11 节 | 尚未建立阶段性验收记录 | 无 | 每个阶段完成后运行对应 smoke，更新本计划和 `docs/LOG.md`，必要时生成下一版方案 | 2026-06-22 |

## MVP 开发顺序

1. P1：先补齐工程脚手架、CLI entrypoint、依赖分组、`pytest` 和基础测试目录。
2. P2-P3：固定 YAML schema、CLI 骨架、canonical data contract 和 artifact schema，并用单元测试锁住。
3. P4-P6：跑通 StatsForecast MVP-0 纵切面，生成统一 metrics、runtime、comparison 和 manifest。
4. P7-P9：在 MVP-0 稳定后依次加入 MLForecast、NeuralForecast、TourismSmall 层级验证。
5. P10：作为 Phase 2 实现 reporting，不作为 MVP 阻塞项。
6. P11：每个阶段都执行 smoke 验收和文档同步，而不是最后集中补测试。

## 后续阶段 Roadmap

- Phase 2：实现 full Nixtla model catalog、Jupyter notebook reporting、更多模型、概率预测、更多图表，并形成自有四个项目的架构诊断报告。
- Phase 3：接入 AIDC demand_load 等业务数据，增加 business profile、业务指标和更完整的复盘 artifact。
- Phase 4：单独设计 TimeGPT、legacy adapter 和本地 foundation model 接入，不反向污染 MVP 核心契约。
