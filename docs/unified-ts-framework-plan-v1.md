# 统一时间序列预测框架方案评审稿 v1

> ⚠️ **SUPERSEDED（已过期，仅作设计史保留）**：所有执行以 `docs/unified-ts-framework-plan-v2.md` + `docs/PLAN.md` 为准。**不要按本文件第 5 节模块图 / 第 6 节 catalog 实施**——下列 v1 内容已在 v2 中删除或后移，照 v1 实施会导致过度抽象：
>
> - **MVP 内 full model catalog**（§6.1）→ v2 推到 Phase 2；MVP-0 只注册 `SeasonalNaive` / `AutoETS`。
> - **`ForecastBackend.fit/predict/cross_validate/save/load` 通用后端协议**（§5.4）→ v2 删除，改为"优先调用各 Nixtla 原生 `forecast` / `cross_validation`"，不做通用 Trainer / FeatureEngineer。
> - **reporting / Jupyter notebook**（§5.12）→ v2 推到 Phase 2，不阻塞 MVP。
> - **features / splitting / backtesting 细分模块**（§5.2 / §5.3）→ v2 收敛；MVP-0 只做配置 / 校验 / 映射 / 输出标准化。
> - **三类后端同时进第一阶段**（§8 阶段 1）→ v2 拆为 MVP-0（仅 StatsForecast）+ MVP-1（ML / Neural / Hierarchical）。
>
> 本文件正文不再维护，仅供追溯设计判断与待评审问题的历史。

> 状态：v1 方案基线，**已被 v2 取代，不进入代码实现**（见上方 SUPERSEDED 说明）。
>
> 保存位置：`docs/unified-ts-framework-plan-v1.md`
>
> 目的：记录统一时间序列预测框架的背景、已确认选择、设计判断、待评审问题和阶段性计划，方便后续继续优化。
>
> 版本规则：本文件作为 v1 基线保存。后续如需修改方案，应基于本文件生成新的版本文档，例如 `docs/unified-ts-framework-plan-v2.md`，不要直接覆盖 v1。

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

当前统一框架仓库已经建立为：

- 本地路径：`/Users/wangzf/projects/tsforecasting/`
- GitHub 远程仓库：`git@github.com:wangzhefeng/tsforecasting.git`
- 当前项目名：`tsforecasting`

新框架的目标是在该仓库内设计一个统一时间序列预测框架，参考 Nixtla 生态的 API、数据契约和工具组织方式，支持统计模型、机器学习模型、深度学习模型、foundation model / TimeGPT 类模型，并为后续逐步接入四个历史项目提供稳定边界。

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
- 仓库和 Python 项目名统一为 `tsforecasting`；后续包目录、导入路径、示例命令和文档均以该命名为准。
- MVP 先做 Nixtla-only 兼容方案，不接入 `tsproj_stat`、`tsproj_ml`、`tsproj_dl`、`tsproj_ltsfm`。
- 内部数据契约采用 Nixtla 风格长表：`unique_id / ds / y`。
- MVP 可运行主线为 StatsForecast、MLForecast、NeuralForecast。
- UtilsForecast 作为 MVP 的评估、绘图、预处理工具层。
- HierarchicalForecast 在 MVP 中作为独立层级验证流程，使用 Nixtla 官方 `TourismSmall` 示例数据，不强行把 ETT 改造成层级数据。
- TimeGPT 不进入 MVP，作为后续 API / foundation model 计划。

这些选择背后的主要理由：

- 独立仓库可以避免某个历史项目的约定成为新框架的全局约束。
- Nixtla 长表契约最适合对齐 StatsForecast、MLForecast、NeuralForecast，也能自然支持多序列。
- MVP 先完整吸收 Nixtla 生态的原生数据、回测、评估、绘图和层级 reconciliation 能力，再反向诊断四个自有框架的验证问题和优化方向。
- StatsForecast、MLForecast、NeuralForecast 都提供原生训练、预测和 cross-validation 能力，第一版应优先调用这些原生能力，而不是重写通用 trainer。
- HierarchicalForecast 需要 `Y_df / S_df / tags` 等层级输入，适合用官方层级示例独立验证 coherence，而不适合作为普通模型后端混入 ETT 主线。
- ETT 小数据公开、轻量、跨框架通用，适合 StatsForecast、MLForecast、NeuralForecast 的 smoke test 和模型对比。

## 3. 当前设计判断

### 3.1 Nixtla-first，而不是 legacy adapter-first

推荐第一阶段优先统一：

- Nixtla 长表数据契约
- 单一 YAML 配置结构
- train/valid/test 和 rolling backtest 参数
- StatsForecast、MLForecast、NeuralForecast 的预测输出转换
- UtilsForecast 评估和绘图入口
- HierarchicalForecast reconciliation 输入和诊断输出
- 统一 artifact 和 manifest

不建议第一阶段接入四个自有项目。它们应先作为流程参考和架构诊断对象，用来回答“Nixtla 现成框架相比自有实现有哪些优势、自有实现是否存在验证问题、后续优化方向是什么”。

### 3.2 先调用 Nixtla 原生能力，不重写训练内部

StatsForecast、MLForecast、NeuralForecast 的训练/推理语义不同。第一阶段只定义最小外部协议和统一输出，不实现通用 Trainer 或通用 FeatureEngineer。

推荐边界：

- 数据、配置、artifact、manifest 由 `tsforecasting` 统一。
- fit、predict、cross-validation 优先调用各 Nixtla 框架原生方法。
- feature spec 只做声明和映射，不在核心里复制 MLForecast 或 NeuralForecast 的内部特征工程。
- reconciliation 作为 forecast 后处理阶段，不放入普通 model backend。

### 3.3 依赖策略：MVP 接受 Nixtla 依赖，避免 legacy 重依赖

当前 `pyproject.toml` 只有基础科学计算依赖，尚未加入 Nixtla 生态包。MVP 需要按阶段加入：

- `statsforecast`
- `mlforecast`
- `neuralforecast`
- `hierarchicalforecast`
- `utilsforecast`
- `datasetsforecast`

