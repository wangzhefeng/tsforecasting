# 统一时间序列预测框架方案 v2

> 状态：v2 当前实施基线。
>
> 保存位置：`docs/unified-ts-framework-plan-v2.md`
>
> 来源：基于 `docs/unified-ts-framework-plan-v1.md` 的方案评审结果收敛而来。v1 保留为历史基线，不直接覆盖。
>
> 目的：把过大的 Nixtla-only MVP 拆成可验证纵切面，降低第一轮落地风险，并为后续 MLForecast、NeuralForecast、HierarchicalForecast、reporting 和 full catalog 扩展保留清晰边界。

## 1. 背景与目标

`tsforecasting` 是一个预实现阶段的统一时间序列预测框架项目。当前仓库已经具备项目元数据、文档、`utils/log_util.py`，尚未创建 `src/`、`configs/`、`examples/`、`tests/`、CLI 入口、测试运行器或 linter。

新框架的长期目标仍然是统一时间序列预测流程：

- 数据读取与预处理。
- 特征声明与后端映射。
- 训练、预测、回测。
- 指标评估。
- artifact、manifest、日志和报告。

v2 保留 v1 的核心方向：Nixtla-first、Nixtla long table、优先复用 Nixtla 原生 API、不在第一阶段接入 TimeGPT、legacy adapter 或本地 foundation model。v2 的主要调整是收缩第一阶段，把“平台蓝图”变成可逐步验证的工程切片。

## 2. 已确认选择

- 仓库和 Python 项目名统一为 `tsforecasting`。
- 内部预测数据契约采用 Nixtla long table：`unique_id / ds / y`。
- 第一阶段仍为 Nixtla-only，不接入 `tsproj_stat`、`tsproj_ml`、`tsproj_dl`、`tsproj_ltsfm`。
- MVP-0 先跑通 StatsForecast 纵切面，不要求三类后端同时可用。
- MVP-1 再接入 MLForecast、NeuralForecast CPU smoke 和 TourismSmall hierarchical reconciliation。
- UtilsForecast 用于通用指标评估；业务 mask、`MAPE Accuracy = 1 - MAPE` 等作为后续 business profile。
- TimeGPT、legacy adapter、本地 foundation model 进入后续阶段，不污染 MVP 核心契约。
- Jupyter notebook reporting 不再作为 MVP 阻塞项，移动到 Phase 2。

## 3. 阶段边界

### 3.1 MVP-0：StatsForecast 可运行纵切面

MVP-0 的目标是尽快得到一个可运行、可测试、可复查的最小框架闭环。

MVP-0 必须包含：

- `src/tsforecasting/` 包结构和 CLI entrypoint。
- `pytest` 与基础测试目录。
- 单一 YAML 配置 schema。
- CSV 数据读取与 `unique_id / ds / y` canonical frame 转换。
- 基础字段映射、频率校验、重复时间戳和缺失时间点检查。
- MVP preset registry，只注册 `SeasonalNaive`、`AutoETS` 等 StatsForecast smoke 模型。
- StatsForecast adapter，优先调用原生 `forecast` / `cross_validation`。
- UtilsForecast 统一产出至少 `mae / rmse / mape / smape`。
- 基础 artifacts：`run_config.yaml`、`manifest.json`、`predictions.csv`、`backtest_predictions.csv`、`metrics.json`、`metrics.csv`、`runtime_metrics.csv`、`model_comparison.csv`。
- `manifest.json` 记录配置来源、运行命令、输入数据、字段映射、后端、模型参数、split/backtest 设置、artifact 路径、日志路径和关键环境变量摘要。

MVP-0 不做：

- MLForecast、NeuralForecast、HierarchicalForecast。
- full model catalog。
- Jupyter notebook reporting。
- Python config、多 YAML 合并、复杂 CLI override。
- TimeGPT、legacy adapter、本地 foundation model。

### 3.2 MVP-1：Nixtla 后端扩展与层级验证

MVP-1 在 MVP-0 稳定后扩展：

