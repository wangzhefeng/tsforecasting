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

> 状态：**已达成**（P1–P6 全部 done，2026-06-23）。

- 工程包结构、CLI entrypoint、`pytest` 和基础测试目录已建立。
- 单一 YAML 配置可通过 `validate-config` 校验。
- CSV 数据能转换为 Nixtla long table：`unique_id / ds / y`。
- 数据契约测试覆盖无 `id_col`、重复时间戳、频率缺失或不可推断。
- StatsForecast `SeasonalNaive` / `AutoETS` smoke 可运行（示例数据用小时级 `ETTh1.csv`，与 `freq: 1h` / `season_length: 24` 一致；不要用 15 分钟的 `ETTm1.csv` 配 `freq: 1h`）。
- UtilsForecast 统一产出至少 `mae / rmse / mape / smape`。
- 统一输出 `predictions.csv`、`backtest_predictions.csv`、`metrics.csv`、`runtime_metrics.csv`、`model_comparison.csv`、`manifest.json`（`metrics.json` 推迟到 MVP-0b）。
- `manifest.json` 记录配置来源、运行命令、输入数据、字段映射、模型参数、`seed`、`run_id`、日志路径、关键环境变量摘要和 artifact 路径。

### MVP-1：Nixtla 后端扩展与层级验证