第一阶段可以在当前 Python 3.12 环境中验证 Nixtla-only 流程。四个自有项目的 Python、Torch、Transformers、本地 foundation model 依赖暂不合并进当前环境。

### 3.4 四个自有项目先做架构诊断，不做迁移

本轮方案不设计 legacy adapter。四个自有项目只用于形成诊断维度：

- 数据契约是否显式、稳定、可追溯
- 回测窗口是否防止数据泄漏
- 历史外生、未来外生、静态特征语义是否清晰
- 指标口径是否可复现、可对比
- artifact 是否能追踪配置、数据、模型参数和环境
- 依赖是否隔离
- 可视化和报告是否服务于模型诊断
- 性能扩展是否依赖自写循环还是可复用成熟框架

### 3.5 核心能力确认

新框架应明确支持以下三类能力：

1. 同一数据的多类型模型性能对比
   - 同一份单变量预测数据可以同时配置统计模型、机器学习模型、深度学习模型，后续再扩展 TimeGPT 或本地 foundation model。
   - 每类模型都允许配置一个或多个具体模型。
   - 对比维度至少包括准确率指标、运行耗时、模型类型、后端、数据规模、`run_id`。
   - 准确率指标统一进入 `metrics.csv` / `metrics.json`；速度和运行规模进入 `runtime_metrics.csv` / `runtime_metrics.json`；综合排序进入 `model_comparison.csv`。

2. 外生变量 / 协变量建模
   - `historic_exog`：历史区间可用的历史外生变量。
   - `future_exog`：预测未来区间已知或可提前获得的未来外生变量。
   - `static_features`：序列级静态特征。
   - 这些字段由 `features/` 层统一声明，再映射到 StatsForecast、MLForecast、NeuralForecast 的后端原生能力。

3. 参数配置与运行方式
   - MVP 主配置方式为单一 YAML 文件。
   - MVP 主运行方式为 CLI 读取 YAML 执行。
   - Python API 只作为 notebook、Jupyter Lab 和调试辅助入口，不作为 MVP 的主配置系统。
   - MVP 不支持 Python config、多 YAML 合并或复杂 CLI override。

## 4. 待评审问题清单

### 4.1 任务范围

- 第一版是否只做 forecasting？
- 未来是否纳入 anomaly detection、imputation、classification？
- 如果纳入，是否仍在同一套 `Task` 抽象下处理，还是分为独立子系统？

建议默认：第一版只做 forecasting。其他任务保留方向，但不进入 MVP。

### 4.2 TimeGPT 调用策略

- TimeGPT 是否作为 API / foundation model 阶段单独规划？
- 是否需要 mock / dry-run client，用于没有 `NIXTLA_API_KEY` 或网络受限时验证流程？
- TimeGPT 的 API 成本、超时、重试、日志脱敏如何管理？

建议默认：TimeGPT 不进入 MVP。后续阶段再设计真实 client 和 mock client，真实调用必须显式配置。

### 4.3 业务指标是否进入核心契约

`tsproj_ml` 中已有一些业务指标和输出约定，例如：

- `MAPE Accuracy = 1 - MAPE`
- 基于 eval mask 的异常点过滤
- 预测上下文保存
- 预测绘图拼接数据

待评审问题：

- 这些是否进入新框架核心？
- 还是先作为 business profile / evaluation plugin 存在？

建议默认：MVP 只用 UtilsForecast 和通用指标做可对比评估；业务 mask 和 MAPE Accuracy 作为后续 business profile，不硬编码到核心默认行为。

### 4.4 NeuralForecast 与本地 LTSFM 后端边界

待评审问题：

- NeuralForecast 与本地 LTSFM 是否共享一套后端协议？
- 是否拆为 `neural` 后端与 `foundation_local` 后端？

建议默认：MVP 只接 NeuralForecast。它是 Nixtla 生态的可训练神经网络后端；本地 LTSFM 和 TimeGPT 都放到后续 foundation model 阶段。

### 4.5 HierarchicalForecast 接入边界

待评审问题：

- 当前是否已有明确层级预测业务，例如园区/楼栋/房间/设备、产品/区域/门店？
- 是否需要 coherent forecast reconciliation？

建议默认：MVP 使用 Nixtla 官方 `TourismSmall` 示例数据验证 HierarchicalForecast，不强行把 ETT 转成层级数据。未来只有当业务数据存在明确层级聚合口径时，再接入业务层级预测。

### 4.6 配置系统复杂度

待评审问题：

- 配置使用单一 YAML 文件，还是支持 Python config、YAML、CLI override 多源合并？
- 是否保留 `tsproj_ml` 的 grouped YAML 风格？

建议默认：MVP 使用单一 YAML。后续接入业务 profile 或 legacy adapter 时再考虑兼容转换器，不把旧 YAML 结构作为新框架唯一格式。

## 5. 推荐总体架构

推荐新框架作为独立 Python 包，包名与当前仓库保持一致：`tsforecasting`。

当前仓库已经落地的结构：

```text
tsforecasting/
  .gitignore
  .python-version
  CLAUDE.md
  LICENSE
  README.md
  docs/
    unified-ts-framework-plan-v1.md
    PLAN.md
    LOG.md
  pyproject.toml
  utils/
    log_util.py
  uv.lock
```

当前尚未创建 `src/`、`configs/`、`examples/`、`tests/`、运行入口、测试套件或 linter。下面是 Nixtla-only MVP 建议补齐的目标结构。

当前 `pyproject.toml` 已确认：

- `name = "tsforecasting"`
- `requires-python = ">=3.12"`
- 已有基础依赖：`matplotlib`、`numpy`、`pandas`、`scikit-learn`、`scipy`、`statsmodels`
- 尚未加入 MVP 需要的 Nixtla 生态依赖
- 尚未配置 dev 依赖、测试运行器或 linter

建议目录结构：

```text
tsforecasting/
  pyproject.toml
  README.md
  AGENTS.md
  CLAUDE.md
  configs/
    examples/
      ett_small_stats_ml_neural.yaml
      tourism_small_hierarchical.yaml
  examples/
    ett_small/
    tourism_small/
  src/
    tsforecasting/
      cli/
      config/
      data/
      features/
      splitting/
      backtesting/
      models/
        base.py
        registry.py
        nixtla/
          stats.py
          ml.py
          neural.py
      hierarchical/
      evaluation/
      artifacts/
      reporting/
      visualization/
      orchestration/
  utils/
    log_util.py
    data_utils.py
    datetime_utils.py
    io_utils.py
  reports/
    notebooks/
    {run_id}/
  tests/
    unit/
    integration/
  docs/
```

