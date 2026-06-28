# Unified TS Framework Plan v3

## 目标

v3 将 `tsforecasting` 主线收敛为 forecast-only 框架，聚焦 StatsForecast、MLForecast、NeuralForecast 三类模型的训练、验证、回测、预测、评估和报告。TourismSmall 层级协调功能暂停，历史代码、配置、脚本和测试保留在 `src/tsforecasting/todo/hierarchical/`，不参与活跃入口。

## 活跃入口

- `src/tsforecasting/main.py`
  - `ForecastRunner` 是本地运行与流程调试主类。
  - 阶段方法固定为 `parse_args -> load_data -> preprocess -> feature_engineering -> train -> valid -> test -> forecast -> run`。
  - `valid` 沿用 rolling-origin backtest；未配置独立 test split 时，`test` 在 manifest 中记录 skipped。
- `src/tsforecasting/main_cli.py`
  - `MainCLI` 是脚本和 console script 的入口类。
  - 支持 `validate-config`、`run`、`backtest`、`report`。
  - 不提供层级协调命令。

## 配置契约

YAML 使用 v2 schema：

```yaml
version: 2
task: forecast
data: {}
split: {}
models:
  statsforecast: []
  mlforecast:
    framework: {}
    models: []
  neuralforecast: []
evaluation: {}
forecast: {}
prediction_intervals: {}
runtime: {}
output: {}
```

解析链路固定为：

`YAML -> raw mapping -> ForecastArgs -> validate -> CLI overrides -> validate -> ForecastRunner`

`validate-config` 必须保持 metadata-only：校验 schema、registry 模型名和 backend mismatch，不读取数据、不 import optional backend、不实例化模型。

## 产物契约

每次运行写入 `output.dir/run_id/`：

- `config/run_config.yaml`
- `data/summary.json`
- `predictions/backtest.csv`
- `predictions/forecast.csv`（仅 `run` 且配置 `forecast`）
- `metrics/metrics.csv`
- `metrics/runtime.csv`
- `metrics/model_comparison.csv`
- `manifest.json`
- `reports/model_comparison.ipynb` / `.html`（由 report 命令生成）

`manifest.json` 必须记录 artifact 相对路径、模型 backend、区间列、阶段状态、配置来源、数据字段映射、日志路径和运行环境摘要。

## 类边界

- `ForecastRunner`：主流程编排。
- `MainCLI`：参数解析和命令分发。
- `ForecastArtifactWriter`：run-local artifact 写入。
- `ReportGenerator`：forecast run 报告生成。

无状态的 schema 校验、DataFrame 归一、指标计算和动态 import helper 继续保持函数式，以降低无意义类包装和测试成本。

## 当前非目标

- 不恢复层级协调。
- 不新增独立 test split 数据契约。
- 不改变 Nixtla adapter 的 predict/cross_validation 输出长表契约。
