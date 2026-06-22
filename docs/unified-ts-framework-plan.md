# 统一时间序列预测框架方案评审稿

> 状态：方案评审稿，暂不进入代码实现。
>
> 保存位置：`docs/unified-ts-framework-plan.md`
>
> 目的：记录统一时间序列预测框架的背景、已确认选择、设计判断、待评审问题和阶段性计划，方便后续继续优化。

## 1. 背景与目标

过去的时间序列预测项目通常基于已有 Python 模型库，围绕具体模型自行构建完整流程：

- 数据读取与预处理
- 特征工程
- 模型训练
- 模型测试与回测
- 模型预测
- 指标评估
- 结果保存与可视化

已有相关项目：

- `/Users/wangzf/projects/tsproj_stat/`
- `/Users/wangzf/projects/tsproj_ml/`
- `/Users/wangzf/projects/tsproj_dl/`
- `/Users/wangzf/projects/tsproj_ltsfm/`

新框架的目标是设计一个统一时间序列预测框架，参考 Nixtla 生态的 API、数据契约和工具组织方式，支持统计模型、机器学习模型、深度学习模型、foundation model / TimeGPT 类模型，并为后续逐步接入四个历史项目提供稳定边界。

框架应覆盖的完整流程：

- 数据读取与预处理
- 特征工程
- 训练集、验证集、测试集切分
- 模型选择与配置
- 模型训练
- 模型测试与回测
- 模型预测
- 指标评估
- 结果保存与可视化

## 2. 已确认的关键选择

本轮方案讨论中已经确认以下选择：

- 新统一框架采用独立仓库，而不是直接改造 `tsproj_ml` 或把四个项目合成 monorepo。
- 内部数据契约采用 Nixtla 风格长表：`unique_id / ds / y`。
- 运行方式采用“核心轻依赖 + 后端隔离适配”。
- 第一阶段 MVP 后端为 StatsForecast、MLForecast、TimeGPT。
- 第一阶段 MVP 数据场景为 ETT 小数据。
- 历史项目迁移顺序按 `tsproj_stat -> tsproj_ml -> tsproj_dl -> tsproj_ltsfm` 理解。

这些选择背后的主要理由：

- 独立仓库可以避免某个历史项目的约定成为新框架的全局约束。
- Nixtla 长表契约最适合对齐 StatsForecast、MLForecast、NeuralForecast、TimeGPT，也能自然支持多序列。
- 四个历史项目的 Python、NumPy、Torch、Transformers 等依赖约束不同，不适合强行放入同一个运行环境。
- MVP 先覆盖统计、机器学习、远程 foundation/API 三类后端，可以较早暴露统一数据、配置、评估、结果契约的问题。
- ETT 小数据公开、轻量、跨框架通用，适合 smoke test 和接口验收。

## 3. 当前设计判断

### 3.1 先统一外部契约，不先统一训练内部

推荐优先统一：

- 数据契约
- 配置结构
- 回测窗口定义
- 预测输出格式
- 指标评估格式
- 结果落盘结构
- 运行 manifest

不建议第一阶段统一所有模型训练内部。StatsForecast、MLForecast、NeuralForecast、TimeGPT、本地 LTSFM 的训练/推理语义差异很大，过早统一 trainer 容易损失各后端原生能力，也会引入大量空泛抽象。

### 3.2 不把 `tsproj_ml` 作为新框架本体

`tsproj_ml` 当前已经有较完整的业务链路，包括 YAML 配置、数据读取、特征工程、模型训练、测试、预测和结果保存。但它的核心约定偏机器学习回归器和业务数据生产流程。如果直接把它作为新框架本体，容易让 ML 项目的历史约定压过统计、深度学习和 foundation model 的统一设计。

更稳妥的方式是：

- 新框架独立建设核心协议。
- `tsproj_ml` 作为 legacy adapter 接入。
- 逐步把稳定、通用、已验证的能力抽到新框架，而不是一次性迁移。

### 3.3 不把所有模型依赖放进一个 Python 环境

当前项目依赖边界存在明显差异：