### 5.1 数据层 `data/`

职责：

- 读取 CSV、Parquet、Nixtla 示例数据等数据源。
- 识别或显式指定时间列、目标列、序列 ID 列。
- 转换为内部标准长表：`unique_id / ds / y`。
- 校验时间戳可解析、频率可推断或已配置、重复时间戳、缺失值、时间间隔连续性。
- 管理静态特征、历史外生、未来外生的字段声明。
- 对 HierarchicalForecast 示例额外加载 `Y_df / S_df / tags`。

默认规则：

- 单序列数据如果没有 `id_col`，自动补 `unique_id = "series_0"`。
- `time_col` 映射为 `ds`。
- `target_col` 映射为 `y`。
- 原始列名、频率、字段映射保存在 manifest 中，便于追溯。

### 5.2 特征层 `features/`

职责：

- 定义 feature spec，而不是一开始实现所有特征逻辑。
- 支持 date features、lag features、lag transforms、target transforms、future exogenous、historic exogenous、static features 的声明。
- 对 MLForecast 优先映射到原生 lags、lag transforms、date features、target transforms。
- 对 NeuralForecast 优先映射到原生 static、historic、future exogenous 配置。
- StatsForecast 只接收其支持的 exogenous 和模型参数，不强行套用 ML 特征语义。

不建议第一阶段做庞大的通用 FeatureEngineer。MVP 只需要把特征声明和后端原生能力打通。

### 5.3 切分与回测层 `splitting/`、`backtesting/`

职责：

- 统一 train/valid/test 切分。
- 统一 rolling backtest 参数：`horizon`、`n_windows`、`step_size`、`cutoff`。
- 执行时优先调用 StatsForecast、MLForecast、NeuralForecast 的原生 `cross_validation`。
- 将各框架的 wide output 转换为统一 long result。

标准回测输出至少包含：

```text
unique_id, cutoff, ds, horizon, y, yhat, model, run_id
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

MVP 后端类型：

- `models/nixtla/stats.py`：StatsForecast adapter。
- `models/nixtla/ml.py`：MLForecast adapter。
- `models/nixtla/neural.py`：NeuralForecast adapter。

不进入 MVP 的后端：

- TimeGPT。
- `tsproj_stat`、`tsproj_ml`、`tsproj_dl`、`tsproj_ltsfm` legacy adapter。
- 本地 LTSFM / foundation model adapter。

### 5.5 层级预测层 `hierarchical/`

职责：

- 作为 forecast 后的 reconciliation stage，而不是普通模型后端。
- 使用 `Y_df / S_df / tags` 表达层级结构。
- 接收 base forecasts，调用 HierarchicalForecast 生成 reconciled forecasts。
- 保存 coherence diagnostics，用于验证 reconciliation 是否让预测满足层级约束。

MVP 示例使用 Nixtla 官方 `TourismSmall` 数据。ETT 主线不进入层级 reconciliation。

### 5.6 训练、预测与编排层 `orchestration/`

职责：

- 编排数据加载、配置解析、后端实例化、fit、predict、cross_validate、evaluate、save artifacts。
- 不直接实现复杂模型训练逻辑。
- 负责调用后端、收集结果、传递 runtime profile。
- 根据配置决定执行 ETT 普通预测主线或 TourismSmall 层级验证主线。

编排层不应持有业务指标或业务数据清洗规则。业务规则应放在后续 business profile 中。

### 5.7 评估与可视化层 `evaluation/`、`visualization/`

通用评估优先使用 UtilsForecast：

- MAE
- RMSE
- MAPE
- SMAPE
- MASE
- pinball loss
- interval coverage
- interval width

可视化优先使用 UtilsForecast：

- 单序列和多序列 `plot_series`
- 回测窗口对比图
- 模型误差对比图
- 层级 reconciliation 前后对比图

R2、业务 mask、`MAPE Accuracy = 1 - MAPE` 等不进入 MVP 默认指标，后续作为 business profile 补充。

### 5.8 结果管理层 `artifacts/`

每次运行建议生成：

```text
runs/{run_id}/
  run_config.yaml
  manifest.json
  predictions.csv
  backtest_predictions.csv
  metrics.json
  metrics.csv
  runtime_metrics.json
  runtime_metrics.csv
  model_comparison.csv
  plots/
  model/
  logs/
```

层级验证运行额外生成：

```text
runs/{run_id}/
  base_predictions.csv
  reconciled_predictions.csv
  reconciliation_diagnostics.csv