- MLForecast adapter：使用 sklearn preset，映射 lags、date features、target transforms。
- NeuralForecast adapter：使用 CPU smoke 的 `NHITS` 或 `NBEATS`，限制训练步数。
- TourismSmall hierarchical reconciliation：加载 `Y_df / S_df / tags`，生成 base forecasts、reconciled forecasts 和 coherence diagnostics。
- 扩展测试：MLForecast smoke、NeuralForecast smoke、TourismSmall reconciliation smoke。

MVP-1 可以开始处理 NeuralForecast 特有验证语义，例如 `val_size`、`test_size`、`refit` 等，但不得反向改变 MVP-0 的 StatsForecast backtest 契约。

### 3.3 Phase 2：能力扩展与报告

Phase 2 包含原 v1 中过重的非首轮能力：

- full Nixtla model catalog / registry，按 `cataloged -> mvp_smoke -> validated -> blocked -> deprecated` 推进。
- Jupyter Lab notebook reporting 和可选 HTML 输出。
- 更多 StatsForecast、MLForecast、NeuralForecast 模型。
- 概率预测、区间指标、更多图表。
- 四个自有项目的架构诊断报告。

### 3.4 Phase 3：业务数据与 business profile

- 接入 AIDC demand_load 等业务数据。
- 增加宽表业务 CSV 到 long table 的 adapter。
- 支持历史外生、未来外生和静态特征。
- 增加 demand load evaluation profile、业务指标和复盘 artifact。

### 3.5 Phase 4：TimeGPT 与 legacy adapter

- TimeGPT real client 和 mock client。
- API key、成本、超时、重试和日志脱敏策略。
- 根据架构诊断结果决定 legacy adapter 的必要性和边界。

## 4. 推荐工程结构

MVP-0 目标结构：

```text
tsforecasting/
  pyproject.toml
  configs/
    examples/
      ett_small_stats.yaml
  examples/
    ett_small/
  src/
    tsforecasting/
      __init__.py
      cli/
      config/
      data/
      evaluation/
      artifacts/
      models/
        registry.py
        nixtla/
          stats.py
      orchestration/
      utils/
        logging.py
  tests/
    unit/
    integration/
  docs/
```

日志边界调整：

- v1 要求复用顶层 `utils/log_util.py`。v2 保留该工具的行为契约，但后续实现应迁入或封装到 `src/tsforecasting/utils/`，避免正式安装包依赖仓库顶层 `utils/`。
- 在迁移前，不能在 feature modules 中重复创建 logger handler。
- `SERVICE_LOG_LEVEL` 继续控制日志级别，`LOG_NAME` 继续控制日志目录语义。

## 5. 数据、配置与回测契约

### 5.1 canonical data contract

内部标准预测表：

```text
unique_id, ds, y
```

默认映射规则：

- 单序列数据如果没有 `id_col`，自动补 `unique_id = "series_0"`。
- `time_col` 映射为 `ds`。
- `target_col` 映射为 `y`。
- 原始列名、频率、字段映射写入 `manifest.json`。

MVP-0 校验：

- `ds` 可解析为时间戳。
- `freq` 必须显式配置或可稳定推断。
- 同一 `unique_id` 下不能有重复 `ds`。
- 缺失时间点要显式报出；是否补齐由后续配置决定，MVP-0 不静默补值。

### 5.2 YAML 配置

MVP-0 只支持单一 YAML 文件和少量运行级 CLI override：

```text
--run-id
--output-dir
--log-name
--log-level
--dry-run
```

MVP-0 backtest 只支持一种主语义：

```text
horizon + n_windows + step_size
```

`valid_size`、`test_size`、NeuralForecast `refit` 等放到 MVP-1 处理。这样可以先锁定 StatsForecast / UtilsForecast 纵切面的输出口径，避免第一轮配置同时承载多个后端差异。

### 5.3 ETT MVP-0 配置草案

```yaml
data:
  path: examples/ett_small/ETTm1.csv
  time_col: date
  target_col: OT
  id_col: null
  freq: 1h

backtest:
  horizon: 24
  n_windows: 3
  step_size: 24

models:
  - name: seasonal_naive
    backend: statsforecast
    params:
      season_length: 24
  - name: auto_ets
    backend: statsforecast
    params:
      season_length: 24

evaluation:
  metrics: [mae, rmse, mape, smape]
  engine: utilsforecast

runtime:
  collect_timing: true
  log_name: ett_small_mvp0
  log_level: INFO

artifacts:
  output_dir: runs/ett_small_stats
  save_plots: false
```