- `tsproj_stat`：Python `>=3.12`，包含 `statsforecast`、`statsmodels`、`pmdarima`、`prophet` 等。
- `tsproj_ml`：Python `==3.10.11`，包含 LightGBM、XGBoost、CatBoost、scikit-learn 等。
- `tsproj_dl`：Python `>=3.10`，包含 PyTorch、Transformers、Reformer、Chronos、TimesFM 等。
- `tsproj_ltsfm`：Python `>=3.11`，对 NumPy、Torch、Transformers、TimesFM、Uni2TS 等有更强版本约束。

因此新框架核心应尽量轻依赖。模型后端可以分为：

- 进程内后端：StatsForecast、MLForecast 这类轻量且依赖相对可控的库。
- API 后端：TimeGPT。
- 子进程/隔离环境后端：`tsproj_dl`、`tsproj_ltsfm`、重依赖本地 foundation models。

### 3.4 旧项目先做 adapter，再抽公共能力

历史项目迁移不应一开始复制代码或大规模重构。建议采用 adapter-first 策略：

1. 新框架定义标准输入、运行配置和结果输出。
2. legacy adapter 将标准配置转换为旧项目能理解的 YAML/argparse/CLI 参数。
3. 旧项目照原方式运行。
4. adapter 负责把旧项目输出转换回统一结果契约。
5. 只有当两个以上后端重复出现稳定逻辑时，再抽到新框架核心。

## 4. 待评审问题清单

### 4.1 范围问题

- 新框架第一版是否只做 forecasting？
- 未来是否纳入 anomaly detection、imputation、classification？
- 如果纳入，是否仍在同一套 `Task` 抽象下处理，还是分为独立子系统？

建议默认：第一版只做 forecasting。其他任务保留目录和配置扩展空间，但不进入 MVP。

### 4.2 TimeGPT 调用策略

- MVP 是否允许真实 API 调用？
- 是否需要提供 mock / dry-run client，用于没有 `NIXTLA_API_KEY` 或网络受限时验证流程？
- TimeGPT 的 API 成本、超时、重试、日志脱敏如何管理？

建议默认：MVP 同时支持真实 client 和 mock client。默认测试走 mock，真实调用需要显式配置。

### 4.3 业务指标是否进入核心契约

`tsproj_ml` 中已有一些业务指标和输出约定，例如：

- `MAPE Accuracy = 1 - MAPE`
- 基于 eval mask 的异常点过滤
- 预测上下文保存
- 预测绘图拼接数据

待评审问题：

- 这些是否进入新框架核心？
- 还是先作为 business profile / evaluation plugin 存在？

建议默认：通用指标进入核心；业务 mask 和 MAPE Accuracy 作为 evaluation profile，不硬编码到核心默认行为。

### 4.4 NeuralForecast 与本地 LTSFM 后端边界

待评审问题：

- NeuralForecast 与本地 LTSFM 是否共享一套后端协议？
- 是否拆为 `neural` 后端与 `foundation_local` 后端？

建议默认：共享最小 `ForecastBackend` 协议，但目录和 runtime profile 分开。NeuralForecast 是可训练神经网络后端；本地 LTSFM 是预训练/foundation model 推理后端。

### 4.5 HierarchicalForecast 是否近期接入

待评审问题：

- 当前是否已有明确层级预测业务，例如园区/楼栋/房间/设备、产品/区域/门店？
- 是否需要 coherent forecast reconciliation？

建议默认：HierarchicalForecast 不进入 MVP。只有当业务数据存在明确层级聚合口径时再接入。

### 4.6 配置系统复杂度

待评审问题：

- 配置使用单一 YAML 文件，还是支持 Python config、YAML、CLI override 多源合并？
- 是否保留 `tsproj_ml` 的 grouped YAML 风格？

建议默认：MVP 使用单一 YAML。后续接入 `tsproj_ml` 时提供兼容转换器，不把旧 YAML 结构作为新框架唯一格式。

## 5. 推荐总体架构

推荐新框架作为独立 Python 包，暂定名 `tsforecast_lab`。

建议目录结构：

```text
tsforecast_lab/
  pyproject.toml
  README.md
  configs/
    examples/
      ett_small_statsforecast.yaml
      ett_small_mlforecast.yaml
      ett_small_timegpt.yaml
  examples/
    ett_small/
  src/
    tsforecast_lab/
      cli/
      config/
      data/
      features/
      splitting/
      backtesting/
      models/
        base.py
        registry.py
        nixtla_stats.py
        nixtla_ml.py
        timegpt.py
        legacy_stat.py
        legacy_ml.py
        legacy_dl.py
        legacy_ltsfm.py
      training/
      prediction/
      evaluation/
      artifacts/
      visualization/
      orchestration/
  tests/
    unit/
    integration/
  docs/
```