```

运行性能指标至少包含：

```text
run_id, backend, model, model_type, n_series, n_rows, fit_seconds, predict_seconds, cross_validation_seconds, total_seconds
```

`manifest.json` 应记录：

- run id
- timestamp
- framework version
- config path
- run command
- input data path 或 Nixtla 示例数据名称
- original column mapping
- canonical data columns
- model backend
- model parameters
- split/backtest settings
- feature spec
- output files
- log path
- report path
- selected environment variables
- environment summary

### 5.9 工程规范与注释规则

代码实现应遵循以下规则：

- 代码保持整洁、可读、职责单一，避免把数据、模型、评估、保存逻辑混在一个函数中。
- 大的功能实现优先使用类封装多个相关方法，例如 backend adapter、orchestrator、artifact writer、report builder。
- 公共模块、类、函数和变量命名使用英文，保证 Python 生态兼容和可搜索性。
- 类、方法使用中文 docstring，说明职责、输入、输出和关键约束。
- 关键步骤和关键变量使用中文注释，解释“为什么这样做”和领域含义，避免逐行翻译代码。
- 对外部契约、字段含义、时间窗口、外生变量类型、指标口径等容易误用的地方必须写注释。
- 不为单次使用逻辑过早抽象；当同一模式在两个以上模块重复出现时再抽公共能力。

### 5.10 日志系统 `utils/log_util.py`

当前仓库已经有项目级日志模块 `utils/log_util.py`。后续实现应基于该模块构建日志系统：

- 各模块统一复用 `utils.log_util.logger`，不要在业务模块中重复创建 handler。
- 日志级别由环境变量 `SERVICE_LOG_LEVEL` 控制。
- 运行名称由环境变量 `LOG_NAME` 控制，日志默认输出到 `logs/{LOG_NAME}/service*`。
- 编排层必须记录配置加载、数据校验、模型开始与结束、运行耗时、artifact 输出路径和异常堆栈。
- 每次运行的 `manifest.json` 记录日志路径和关键环境变量摘要。
- notebook/reporting 中只读取运行结果，不重新配置 logger。

### 5.11 项目级工具模块 `utils/`

`utils/` 用于管理跨数据项目复用的项目级工具函数，不承载模型训练业务逻辑。

建议边界：

- `utils/log_util.py`：日志配置和全局 logger。
- `utils/data_utils.py`：通用数据字段检查、列名清洗、基础 DataFrame 工具。
- `utils/datetime_utils.py`：时间戳解析、频率推断、时间范围校验。
- `utils/io_utils.py`：路径创建、CSV/JSON/YAML 读写薄封装。

`src/tsforecasting/` 内部模块可以调用 `utils/` 的通用能力，但核心业务流程仍应放在包内对应层次中。

### 5.12 报告输出层 `reporting/`

报告模块用于汇总模型运行结果，优先兼容 Jupyter Lab。

职责：

- 读取 `manifest.json`、`metrics.csv`、`runtime_metrics.csv`、`model_comparison.csv`、`predictions.csv`、`backtest_predictions.csv`。
- 汇总模型准确率、运行速度、预测曲线、回测表现、最佳模型排序、运行配置和 artifact 路径。
- 生成 Jupyter notebook 报告输入数据，并支持将模板 notebook 保存到 `reports/{run_id}/`。
- 报告输出可包含 `.ipynb`、`.html`，PDF 作为后续扩展。

建议目录：

```text
reports/
  notebooks/
    model_comparison_template.ipynb
  {run_id}/
    model_comparison.ipynb
    model_comparison.html