> 状态：**已达成**（P7 MLForecast、P8 NeuralForecast、P9 TourismSmall hierarchical 全部 done，2026-06-23）。

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
| P1 | mvp-0 | 工程脚手架、依赖与测试基础 | done | v2 第 3、4、9、10 节 | 开 `feat/mvp-0-statsforecast` 分支；重写 `pyproject.toml`（hatchling+src 布局、`[project.scripts]`、base=statsforecast/utilsforecast/pyyaml/numpy/pandas、extras ml/neural/hierarchical/plot、dev=pytest/ruff、ruff+pytest 配置）；dependency spike 通过：上游硬钉 `pandas<3` 且 numba 传递依赖钉 `numpy<2.5` → pin `pandas>=2.2,<3` / `numpy>=1.26,<2.5`（解析 statsforecast 2.0.3 / pandas 2.3.3 / numpy 2.4.6 / numba 0.65.1）；vendor `utils/log_util.py`→`src/tsforecasting/utils/logging.py`（lazy、不重复 handler、CWD 相对）；argparse CLI 骨架（validate-config/run/backtest）；下载完整 `examples/ett_small/ETTh1.csv`；`tests/unit/test_logging.py` | `uv sync`；`uv run tsforecasting --help`；`uv run pytest -q`（7 passed） | P2：YAML schema + `validate-config` + run_id/seed | 2026-06-23 |
| P2 | mvp-0 | YAML schema、CLI 骨架与配置校验 | done | v2 第 5.2、5.3 节 | `src/tsforecasting/config/schema.py`（stdlib dataclasses + 手写校验，无 pydantic；data/backtest/models/evaluation/runtime/artifacts/predict/seed；load_config/validate/generate_run_id/resolve_overrides）；`configs/examples/ett_small_stats.yaml`；CLI 接入 `validate-config`（合法退出 0、非法退出 1）；`tests/unit/test_config.py` | `uv run tsforecasting validate-config --config configs/examples/ett_small_stats.yaml`；`uv run pytest -q`（21 passed）；`uv run ruff check .` | P3：canonical data contract + artifact schema | 2026-06-23 |
| P3 | mvp-0 | canonical data contract 与 artifact schema | done | v2 第 5.1、7 节 | `src/tsforecasting/data/loader.py`（CSV→`unique_id/ds/y`；字段映射；id_col 空→`series_0`；ds 解析；重复时间戳报错；freq 显式或可推断否则报错；缺失点计数不填充）；`src/tsforecasting/artifacts/schema.py`（5 个 artifact 列契约 + `validate_columns`）；`tests/unit/test_data_loader.py` | `uv run pytest -q`（29 passed）；`uv run ruff check .` | P4：MVP preset registry | 2026-06-23 |
| P4 | mvp-0 | MVP preset registry | done | v2 第 6 节 | `src/tsforecasting/models/registry.py`（RegistryEntry 字段 backend/model_name/class_path/model_type/mvp_preset/status/dependency_group；注册 `seasonal_naive`/`auto_ets` 均 core；`build_models(config)` 动态 import class_path 实例化）；`tests/unit/test_registry.py` | `uv run pytest -q`（34 passed）；`uv run ruff check .` | P5：StatsForecast backend | 2026-06-23 |
| P5 | mvp-0 | StatsForecast backend | done | v2 第 3.1、6、7 节 | `src/tsforecasting/models/nixtla/stats.py`（`StatsForecastAdapter`：原生 `fit`/`predict`/`cross_validation` + batched 计时；wide→long 归一到 predictions/backtest 契约；`horizon` 由 `groupby(unique_id,cutoff)` 的 dense rank 派生等价于 `(ds-cutoff)/freq`）；`tests/unit/test_stats_backend.py` | `uv run pytest -q`（37 passed）；`uv run ruff check .` | P6：backtest/UtilsForecast 评估 + artifacts + manifest + 端到端 smoke | 2026-06-23 |
| P6 | mvp-0 | backtesting、UtilsForecast evaluation 与 artifacts | done | v2 第 5.2、7、9 节 | `evaluation/metrics.py`（UtilsForecast `evaluate`→4 核心 metrics long form；`build_runtime_metrics`；`build_model_comparison` 按 `rank_metric` 排名）；`artifacts/writer.py`（5 CSV + `manifest.json` + `run_config.yaml`，写前 `validate_columns`）；`orchestration/run.py`（load→build→predict/cv→eval→artifacts，seed/run_id/logging 串联）；CLI `run`/`backtest` + `--dry-run`；`tests/integration/test_run_smoke.py` | `uv run tsforecasting run --config configs/examples/ett_small_stats.yaml`（`runs/{run_id}/` 产物齐全：predictions/backtest_predictions/metrics/runtime_metrics/model_comparison/manifest/run_config；auto_ets mae=1.054 rank1 胜 seasonal_naive mae=1.42）；`uv run pytest -q`（40 passed）；`uv run ruff check .` | MVP-0 纵切面完成；进入 MVP-1（P7-P9） | 2026-06-23 |
| P7 | mvp-1 | MLForecast backend | done | v2 第 3.2、6、9 节 | `config/schema.py` 增 `mlforecast` backend + 顶层 `MLForecastConfig`（lags/date_features/target_transforms spec）；`models/registry.py` 注册 6 个 sklearn preset（dependency_group=ml）；`models/nixtla/ml.py`（新）`MLForecastAdapter` 镜像 `StatsForecastAdapter`（同 melt/dense-rank horizon/batched 计时，mlforecast 1.0.31 构造需必填 `freq`、输出列序与 models= 一致）；`orchestration/run.py` 按 backend 分组分发适配器；`evaluation/metrics.py` `build_runtime_metrics` 改 dict[backend->timing]；`artifacts/writer.py` manifest 增 `mlforecast` provenance 键；示例 `configs/examples/ett_small_ml.yaml`（混合 statsforecast+mlforecast + Differences([24])） | `uv sync --extra ml`；`uv run tsforecasting run --config configs/examples/ett_small_ml.yaml`（混合 run：linear_regression mae=1.241 rank1 胜 seasonal_naive mae=1.422 rank2 胜 random_forest mae=1.453 rank3，跨 backend 统一排名）；`uv run pytest -q`（51 passed，with ml extra；base env 45 passed/3 skipped）；`uv run ruff check .` | P8：NeuralForecast CPU smoke（NHITS/NBEATS，受控训练步数 + val_size 语义） | 2026-06-23 |
| P8 | mvp-1 | NeuralForecast backend | done | v2 第 3.2、6、9 节 | `config/schema.py` `SUPPORTED_BACKENDS` 增 `neuralforecast`（无顶层 section，超参走 `models[].params`，因 NeuralForecast 超参挂模型实例上、异于 MLForecast 的框架共享 lags）；`models/registry.py` 注册 `nhits`+`nbeats`（`dependency_group="neural"`、`model_type="neural"`）；`models/nixtla/neural.py`（新）`NeuralForecastAdapter` 镜像 stats/ml（同 melt/dense-rank horizon/batched 计时；`predict(h)`/`cross_validation(h,...)` 显式传 `h`，并给 `fit`/`cv` 传 `val_size=h` 处理验证语义而不改 MVP-0 backtest 契约）；`orchestration/run.py` `_build_adapter` 增 `neuralforecast` 分支 lazy import；示例 `configs/examples/ett_small_neural.yaml`（statsforecast + nhits，`max_steps: 50`） | `uv sync --extra neural`；`uv run tsforecasting run --config configs/examples/ett_small_neural.yaml`（跨 backend 排名：nhits mae=0.938 rank1 胜 seasonal_naive mae=1.422 rank2；7 artifact 齐全；`Trainer.fit stopped: max_steps=50 reached`）；`uv run pytest -q`（neural env 50 passed/3 skipped；base env 47 passed/4 skipped）；`uv run ruff check .` | P9：TourismSmall hierarchical reconciliation（`Y_df`/`S_df`/`tags` + HierarchicalForecast reconciliation + coherence diagnostics） | 2026-06-23 |
| P9 | mvp-1 | TourismSmall hierarchical reconciliation | done | v2 第 3.2、8、9 节 | **独立流程**（不复用 MVP-0 `Config`/`run_pipeline`）：`config/hierarchical.py`（新，`HierarchicalConfig` + `base_forecast`/`hierarchical.reconcilers` 的 `{name,class,params}` spec，`evaluation` 限 `[mse]`）；`data/hierarchical.py`（新，`HierarchicalData.load` 取 `Y_df/S_df/tags` 三返回值——签名错标 2——并 `S_df.reset_index`）；`reconciliation.py`（新，base forecast→逐 reconciler reconcile→coherence 自验 `S@bottom==aggregate`+mse vs hold-out；reconciler 用 importlib 从 spec 实例化，无 reconciler registry）；`orchestration/reconcile.py`（新，`run_reconciliation`：hold-out `horizon` 步 split + 全流程）；`artifacts/{schema,writer}` 增 `base_predictions`/`reconciled_predictions`/`reconciliation_diagnostics` 三契约 + hierarchical manifest；CLI 新增 `reconcile` 子命令（+run-level overrides/--dry-run）；示例 `configs/examples/tourism_small_hierarchical.yaml`（`seasonal_naive` base + BottomUp/MinTrace/TopDown/MiddleOut 四 reconciler，`top_down_method=average_proportions`） | `uv sync --extra hierarchical`；`uv run tsforecasting reconcile --config configs/examples/tourism_small_hierarchical.yaml`（89 series/4 levels；train/test=2848/356；4 reconciler 全 `coherent=True`，`middle_out_state` mse=674088 最优 < 其余 677674）；`uv run pytest -q`（hierarchical env 65 passed/3 skipped；base env 59 passed/6 skipped）；`uv run ruff check .` | MVP-1 完成（P7-P9 全 done）；P10 reporting（Phase 2，非阻塞）；P11 阶段验收 | 2026-06-23 |
| P10 | phase-2 | Jupyter Lab reporting | done | v2 第 3.3、7、9 节 | `reporting.py`（新）：`detect_run_type` 按有无 `model_comparison.csv`/`reconciliation_diagnostics.csv` 区分 MVP-0 / hierarchical run；`build_mvp0_notebook`/`build_hierarchical_notebook` 用 `nbformat` **静态构造**（不执行）notebook（markdown 元信息 + 5 个 code cell：MVP-0 = 排名表/metrics 柱状图/backtest 曲线/runtime 计时；hierarchical = 层级表/diagnostics 排名表/mse 柱状图/reconciled vs base 曲线）；`generate_report` 写 `reports/{run_id}/model_comparison.ipynb` 或 `reconciliation.ipynb`。CLI 新增 `report --run-dir [--output-dir]` 子命令。新 `[report]` extra = `["nbformat"]`（绘图靠 `plot` extra 的 matplotlib，notebook 顶部注明 Run All 需 `pandas`+`matplotlib`）。HTML 导出（`nbconvert`）未做，后置 | `uv sync --extra report`；`uv run tsforecasting report --run-dir <stats run>` → `model_comparison.ipynb`（6 cells）；`--run-dir <hier run>` → `reconciliation.ipynb`（6 cells），均 nbformat 读回有效、静态（outputs 空）；`uv run pytest -q`（report+hierarchical+plot env 71 passed/3 skipped）；`uv run ruff check .` | P11 阶段验收；Phase 2 余项（full catalog、更多模型、概率预测、四项目架构诊断报告） | 2026-06-23 |
| P11 | continuous | smoke tests、文档同步和阶段验收 | done | v2 第 9、11 节 | 本轮对 MVP-0 / MVP-1 / Phase 2(P10) 做完整 smoke 验收（持续项，首次全验收）：全 extra env（`uv sync --extra ml --extra neural --extra hierarchical --extra report --extra plot`）下 4 个 example 端到端通过（`validate-config` ×4；`run` ett_small_stats/ml/neural；`reconcile` tourism_small_hierarchical），`report` 生成两种 notebook，`pytest` **79 passed/0 skipped**，`ruff` clean | `uv sync --extra ml --extra neural --extra hierarchical --extra report --extra plot`；4 example smoke；`uv run pytest -q`（79 passed）；`uv run ruff check .` | 验收清单：MVP-0（纵切面 + manifest）✓、MVP-1（MLForecast / NeuralForecast / TourismSmall）✓、Phase 2（reporting）✓；Phase 2 余项（full catalog、四项目架构诊断报告、概率预测、HTML 导出）待做 | 2026-06-23 |
| P12 | phase-2 | full Nixtla model catalog | done | v2 第 3.3、6、9 节 | `src/tsforecasting/models/catalog.py`（新，纯数据，独立于 `REGISTRY`）：`CatalogEntry`(name/backend/class_path/model_type/status/source_url/dependency_group) + `CATALOG` 共 77 条（statsforecast 35 + neuralforecast 34 + mlforecast-sklearn 8），`list_catalog(backend/status)` 过滤、`generate_catalog_md` 生成文档表。现有 10 个 mvp preset 标 `mvp_smoke`，其余 `cataloged`（plan §6「不全量验证」）；全部 `class_path` 经 import 验证 0 错。生成 `docs/model_catalog.md`（77 条来源 + 状态表） | `uv run pytest -q tests/unit/test_catalog.py`（6 passed）；全量 `class_path` import 验证 0 bad；`uv run ruff check .` | Phase 2 余项：四项目架构诊断报告（tsproj_*，推迟）、概率预测/区间指标、HTML 导出 | 2026-06-23 |
| P13 | phase-2 | HTML report export | done | v2 第 3.3、9 节 | `reporting.to_html`（新）：`nbconvert` `ExecutePreprocessor` 执行 notebook + `HTMLExporter` 转 HTML（含 matplotlib 图表输出）；kernel 缺失转 friendly `ImportError`（提示 `python -m ipykernel install --sys-prefix --name python3`）。CLI `report --html` flag。`generate_report` 把 run_dir resolve 为绝对路径（执行 cwd 无关）。`[report]` extra += `nbconvert`/`ipykernel` | `uv sync --extra report`；`tsforecasting report --run-dir <run> --html` → `.ipynb` + `.html`（372KB，含 `<img>`）；`pytest tests/unit/test_reporting.py`（7 passed） | — | 2026-06-24 |
| P14 | phase-2 | prediction intervals + 区间指标 | done | v2 第 3.3 节 | config 增 `PredictionIntervalsConfig(levels)` 顶层可选（`(0,100)` 整数）；`StatsForecastAdapter` 接 `levels`，`predict`/`cross_validation` 传 `level=` 并按模型 concat 把 `lo-{l}`/`hi-{l}` **追加**到 long（必需列契约不变）；`compute_metrics` 当 backtest 含 lo/hi 时加 `coverage-{l}`/`width-{l}` 行到 `metrics.csv`（`model_comparison` 只 pivot core metrics，区间行被忽略）。先支持 statsforecast（原生 level） | `tsforecasting run --config configs/examples/ett_small_intervals.yaml`（predictions/backtest 追加 lo-80/hi-80/lo-95/hi-95；metrics 含 coverage/width；comparison 仅 core）；`pytest`（85 passed/3 skipped） | 扩到 neural（quantile loss）/ml（conformal）；区间指标进 model_comparison | 2026-06-24 |
| P15 | phase-2 | intervals 扩展到 neural/ml + comparison | done | v2 第 3.3 节 | 共享 `melt_forecast_long` helper 从 stats 提取，ml/neural 复用。**neural**：新 preset `nhits_quantile`（NHITS+MQLoss），`build_model` 解析 `{class,kwargs}` loss spec 实例化 MQLoss（YAML-safe）；adapter 归一 `NHITS-lo-80.0`→`lo-80`、`NHITS-median`→point、`yhat`=median。**ml**：`fit` 传 `PredictionIntervals`（conformal），`predict(level=)` 产 lo/hi（**cv 不产**——MLForecast 限制，故 ml 仅 predictions 有区间）。**comparison**：`build_model_comparison` 当 metrics 含区间行时追加 `coverage-/width-` 列展示（`rank_metric` 仍点指标） | `tsforecasting run --config configs/examples/ett_small_intervals_mixed.yaml`（stats/ml/neural 三 backend predictions 都有 lo-80/hi-80；metrics 含 coverage-80/width-80；comparison 追加区间列）；`pytest`（90 passed/1 skipped） | ml cv intervals（受 MLForecast 限制）；区间 rank_metric | 2026-06-24 |

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