示例数据策略：

- `examples/ett_small/ETTm1.csv` 是目标路径，不得假设当前已经存在。
- P1/P2 应明确采用“提交极小 fixture”或“提供下载/cache 命令”中的一种，避免 smoke test 隐式依赖网络。

## 6. 模型与 registry 策略

MVP-0 只实现 MVP preset registry，不做 full catalog。

MVP-0 registry 最小字段：

```text
backend, model_name, class_path, model_type, mvp_preset, status
```

MVP-0 初始模型：

- `statsforecast.SeasonalNaive`
- `statsforecast.AutoETS`

MVP-1 扩展：

- MLForecast sklearn preset，例如 `LinearRegression`、`RandomForestRegressor`。
- NeuralForecast CPU smoke，例如 `NHITS` 或 `NBEATS`。
- HierarchicalForecast reconcilers。

Full catalog 放到 Phase 2。catalog 覆盖官方模型目录时，必须记录来源 URL 和当前验证状态，但不得把全量验证作为 MVP 阻塞项。

## 7. 输出契约

标准预测输出：

```text
unique_id, ds, yhat, model, backend, run_id
```

如果有真实值：

```text
unique_id, ds, y, yhat, model, backend, run_id
```

标准回测输出：

```text
unique_id, cutoff, ds, horizon, y, yhat, model, backend, run_id
```

运行指标输出：

```text
run_id, backend, model, model_type, n_series, n_rows, fit_seconds, predict_seconds, cross_validation_seconds, total_seconds
```

模型对比输出至少包含：

```text
run_id, backend, model, model_type, mae, rmse, mape, smape, total_seconds, rank_metric, rank
```

MVP-0 结果目录：

```text
runs/{run_id}/
  run_config.yaml
  manifest.json
  predictions.csv
  backtest_predictions.csv
  metrics.json
  metrics.csv
  runtime_metrics.csv
  model_comparison.csv
  logs/
```

MVP-1 层级验证额外目录：

```text
runs/{run_id}/
  base_predictions.csv
  reconciled_predictions.csv
  reconciliation_diagnostics.csv
```

Notebook reporting 目录移动到 Phase 2：

```text
reports/{run_id}/
  model_comparison.ipynb
  model_comparison.html
```

## 8. TourismSmall 层级配置草案

TourismSmall 不属于 MVP-0，进入 MVP-1。配置必须显式表达 reconciler 参数，不能只写模糊字符串。

```yaml
data:
  source: datasetsforecast
  dataset: TourismSmall
  freq: QE

base_forecast:
  backend: statsforecast
  models:
    - name: naive
      params: {}
    - name: auto_arima
      params:
        season_length: 4

hierarchical:
  reconcilers:
    - name: bottom_up
      class: BottomUp
      params: {}
    - name: top_down_forecast_proportions
      class: TopDown
      params:
        method: forecast_proportions
    - name: middle_out_country_purpose_state
      class: MiddleOut
      params:
        middle_level: Country/Purpose/State
        top_down_method: proportion_averages
  diagnostics: true

evaluation:
  metrics: [mse]
  engine: hierarchicalforecast

artifacts:
  output_dir: runs/tourism_small_hierarchical
```

## 9. 测试与验收

测试必须从 P1 开始，不得放到最后集中补。

MVP-0 验收：

- `uv run pytest` 可以运行最小测试套件。
- `validate-config` 能校验 ETT MVP-0 配置。
- canonical frame 转换测试覆盖无 `id_col`、重复时间戳、频率缺失或不可推断。
- StatsForecast smoke 可以生成 `predictions.csv`、`backtest_predictions.csv`、`metrics.csv`、`metrics.json`、`runtime_metrics.csv`、`model_comparison.csv`、`manifest.json`。
- `manifest.json` 包含配置、命令、日志、输入、字段映射、模型参数和 artifact 路径。