```

## 6. Nixtla 生态兼容方案

本节从第 5 节总体架构出发，说明每个 Nixtla 框架在 `tsforecasting` 中承担的模块职责。

### 6.1 Nixtla 模型与方法目录

本框架需要把 Nixtla 官方支持的模型和方法完整纳入 catalog，但 MVP 不要求把全部模型逐一跑通。MVP 只启用少量 smoke preset，完整目录用于后续配置发现、能力对照和逐步扩展。

StatsForecast 模型目录：

- ADIDA
- ARCH / GARCH
- ARIMA / AutoARIMA
- AutoCES
- AutoETS
- AutoRegressive
- AutoTheta
- CrostonClassic / CrostonOptimized / CrostonSBA
- DynamicOptimizedTheta / DynamicStandardTheta
- HistoricAverage
- Holt / HoltWinters
- IMAPA
- MFLES
- MSTL
- Naive / SeasonalNaive
- OptimizedTheta / StandardTheta
- SeasonalExponentialSmoothing / SeasonalExponentialSmoothingOptimized
- SimpleExponentialSmoothing / SimpleExponentialSmoothingOptimized
- Theta
- TSB

MLForecast 模型目录：

- 不维护固定的第三方模型全集。
- 支持任何符合 scikit-learn `fit` / `predict` API 的 regressor。
- MVP 内置 sklearn preset：`LinearRegression`、`Ridge`、`Lasso`、`ElasticNet`、`RandomForestRegressor`、`HistGradientBoostingRegressor`。
- 后续可通过 import path 接入 LightGBM、XGBoost、CatBoost 或用户自定义 sklearn-compatible estimator。

NeuralForecast 模型目录：

- Autoformer / AutoAutoformer
- BiTCN / AutoBiTCN
- DeepAR / AutoDeepAR
- DeepNPTS
- DilatedRNN / AutoDilatedRNN
- FEDformer / AutoFEDformer
- GRU / AutoGRU
- HINT
- Informer / AutoInformer
- iTransformer / AutoiTransformer
- KAN / AutoKAN
- LSTM / AutoLSTM
- MLP / AutoMLP
- MLPMultivariate / AutoMLPMultivariate
- NBEATS / AutoNBEATS
- NBEATSx / AutoNBEATSx
- NHITS / AutoNHITS
- NLinear / AutoNLinear
- PatchTST / AutoPatchTST
- RMoK / AutoRMoK
- RNN / AutoRNN
- SOFTS / SOFTSSharp
- StemGNN
- TCN / AutoTCN
- TFT / AutoTFT
- TiDE / AutoTiDE
- TimeMixer / AutoTimeMixer
- TimeLLM
- TimesNet / AutoTimesNet
- TimeXer / AutoTimeXer
- TSMixer / AutoTSMixer
- TSMixerx / AutoTSMixerx
- VanillaTransformer / AutoVanillaTransformer
- XLinear / AutoXLinear
- xLSTM / AutoxLSTM

HierarchicalForecast 方法目录：

- BottomUp
- TopDown
- MiddleOut
- MinTrace
- ERM
- Normality
- Bootstrap
- PERMBU
- Conformal
- Temporal reconciliation

HierarchicalForecast 方法不进入普通 model backend registry，而进入 `hierarchical/` reconciliation catalog。

UtilsForecast 工具目录：

- evaluation：统一评估入口。
- losses：MAE、RMSE、MAPE、SMAPE、MASE 等指标函数。
- plotting：`plot_series` 等绘图工具。
- preprocessing：`fill_gaps` 等时间序列预处理工具。

UtilsForecast 不作为模型后端，只作为 `evaluation/`、`visualization/`、`data/` 预处理工具层。

### 6.2 模型纳入方式与原生 API 优先原则

建议建立 `model catalog / registry`，用于记录 Nixtla 官方支持模型、MVP preset 和后续扩展状态。catalog 至少包含以下字段：

```text
backend, model_name, class_path, model_type, family, supports_exog,
supports_probabilistic, dependency_group, mvp_preset, source_url, status
```

字段含义：

- `backend`：`statsforecast`、`mlforecast`、`neuralforecast`、`hierarchicalforecast`、`utilsforecast`。
- `model_name`：配置中使用的稳定名称。
- `class_path`：Nixtla 原生类路径或用户指定 estimator import path。
- `model_type`：`statistical`、`machine_learning`、`deep_learning`、`reconciliation`、`utility`。
- `family`：模型族，例如 ARIMA、ETS、Croston、Transformer、RNN、Reconciliation。
- `supports_exog`：是否支持外生变量；需要区分 static、historic、future。
- `supports_probabilistic`：是否支持概率预测或区间输出。
- `dependency_group`：依赖组，例如 core、ml、torch、hierarchical、api。
- `mvp_preset`：是否进入 MVP smoke 配置。
- `source_url`：对应官方文档或模型引用页。
- `status`：`cataloged`、`mvp_smoke`、`validated`、`blocked`、`deprecated`。

纳入规则：

- catalog 覆盖 Nixtla 官方支持模型和 reconciliation 方法。
- MVP 只启用少量 smoke preset，避免把全模型验证变成第一阶段阻塞项。
- StatsForecast 和 NeuralForecast 的 catalog 记录官方模型类；实现层按配置动态实例化。
- MLForecast 支持两类入口：内置 sklearn preset，以及用户通过 import path 指定的 sklearn-compatible estimator。
- HierarchicalForecast 只进入 reconciliation catalog，不和普通预测模型混在同一个 backend 列表中。
- UtilsForecast 只进入 utility API catalog，不参与模型排行榜。

原生 API 优先原则：

- StatsForecast：训练、预测、`forecast`、`cross_validation`、概率区间优先调用原生 API。
- MLForecast：lags、lag transforms、date features、target transforms、exogenous、`cross_validation` 优先调用原生 API。
- NeuralForecast：模型训练、预测、`cross_validation`、exogenous、save/load 优先调用原生 API。
- HierarchicalForecast：reconciliation、coherence diagnostics 优先调用原生 API。
- UtilsForecast：`evaluate`、losses、`plot_series`、`fill_gaps` 优先调用原生 API。

`tsforecasting` 本层只负责：

- 配置解析与 schema 校验。
- 输入字段映射与 canonical frame 校验。
- Nixtla 原生参数组装。
- 输出字段标准化。
- runtime metrics、日志、artifact、manifest、reporting。

实现时不重复构建 Nixtla 已经提供的训练、特征生成、回测、评估、绘图、reconciliation 能力。代码注释需要标明“调用的 Nixtla 原生 API”和“本层只做的适配职责”，便于后续 Agent 判断边界。

### 6.3 StatsForecast：统计模型、基线和快速 backtest

定位：统计模型后端和强基线后端。

适合模型：

- SeasonalNaive
- Naive
- HistoricAverage
- AutoETS
- AutoARIMA
- AutoTheta
- MSTL
- Croston
- GARCH / ARCH 等

接入方式：

- 输入使用 `unique_id / ds / y` 长表。
- 使用 StatsForecast 原生 `fit`、`predict`、`forecast`、`cross_validation`。
- 对 ETT smoke 优先使用 `SeasonalNaive`、`AutoETS`、轻量 `AutoARIMA`。
- 输出转换为统一 `ForecastFrame` / `BacktestFrame`。

主要用于验证：统计基线、季节性设置、快速滚动回测、概率区间基础能力。

### 6.4 MLForecast：lag/date/target transform 与 sklearn regressor

定位：机器学习模型后端。

适合模型：

- LinearRegression
- Ridge / Lasso / ElasticNet
- RandomForestRegressor
- HistGradientBoostingRegressor
- 后续可选 LightGBM、XGBoost、CatBoost

接入方式：

- 输入使用 `unique_id / ds / y` 长表。
- lags、lag transforms、date features、target transforms 优先映射到 MLForecast 原生参数。
- MVP 默认先使用 scikit-learn 内置模型，避免为了 smoke test 额外引入 LightGBM。
- 模型参数保留 sklearn 风格。
- 输出转换为统一 `ForecastFrame` / `BacktestFrame`。

主要用于验证：机器学习回归器的特征生成、目标变换、滚动窗口防泄漏、全局模型对多序列的支持。

### 6.5 NeuralForecast：深度学习预测后端

定位：Nixtla 生态内的可训练神经网络预测后端。

适合模型：

- NHITS
- NBEATS
- TFT
- PatchTST
- LSTM / RNN / TCN
- Informer / Transformer 类模型

接入方式：

- 输入使用 `unique_id / ds / y` 长表。
- 支持 static、historic、future exogenous 的后端原生配置。
- MVP 默认使用小规模 `NHITS` 或 `NBEATS`，CPU smoke 配置，并限制训练步数。
- 输出转换为统一 `ForecastFrame` / `BacktestFrame`。

主要用于验证：深度学习模型的训练/验证拆分、概率预测、外生变量语义、与自有 `tsproj_dl` 的后续能力对照。

### 6.6 HierarchicalForecast：层级 reconciliation 验证

定位：层级预测 reconciliation 层，不是基础模型层。

接入方式：

- 使用 Nixtla 官方 `TourismSmall` 示例数据。
- 输入包含 `Y_df / S_df / tags`。
- 先由 StatsForecast 生成 base forecasts。
- 再由 HierarchicalForecast 执行 BottomUp、TopDown、MiddleOut、MinTrace 等 reconciliation。
- 保存 reconciled forecasts 和 coherence diagnostics。

主要用于验证：层级一致性、reconciliation 前后误差变化、层级预测 artifact 结构。

### 6.7 UtilsForecast：评估、losses、绘图和预处理

定位：通用工具层。

MVP 用途：

- `evaluate` 统一计算模型指标。
- `losses` 提供 MAE、RMSE、MAPE、SMAPE、MASE 等指标函数。
- `plot_series` 生成标准序列图和预测对比图。
- `fill_gaps` 等预处理工具用于时间戳连续性补齐或显式暴露缺失。

主要用于验证：不同后端的评估口径一致性、绘图口径一致性、缺失时间点处理口径。

### 6.8 TimeGPT：后续 API / foundation model 阶段

定位：远程 foundation model / API 后端。

后续接入前需要单独设计：

- 是否允许真实 API 调用。
- mock / dry-run client。
- `NIXTLA_API_KEY` 管理。
- 成本、超时、重试、日志脱敏。
- 与本地 LTSFM / foundation model 的对比维度。

TimeGPT 不进入 MVP。

## 7. 自有四个项目的架构诊断维度

MVP 不接入 `tsproj_stat`、`tsproj_ml`、`tsproj_dl`、`tsproj_ltsfm`。它们在本阶段只用于和 Nixtla 生态做架构诊断。

### 7.1 `tsproj_stat`

诊断重点：

- 与 StatsForecast 的统计模型覆盖、速度、概率区间、cross-validation 能力对比。
- 当前 `fit(y, X_hist=None, X_future=None) / predict_one(X_future_one=None)` 契约是否需要向 Nixtla 长表收敛。
- `saved_results/` 输出是否能映射到统一 artifact。

### 7.2 `tsproj_ml`

诊断重点：

- 自有特征工程与 MLForecast 原生 lags、lag transforms、date features、target transforms 的重叠和差异。
- YAML/dataclass 配置是否存在隐式字段、业务字段和模型字段混杂。
- 回测、预测上下文、业务指标是否可拆成 core evaluation 与 business profile。

### 7.3 `tsproj_dl`

诊断重点：

- 与 NeuralForecast 在训练/验证拆分、模型接口、概率预测、外生变量支持上的差异。
- `run.py` / argparse 实验流程是否能被更清晰的 config + artifact contract 替代。
- PyTorch 实验结果是否具备统一 metrics、plots、manifest。

### 7.4 `tsproj_ltsfm`

诊断重点：

- 本地 foundation model 推理流程与 TimeGPT / 后续 API 后端的接口共性。
- 本地/A100 两级实验策略是否应保留为 runtime profile。
- 预训练模型结果是否能统一到 predictions、metrics、summary、plot、manifest。

### 7.5 共用诊断问题

- 数据契约是否显式，还是分散在 loader、config、model 中。
- 回测窗口是否严格防止未来数据泄漏。
- 外生变量在历史/未来/静态三个类别中的归属是否清晰。
- 指标是否能复现，是否区分通用指标和业务指标。
- 结果目录是否能支撑模型对比、复盘和审计。
- 依赖是否能隔离，是否有必要把重依赖移出核心环境。

## 8. 阶段性实施路线

### 阶段 1：Nixtla-only MVP

目标：

- 在当前 `tsforecasting` 独立仓库内补齐 MVP 基础工程结构。
- 实现内部长表数据契约。
- 使用 ETT 小数据跑通 StatsForecast、MLForecast、NeuralForecast 三类后端。
- 使用 UtilsForecast 固定评估、绘图、预处理口径。
- 使用 TourismSmall 跑通 HierarchicalForecast reconciliation 验证。
- 固定配置、评估、运行耗时、日志、报告和结果落盘契约。

核心任务：

- 创建 `src/tsforecasting/` 基础包结构。
- 按需加入 `statsforecast`、`mlforecast`、`neuralforecast`、`hierarchicalforecast`、`utilsforecast`、`datasetsforecast` 并刷新 `uv.lock`。
- 定义 YAML schema。
- 建立 Nixtla model catalog / registry，先 catalog 全量官方模型和方法，再只启用 MVP smoke preset。
- 实现数据读取与 canonical frame 转换。
- 实现 StatsForecast adapter。
- 实现 MLForecast adapter。
- 实现 NeuralForecast adapter。
- 实现 HierarchicalForecast reconciliation stage。
- 实现 UtilsForecast evaluation / plotting wrapper。
- 在 adapter 注释中标明调用的 Nixtla 原生 API，以及 `tsforecasting` 只负责的适配职责。
- 实现统一 artifact writer 和 manifest writer。
- 基于 `utils.log_util.logger` 接入统一日志。
- 记录模型级 runtime metrics，并生成 `model_comparison.csv`。
- 实现 reporting 模块和 Jupyter Lab notebook 报告模板。
- 提供 `ett_small_stats_ml_neural.yaml` 和 `tourism_small_hierarchical.yaml` smoke examples。
- 每次实施后更新 `docs/PLAN.md` 的计划项实现记录；如涉及范围、架构或 MVP 边界变化，再更新本文档的方案调整记录。

验收标准：

- 同一份 ETT 数据可以通过 StatsForecast、MLForecast、NeuralForecast 运行。
- model catalog 覆盖 Nixtla 官方模型和方法目录，MVP preset 与完整支持目录明确区分。
- 生成统一的 `predictions.csv`、`backtest_predictions.csv`、`metrics.json`、`runtime_metrics.csv`、`model_comparison.csv`、`manifest.json`。
- UtilsForecast 统一产出至少 `mae / rmse / mape / smape`。
- TourismSmall 示例能产出 `base_predictions.csv`、`reconciled_predictions.csv`、`reconciliation_diagnostics.csv`。
- manifest 能记录配置来源、运行命令、日志路径、报告路径和关键环境变量摘要。
- `reports/{run_id}/` 能生成 Jupyter Lab 可打开的模型对比 notebook。
- `docs/PLAN.md` 的计划项实现记录包含已完成模块、验证命令、产物路径和下一步。

### 阶段 2：Nixtla 能力扩展与诊断报告

目标：

- 扩展更多 StatsForecast、MLForecast、NeuralForecast 模型。
- 形成与四个自有项目的架构诊断报告。
- 固化模型对比和报告输出。

核心任务：

- 根据 catalog status 分批把模型从 `cataloged` 推进到 `validated`。
- 增加更多统计基线和机器学习模型配置。
- 增加 NeuralForecast 概率预测和外生变量示例。
- 形成 `docs/` 下的自有框架诊断文档。
- 增加模型排行榜、速度/准确率对比和报告导出。

验收标准：

- 能用统一 artifact 对比统计、机器学习、神经网络模型。
- 诊断报告能明确指出自有框架的可保留能力、验证风险和优化方向。

### 阶段 3：业务数据与 business profile

目标：

- 接入 AIDC demand_load 等业务数据场景。
- 引入业务评估 profile。
- 固化更完整的可追溯 artifact。

核心任务：

- 增加宽表业务 CSV 到长表的 adapter。
- 支持历史外生和未来外生。
- 增加 demand load evaluation profile。
- 增加预测上下文和绘图数据保存。

验收标准：

- AIDC demand_load 可以通过至少一个 Nixtla 后端跑通。
- 输出能满足业务复盘和领导汇报所需字段。

### 阶段 4：TimeGPT 与 legacy adapter

目标：

- 接入 TimeGPT。
- 评估是否按顺序接入 `tsproj_stat -> tsproj_ml -> tsproj_dl -> tsproj_ltsfm`。

核心任务：

- TimeGPT real client 和 mock client。
- API key、成本、超时、重试、日志脱敏策略。
- 按诊断结果决定 legacy adapter 的必要性和边界。

验收标准：

- TimeGPT 可在显式 opt-in 下运行。
- legacy adapter 只接入确有复用价值的历史能力，不把旧项目约定反向污染核心契约。

## 9. 关键风险与不宜过早抽象的部分

### 9.1 关键风险

- Nixtla 依赖范围扩大：NeuralForecast 会引入深度学习依赖，需要控制 smoke 配置和运行时间。
- 数据契约漂移：ETT 长表、TourismSmall 层级表、业务宽表之间容易出现隐式转换错误。
- 回测口径不一致：不同后端原生 cross-validation 输出列形态不同，需要统一转换。
- 指标口径不一致：UtilsForecast 通用指标与业务 mask 指标需要清晰分层。
- 层级预测误用：没有明确层级结构的数据不应强行做 reconciliation。
- TimeGPT 外部依赖：API key、网络、成本、超时、重试都会影响稳定性，因此不进入 MVP。
- 结果保存不统一：如果 artifact 契约不先固定，后续模型对比和 legacy 迁移会反复返工。

### 9.2 不宜过早抽象

第一阶段不建议做：

- 通用 Trainer 大抽象。
- 通用 FeatureEngineer 大抽象。
- 全模型统一超参搜索。
- 全任务统一 Task 系统。
- 分布式训练。
- 本地 foundation model 管理平台。
- 完整 AutoML。
- legacy adapter。

建议只在真实重复出现后再抽象：

- 两个以上 Nixtla 后端共享同一外部逻辑。
- 两个以上业务场景需要同一评估 profile。
- 多个 adapter 产出相同 artifact 转换逻辑。

## 10. 当前方案草案

### 10.1 参数配置与运行方式契约

MVP 主配置方式为单一 YAML 文件。CLI 是主运行入口，Python API 只作为 notebook 和调试辅助入口。

建议 CLI 命令：

```bash
uv run tsforecasting validate-config --config configs/examples/ett_small_stats_ml_neural.yaml
uv run tsforecasting run --config configs/examples/ett_small_stats_ml_neural.yaml
uv run tsforecasting backtest --config configs/examples/ett_small_stats_ml_neural.yaml
uv run tsforecasting predict --config configs/examples/ett_small_stats_ml_neural.yaml
uv run tsforecasting hierarchical --config configs/examples/tourism_small_hierarchical.yaml
uv run tsforecasting report --run-id <run_id>
```

MVP 只允许少量运行级 CLI override：

```text
--run-id
--output-dir
--log-name
--log-level
--dry-run
```

暂不支持 Python config、多 YAML 合并、复杂 CLI override。

### 10.2 ETT 小数据配置草案

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
    window_mode: rolling

features:
  date_features: [hour, dayofweek]
  lags: [1, 24, 48]
  lag_transforms: []
  target_transforms: []
  static_features: []
  historic_exog: []
  future_exog: []

models:
  - name: seasonal_naive
    backend: statsforecast
    params:
      season_length: 24
  - name: auto_ets
    backend: statsforecast
    params:
      season_length: 24
  - name: linear_regression
    backend: mlforecast
    params: {}
  - name: random_forest
    backend: mlforecast
    params:
      n_estimators: 100
      random_state: 42
  - name: nhits_smoke
    backend: neuralforecast
    params:
      input_size: 48
      max_steps: 50
      random_seed: 42

evaluation:
  metrics: [mae, rmse, mape, smape]
  engine: utilsforecast

runtime:
  collect_timing: true
  log_name: ett_small_mvp
  log_level: INFO

artifacts:
  output_dir: runs/ett_small_stats_ml_neural
  save_plots: true

reporting:
  enabled: true
  template: reports/notebooks/model_comparison_template.ipynb
  output_dir: reports/ett_small_stats_ml_neural
```