### 5.1 数据层 `data/`

职责：

- 读取 CSV、Parquet 等数据源。
- 识别或显式指定时间列、目标列、序列 ID 列。
- 转换为内部标准长表：`unique_id / ds / y`。
- 校验时间戳可解析、频率可推断或已配置、重复时间戳、缺失值、时间间隔连续性。
- 管理历史外生、未来外生、静态特征的字段映射。

默认规则：

- 单序列数据如果没有 `id_col`，自动补 `unique_id = "series_0"`。
- `time_col` 映射为 `ds`。
- `target_col` 映射为 `y`。
- 原始列名保存在 manifest 中，便于追溯。

### 5.2 特征层 `features/`

职责：

- 定义 feature spec，而不是一开始实现所有特征逻辑。
- 支持 date features、lag features、rolling features、target transforms、future exogenous。
- 对 MLForecast 优先使用原生 feature engineering。
- 对 legacy ML 项目通过 adapter 映射到原有 `FeatureEngineering.py`。

不建议第一阶段做一个庞大的通用 FeatureEngineer。不同后端对特征的接收方式不同，MVP 只需要把特征声明和后端映射打通。

### 5.3 切分与回测层 `splitting/`、`backtesting/`

职责：

- 统一 train/valid/test 切分。
- 统一 rolling、expanding、sliding 回测窗口定义。
- 标准化 `horizon`、`n_windows`、`step_size`、`cutoff`。

标准回测输出至少包含：

```text
unique_id, cutoff, ds, horizon, y, yhat, model
```

如果是多模型并行比较，允许同一结果表中存在多个 `model` 值。

### 5.4 模型层 `models/`

核心协议：

```python
ForecastBackend.fit(train_df, exog_df=None) -> FittedModel
ForecastBackend.predict(h, future_df=None) -> ForecastFrame
ForecastBackend.cross_validate(df, h, n_windows, step_size) -> BacktestFrame
ForecastBackend.save(path)
ForecastBackend.load(path)
```

注意：这只是外部协议，不要求所有后端内部都真的按同一方式训练。

后端类型：

- `nixtla_stats.py`：StatsForecast adapter。
- `nixtla_ml.py`：MLForecast adapter。
- `timegpt.py`：TimeGPT adapter。
- `legacy_stat.py`：`tsproj_stat` adapter。
- `legacy_ml.py`：`tsproj_ml` adapter。
- `legacy_dl.py`：`tsproj_dl` adapter。
- `legacy_ltsfm.py`：`tsproj_ltsfm` adapter。

### 5.5 训练与预测层 `training/`、`prediction/`

职责：

- 编排 fit、predict、cross_validate。
- 不直接实现复杂模型训练逻辑。
- 负责调用后端、收集结果、传递 runtime profile。

训练层不应持有过多业务逻辑。业务规则应放在配置、数据 adapter、evaluation profile 或 artifact writer 中。

### 5.6 评估层 `evaluation/`

通用指标：

- MAE
- RMSE
- MAPE
- SMAPE
- MASE
- R2
- pinball loss
- interval coverage
- interval width

业务评估 profile：

- demand load mask
- `MAPE Accuracy = 1 - MAPE`
- 近零值过滤
- 分位阈值过滤

建议第一阶段只实现通用指标，业务 profile 在接入 AIDC demand_load 或 `tsproj_ml` 时补充。

### 5.7 结果管理层 `artifacts/`

每次运行建议生成：

```text
runs/{run_id}/
  run_config.yaml
  manifest.json
  predictions.csv
  backtest_predictions.csv
  metrics.json
  metrics.csv
  plots/
  model/
  logs/
```

`manifest.json` 应记录：

- run id
- timestamp
- framework version
- input data path
- original column mapping
- canonical data columns
- model backend
- model parameters
- split/backtest settings
- output files
- environment summary

## 6. Nixtla 生态兼容方案

### 6.1 StatsForecast

定位：统计模型后端。

适合模型：