MVP-1 验收：

- MLForecast smoke 可运行并进入统一 metrics / comparison。
- NeuralForecast CPU smoke 可运行，训练步数受控。
- TourismSmall 可生成 base forecasts、reconciled forecasts 和 coherence diagnostics。

Phase 2 验收：

- full catalog 与官方模型目录有来源记录和 status。
- `reports/{run_id}/model_comparison.ipynb` 可由已存在 artifacts 生成。
- 自有四个项目的架构诊断报告能指出可保留能力、验证风险和优化方向。

## 10. 风险与约束

- NeuralForecast 会引入深度学习依赖，MVP-1 必须限制 CPU smoke 配置和运行时间。
- ETT、TourismSmall、业务宽表的数据契约不同，必须通过显式 loader 和 manifest 避免隐式转换。
- StatsForecast、MLForecast、NeuralForecast 的 cross-validation 输出列不同，统一转换必须有测试覆盖。
- UtilsForecast 通用指标和业务指标必须分层，避免业务口径污染 core evaluation。
- 没有明确层级结构的数据不得强行做 reconciliation。
- TimeGPT 受 API key、网络、成本、超时影响，不进入 MVP。
- Full catalog 和 notebook reporting 不应阻塞 MVP-0。

## 11. 方案调整记录

| date | change | reason | impact |
| --- | --- | --- | --- |
| 2026-06-22 | 生成 v2 当前实施基线 | v1 的 MVP 范围过大，三类后端、层级验证、full catalog 和 reporting 同时进入第一阶段会增加落地风险 | v1 保留为历史基线；后续执行入口改为 v2 + `docs/PLAN.md` |
| 2026-06-22 | 将 Phase 1 拆为 MVP-0 与 MVP-1 | 先用 StatsForecast 纵切面锁定配置、数据、回测、指标和 artifact 契约 | MLForecast、NeuralForecast、TourismSmall 移到 MVP-1 |
| 2026-06-22 | full catalog 和 Jupyter notebook reporting 移到 Phase 2 | 它们是扩展能力，不应阻塞首个可运行框架闭环 | MVP 只要求 CSV/JSON/manifest 可复查 |
| 2026-06-22 | 测试提前到 P1/P2 | 避免后端实现后才发现配置、数据和 artifact 契约漂移 | P1 引入 pytest，P2/P3 要求 schema 与数据契约测试 |
| 2026-06-22 | 调整日志工具包边界 | 顶层 `utils/` 不适合作为正式安装包内部依赖 | 后续迁入或封装到 `src/tsforecasting/utils/` |

## 12. 参考资料

Nixtla 官方资料：

- Nixtlaverse: <https://nixtlaverse.nixtla.io/>
- StatsForecast: <https://nixtlaverse.nixtla.io/statsforecast/>
- StatsForecast cross-validation: <https://nixtlaverse.nixtla.io/statsforecast/docs/tutorials/crossvalidation.html>
- MLForecast: <https://nixtlaverse.nixtla.io/mlforecast/>
- MLForecast cross-validation: <https://nixtlaverse.nixtla.io/mlforecast/docs/how-to-guides/cross_validation.html>
- NeuralForecast: <https://nixtlaverse.nixtla.io/neuralforecast/docs/getting-started/introduction.html>
- NeuralForecast cross-validation: <https://nixtlaverse.nixtla.io/neuralforecast/docs/capabilities/cross_validation.html>
- HierarchicalForecast: <https://nixtlaverse.nixtla.io/hierarchicalforecast/index.html>
- HierarchicalForecast TourismSmall example: <https://nixtlaverse.nixtla.io/hierarchicalforecast/examples/tourismsmall.html>
- UtilsForecast: <https://nixtlaverse.nixtla.io/utilsforecast/>
- TimeGPT docs: <https://www.nixtla.io/docs>

本机项目参考：

- `/Users/wangzf/projects/tsproj_stat/`
- `/Users/wangzf/projects/tsproj_ml/`
- `/Users/wangzf/projects/tsproj_dl/`
- `/Users/wangzf/projects/tsproj_ltsfm/`