### 10.3 TourismSmall 层级配置草案

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
    - bottom_up
    - top_down_forecast_proportions
    - middle_out
  diagnostics: true

evaluation:
  metrics: [mse]
  engine: utilsforecast

runtime:
  collect_timing: true
  log_name: tourism_small_hierarchical
  log_level: INFO

artifacts:
  output_dir: runs/tourism_small_hierarchical
  save_plots: true

reporting:
  enabled: true
  template: reports/notebooks/model_comparison_template.ipynb
  output_dir: reports/tourism_small_hierarchical
```

### 10.4 ETT 典型运行流程

```text
load_config
  -> load_raw_data
  -> convert_to_canonical_frame(unique_id/ds/y)
  -> validate_frequency_and_missing_values
  -> resolve_feature_spec
  -> build_split_or_backtest_windows
  -> resolve_nixtla_backend
  -> call_native_fit_predict_or_cross_validation
  -> normalize_forecast_outputs
  -> collect_runtime_metrics
  -> evaluate_with_utilsforecast
  -> save_artifacts
  -> build_report_inputs
  -> write_manifest
```

### 10.5 层级典型运行流程

```text
load_config
  -> load_tourism_small(Y_df/S_df/tags)
  -> split_train_test
  -> generate_base_forecasts_with_statsforecast
  -> reconcile_with_hierarchicalforecast
  -> compute_coherence_diagnostics
  -> evaluate_with_utilsforecast
  -> save_artifacts
  -> build_report_inputs
  -> write_manifest