- AutoARIMA
- AutoETS
- AutoTheta
- MSTL
- Croston
- SeasonalNaive
- HistoricAverage
- GARCH / ARCH 等

接入方式：

- 输入使用 `unique_id / ds / y` 长表。
- 使用 StatsForecast 原生 `fit`、`predict`、`cross_validation`。
- 输出转换为统一 `ForecastFrame` / `BacktestFrame`。

适合第一阶段接入。

### 6.2 MLForecast

定位：机器学习模型后端。

适合模型：

- LightGBM
- XGBoost
- CatBoost
- RandomForest
- sklearn regressor

接入方式：

- 输入使用 `unique_id / ds / y` 长表。
- lags、lag transforms、date features、target transforms 优先映射到 MLForecast 原生参数。
- 模型参数保留 sklearn 风格。

适合第一阶段接入。

### 6.3 TimeGPT

定位：远程 foundation model / API 后端。

接入方式：

- 使用 Nixtla Python SDK。
- 输入需满足 TimeGPT 数据要求：时间列、目标列、频率、缺失值、时间连续性。
- 支持 `NIXTLA_API_KEY` 环境变量。
- 支持 mock / dry-run client 进行无 API key 的流程测试。

适合第一阶段接入，但真实调用应显式开启。

### 6.4 NeuralForecast

定位：深度学习预测后端。

适合模型：

- NBEATS
- NHITS
- TFT
- PatchTST
- LSTM / RNN / TCN
- Informer / Transformer 类模型

接入建议：

- 第二阶段接入。
- 使用独立 runtime profile。
- 不与 `tsproj_dl` 一开始强行合并。

### 6.5 HierarchicalForecast

定位：层级预测 reconciliation 层，不是基础模型层。

接入前置条件：

- 存在明确层级结构。
- 有 `S_df`、`tags` 或等价层级映射。
- 需要上下层预测一致性。

建议第三阶段或业务出现明确层级需求后接入。

### 6.6 UtilsForecast

定位：评估和可视化工具层。

可用于：

- 标准指标计算
- 多序列绘图
- 模型对比结果整理

是否使用由具体实现阶段决定，不应成为核心强依赖。

## 7. 现有四个项目迁移策略

### 7.1 `tsproj_stat`

当前特点：

- 已有 `app/`、`config/`、`models/`、`evaluation/`、`data_provider/`、`features/` 分层。
- 统计主线已接近统一 `fit(y, X_hist=None, X_future=None) / predict_one(X_future_one=None)` 契约。
- 已包含部分 StatsForecast 模型。

迁移策略：

1. 第一批作为 legacy adapter 接入。
2. 对齐输出字段：`forecast.csv`、`backtest_predictions.csv`、metrics。
3. 与 StatsForecast 原生后端做同数据对比。
4. 稳定后抽取通用统计模型 registry 经验。

### 7.2 `tsproj_ml`

当前特点：

- 以 LightGBM、XGBoost、CatBoost 为主。
- 已有 YAML 配置、数据读取、特征工程、训练、测试、预测、结果保存链路。
- 业务输出契约较强，例如 AIDC demand_load、MAPE Accuracy、预测上下文保存。

迁移策略：

1. 先做 YAML adapter：新框架配置转换为 `tsproj_ml` 可运行 YAML 或直接调用其 loader。
2. 先复用原 `main.Model.run()`，不重写训练细节。
3. adapter 负责把 `tsproj_ml` 输出转换为统一 artifact。
4. 后续再评估是否把稳定的业务 mask、预测上下文保存抽为新框架 profile。

### 7.3 `tsproj_dl`

当前特点：

- PyTorch 深度学习实验框架。
- 主入口是 `run.py`。
- 主线包括 `exp/exp_long_term_forecasting.py`、`data_provider/`、`models/`、`layers/`。
- 支持 Transformer、MLP、RNN、CNN、GNN 等模型族。

迁移策略：

1. 不直接合并依赖。
2. 通过子进程或独立环境运行 `run.py`。
3. 新框架只负责生成 argparse 参数和读取标准结果。
4. 后续再考虑与 NeuralForecast 后端的对比和收敛。

### 7.4 `tsproj_ltsfm`

当前特点：

- 面向大时间序列 foundation model。
- 包含 Time-MoE、Sundial、Chronos、TimesFM、Moirai、TiRex 等本地预训练模型。
- 已有 benchmark CLI 和统一输出雏形。
- 本地和 A100 服务器有不同运行策略。

迁移策略：

1. 最后接入，避免早期被重依赖和硬件环境拖住。
2. 保留其本地/A100 两级实验策略。
3. 通过 `foundation_local` runtime profile 调用。
4. 输出统一到 predictions、metrics、summary、plot、manifest。

## 8. 阶段性实施路线

### 阶段 1：MVP

目标：

- 新建独立框架仓库。
- 实现内部长表数据契约。
- 使用 ETT 小数据跑通 StatsForecast、MLForecast、TimeGPT 三类后端。
- 固定配置、评估、结果落盘契约。

核心任务：

- 创建基础包结构。
- 定义 YAML schema。
- 实现数据读取与 canonical frame 转换。
- 实现 StatsForecast adapter。
- 实现 MLForecast adapter。
- 实现 TimeGPT adapter 和 mock client。
- 实现统一 metrics 和 artifact writer。
- 提供 ETT smoke examples。

验收标准：

- 同一份 ETT 数据可以通过三个后端运行。
- 生成统一的 `predictions.csv`、`metrics.json`、`manifest.json`。
- 无 API key 时 TimeGPT mock 流程仍可验证。

### 阶段 2：业务数据与结果契约

目标：

- 接入 AIDC demand_load 作为业务数据场景。
- 引入业务评估 profile。
- 固化更完整的可追溯 artifact。

核心任务：

- 增加宽表业务 CSV 到长表的 adapter。
- 支持历史外生和未来外生。
- 增加 demand load evaluation profile。
- 增加预测上下文和绘图数据保存。

验收标准：

- AIDC demand_load 可以通过至少一个 Nixtla 后端和一个 legacy adapter 跑通。
- 输出能满足业务复盘和领导汇报所需字段。

### 阶段 3：历史项目接入

目标：

- 按顺序接入 `tsproj_stat -> tsproj_ml -> tsproj_dl -> tsproj_ltsfm`。

核心任务：

- `legacy_stat` adapter 接 `tsproj_stat`。
- `legacy_ml` adapter 接 `tsproj_ml` YAML 和 `main.Model.run()`。
- `legacy_dl` adapter 通过子进程运行 `tsproj_dl/run.py`。
- `legacy_ltsfm` adapter 通过 runtime profile 运行本地 foundation model benchmark。

验收标准：

- 每个历史项目至少有一个 smoke 配置可由新框架调度。
- 每个 adapter 都能输出统一 `manifest` 和结果表。

### 阶段 4：高级能力

目标：

- 加入 NeuralForecast。
- 在需要时加入 HierarchicalForecast。
- 增加批量实验、模型对比报告和可视化仪表盘。

核心任务：

- NeuralForecast adapter。
- 层级数据 schema 和 reconciliation 配置。
- 批量运行和模型排行榜。
- 报告生成。

验收标准：

- 能跨统计、机器学习、神经网络、foundation model 做统一模型对比。
- 结果可复现、可追溯、可审计。

## 9. 关键风险与不宜过早抽象的部分

### 9.1 关键风险

- 依赖冲突：四个历史项目依赖约束不同，尤其是 Torch、Transformers、NumPy、Python 版本。
- 数据契约漂移：业务宽表、Nixtla 长表、深度学习张量窗口之间容易出现隐式转换错误。
- 指标口径不一致：通用指标与业务 mask 指标需要清晰分层。
- TimeGPT 外部依赖：API key、网络、成本、超时、重试都会影响稳定性。
- 本地 LTSFM 运行成本：模型体积、硬件、MPS/CUDA、服务器路径都需要 runtime profile 管理。
- 结果保存不统一：如果 artifact 契约不先固定，后续迁移会反复返工。

### 9.2 不宜过早抽象

第一阶段不建议做：

- 通用 Trainer 大抽象。
- 通用 FeatureEngineer 大抽象。
- 全模型统一超参搜索。
- 全任务统一 Task 系统。
- 分布式训练。
- 层级预测。
- 本地 foundation model 管理平台。
- 完整 AutoML。

建议只在真实重复出现后再抽象：

- 两个以上后端共享同一逻辑。
- 两个以上业务场景需要同一评估 profile。
- 多个 adapter 产出相同 artifact 转换逻辑。