```

### 10.6 标准预测输出

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

运行指标输出：

```text
run_id, backend, model, model_type, n_series, n_rows, fit_seconds, predict_seconds, cross_validation_seconds, total_seconds
```

模型对比输出至少包含：

```text
run_id, backend, model, model_type, mae, rmse, mape, smape, total_seconds, rank_metric, rank
```

### 10.7 标准结果目录

```text
runs/{run_id}/
  run_config.yaml
  manifest.json
  predictions.csv
  backtest_predictions.csv
  metrics.json
  metrics.csv
  runtime_metrics.json
  runtime_metrics.csv
  model_comparison.csv
  plots/
  model/
  logs/
```

层级验证目录额外包含：

```text
runs/{run_id}/
  base_predictions.csv
  reconciled_predictions.csv
  reconciliation_diagnostics.csv
```

报告输出目录：

```text
reports/{run_id}/
  model_comparison.ipynb
  model_comparison.html
```

### 10.8 当前默认假设

- 新框架、仓库和 Python 项目名统一为 `tsforecasting`。
- MVP 只做 forecasting。
- MVP 数据使用 ETT 小数据和 TourismSmall 层级示例数据。
- MVP 可运行主线为 StatsForecast、MLForecast、NeuralForecast。
- UtilsForecast 进入 MVP，作为评估、绘图、预处理工具层。
- HierarchicalForecast 进入 MVP 的独立层级验证流程，不作为普通模型后端。
- TimeGPT 不进入 MVP，只作为后续 API / foundation model 阶段规划。
- 四个自有项目不进入 MVP，只作为架构诊断对象。
- MVP 主配置方式为单一 YAML，主运行入口为 CLI。
- 报告模块以 Jupyter Lab / notebook 为主，HTML/PDF 导出作为后续扩展。

## 11. 方案调整记录

后续任何范围变化必须先追加本节记录，再修改对应章节，避免不同 Agent 在多阶段实施中丢失设计上下文。

| date | change | reason | impact |
| --- | --- | --- | --- |
| 2026-06-22 | 将方案文档固化为 v1 基线 | 后续方案修改需要保留历史版本，避免覆盖已确认设计 | 当前文件重命名为 `docs/unified-ts-framework-plan-v1.md`；后续方案变更应生成 v2/v3 文档 |
| 2026-06-22 | 拆分开发日志和执行计划文档 | 方案文档应只记录架构方案和方案变更，开发日志与计划实现记录需要独立维护 | 新增 `docs/LOG.md`、`docs/PLAN.md`；本文档不再维护任务执行进展 |
| 2026-06-22 | 项目命名从旧暂定名统一为 `tsforecasting` | 与当前 GitHub 仓库、Python 项目命名保持一致 | 包路径、文档、示例配置统一使用 `tsforecasting` |
| 2026-06-22 | MVP 主线从 StatsForecast、MLForecast、TimeGPT 调整为 StatsForecast、MLForecast、NeuralForecast | 先完整吸收 Nixtla 本地生态能力，再评估 API / foundation model | TimeGPT 移到后续阶段，不进入 MVP |
| 2026-06-22 | HierarchicalForecast 进入 MVP 的独立 TourismSmall 验证流程 | 层级预测需要 `Y_df / S_df / tags`，不应强行改造 ETT | `hierarchical/` 作为 forecast 后 reconciliation stage |
| 2026-06-22 | UtilsForecast 进入 MVP 工具层 | 统一评估、losses、绘图和预处理口径 | `evaluation/`、`visualization/`、`data/` 优先封装 UtilsForecast |
| 2026-06-22 | 增加 runtime metrics、model comparison、manifest、日志和 Jupyter Lab reporting 契约 | 支持同一数据多模型的速度、准确率和可追溯对比 | artifact 目录新增 `runtime_metrics.*`、`model_comparison.csv`、`reports/{run_id}/` |
| 2026-06-22 | 明确代码风格、中文注释规则、`utils/log_util.py` 复用和项目级 `utils/` 管理 | 降低后续多阶段实现的维护成本 | 复杂模块优先类封装，注释说明 Nixtla API 调用和本层适配职责 |
| 2026-06-22 | 增加 Nixtla 模型与方法 catalog、registry 纳入方式和原生 API 优先原则 | 需要把官方支持能力全部纳入框架，但不把全模型 smoke 作为 MVP 阻塞项 | catalog 覆盖官方模型和方法，MVP 只启用少量 preset，避免重复实现 Nixtla 已有能力 |

## 12. 参考资料

Nixtla 官方资料：

- Nixtlaverse: <https://nixtlaverse.nixtla.io/>
- StatsForecast: <https://nixtlaverse.nixtla.io/statsforecast/>
- StatsForecast model references: <https://nixtlaverse.nixtla.io/statsforecast/docs/models/autoarima.html>
- StatsForecast cross-validation: <https://nixtlaverse.nixtla.io/statsforecast/docs/tutorials/crossvalidation.html>
- MLForecast: <https://nixtlaverse.nixtla.io/mlforecast/>
- MLForecast cross-validation: <https://nixtlaverse.nixtla.io/mlforecast/docs/how-to-guides/cross_validation.html>
- NeuralForecast: <https://nixtlaverse.nixtla.io/neuralforecast/docs/getting-started/introduction.html>
- NeuralForecast forecasting models: <https://nixtlaverse.nixtla.io/neuralforecast/docs/capabilities/overview.html>
- NeuralForecast data requirements: <https://nixtlaverse.nixtla.io/neuralforecast/docs/getting-started/datarequirements.html>
- NeuralForecast cross-validation: <https://nixtlaverse.nixtla.io/neuralforecast/docs/capabilities/cross_validation.html>
- HierarchicalForecast: <https://nixtlaverse.nixtla.io/hierarchicalforecast/index.html>
- HierarchicalForecast TourismSmall example: <https://nixtlaverse.nixtla.io/hierarchicalforecast/examples/tourismsmall.html>
- UtilsForecast: <https://nixtlaverse.nixtla.io/utilsforecast/>
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