## 10. 当前方案草案

### 10.1 示例配置草案

```yaml
data:
  path: examples/ett_small/ETTm1.csv
  time_col: date
  target_col: OT
  id_col: null
  freq: 1h

split:
  horizon: 24
  valid_size: 96
  test_size: 96
  backtest:
    n_windows: 3
    step_size: 24
    window_mode: expanding

features:
  date_features: [hour, dayofweek]
  lags: [1, 24, 48]
  future_exog: []

models:
  - name: auto_arima
    backend: statsforecast
    params:
      season_length: 24
  - name: lgbm
    backend: mlforecast
    params:
      random_state: 42
  - name: timegpt
    backend: timegpt
    params:
      model: timegpt-1
      mode: mock

evaluation:
  metrics: [mae, rmse, mape, smape]
  mask: none

artifacts:
  output_dir: runs/ett_small_mvp
  save_plots: true
```

### 10.2 典型运行流程

```text
load_config
  -> load_raw_data
  -> convert_to_canonical_frame(unique_id/ds/y)
  -> validate_frequency_and_missing_values
  -> build_split_or_backtest_windows
  -> resolve_backend
  -> fit_or_cross_validate
  -> predict
  -> evaluate
  -> save_artifacts
  -> write_manifest
```

### 10.3 标准预测输出

```text
unique_id, ds, yhat, model, run_id
```

如果有真实值：

```text
unique_id, ds, y, yhat, model, run_id
```

回测输出：

```text
unique_id, cutoff, ds, horizon, y, yhat, model, run_id
```

概率预测可选列：

```text
yhat_q10, yhat_q50, yhat_q90, yhat_lo_95, yhat_hi_95
```

### 10.4 标准结果目录

```text
runs/{run_id}/
  run_config.yaml
  manifest.json
  predictions.csv
  backtest_predictions.csv
  metrics.json
  metrics.csv
  plots/
  model/
  logs/
```

### 10.5 当前默认假设

- 新框架暂定名为 `tsforecast_lab`，后续可改。
- MVP 只做 forecasting。
- MVP 数据使用 ETT 小数据。
- MVP 后端为 StatsForecast、MLForecast、TimeGPT。
- TimeGPT 默认支持 mock，真实 API 调用需要显式启用。
- 业务指标先作为 evaluation profile，不进入核心默认指标。
- 历史项目以 adapter 方式接入，不直接合并依赖和源码。

## 11. 参考资料

Nixtla 官方资料：

- Nixtlaverse: <https://nixtlaverse.nixtla.io/>
- StatsForecast: <https://nixtlaverse.nixtla.io/statsforecast/>
- MLForecast: <https://nixtlaverse.nixtla.io/mlforecast/>
- NeuralForecast: <https://nixtlaverse.nixtla.io/neuralforecast/docs/getting-started/introduction.html>
- NeuralForecast data requirements: <https://nixtlaverse.nixtla.io/neuralforecast/docs/getting-started/datarequirements.html>
- HierarchicalForecast: <https://nixtlaverse.nixtla.io/hierarchicalforecast>
- TimeGPT docs: <https://www.nixtla.io/docs>
- TimeGPT quickstart: <https://www.nixtla.io/docs/forecasting/timegpt_quickstart>
- TimeGPT data requirements: <https://www.nixtla.io/docs/data_requirements/data_requirements>
- TimeGPT SDK reference: <https://www.nixtla.io/docs/reference/sdk_reference>

本机项目参考：

- `/Users/wangzf/projects/tsproj_stat/`
- `/Users/wangzf/projects/tsproj_ml/`
- `/Users/wangzf/projects/tsproj_dl/`
- `/Users/wangzf/projects/tsproj_ltsfm/`

已观察到的本机项目事实：

- `tsproj_stat` 已有统计模型、EDA、回测、结果保存等分层，并已包含 `statsforecast` 依赖。
- `tsproj_ml` 当前主线是 `main.Model.run()`，配置以 YAML/dataclass 为主，结果和业务指标契约较强。
- `tsproj_dl` 当前推荐入口是 `run.py`，主线以 PyTorch 实验流程为主。
- `tsproj_ltsfm` 面向 foundation models，包含本地和 A100 两级实验策略，依赖隔离要求更高。
