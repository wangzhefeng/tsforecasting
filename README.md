# tsforecasting

基于 Nixtla 栈的统一时间序列预测框架。当前主线聚焦三类 forecast backend：`statsforecast`、`mlforecast`、`neuralforecast`；原 TourismSmall 层级协调功能已暂停并移入 `src/tsforecasting/todo/hierarchical/` 留作后续恢复参考。

## 当前状态

- Python 项目名 `tsforecasting`，Python `>=3.12`，包管理 `uv`。
- 本地调试入口：`src/tsforecasting/main.py`，核心类为 `ForecastRunner`。
- Shell/脚本入口：`src/tsforecasting/main_cli.py`，核心类为 `MainCLI`。
- CLI 命令：`validate-config` / `run` / `backtest` / `report`。
- Base 依赖：`statsforecast`、`utilsforecast`、`pyyaml`、`numpy`、`pandas`、`nbformat`。
- Extras：`ml`（MLForecast + scikit-learn）/ `neural`（NeuralForecast）/ `plot`（matplotlib）/ `report`（nbconvert/ipykernel，用于执行并导出 HTML）；dev 组：`pytest`、`ruff`。
- 依赖版本上限是硬约束：Nixtla 硬钉 `pandas<3`，numba（经 `statsforecast` 传递依赖）钉 `numpy<2.5`，升级前必须先做 spike。

## 快速开始

```bash
uv sync
uv run python -m tsforecasting.main_cli validate-config --config configs/examples/ett_small/stats.yaml
uv run python -m tsforecasting.main_cli run --config configs/examples/ett_small/stats.yaml
scripts/ett_small/run_stats.sh --dry-run
uv run pytest && uv run ruff check .
```

示例配置均基于小时级 `dataset/ett_small/ETTh1.csv`：

| 配置 | 说明 | 需 extra |
| --- | --- | --- |
| `ett_small/stats.yaml` | StatsForecast `SeasonalNaive`/`AutoETS` | base |
| `ett_small/ml.yaml` | 混合 StatsForecast + MLForecast | `ml` |
| `ett_small/neural.yaml` | 混合 StatsForecast + NeuralForecast NHITS（CPU smoke） | `neural` |
| `ett_small/intervals.yaml` | StatsForecast + 预测区间（levels 80/95） | base |
| `ett_small/intervals_mixed.yaml` | 三 backend + 预测区间（levels 80） | `neural` + `ml` |

运行级 override：`--run-id` / `--output-dir` / `--log-name` / `--log-level` / `--dry-run`。

## 配置与产物

YAML 使用 v2 schema：`version`、`task: forecast`、`data`、`split`、按 backend 分组的 `models`、`evaluation`、`forecast`、`prediction_intervals`、`runtime`、`output`。

`run` / `backtest` 输出到 `output.dir/run_id/`：

- `config/run_config.yaml`
- `data/summary.json`
- `predictions/backtest.csv`
- `predictions/forecast.csv`（仅 `run` 且配置 `forecast` 时）
- `metrics/metrics.csv`
- `metrics/runtime.csv`
- `metrics/model_comparison.csv`
- `manifest.json`
- `reports/model_comparison.ipynb`（由 `report` 生成，`--html` 额外导出 HTML）

`metrics.csv` 当前始终产出四个 core metrics：`mae`、`rmse`、`mape`、`smape`；`evaluation.metrics` 用于限定配置中的核心指标集合与 `rank_metric` 合法性，不作为输出筛选器。

## 文档入口

- [docs/PLAN.md](docs/PLAN.md) — 可执行开发计划与计划项实现记录。
- [docs/unified-ts-framework-plan-v3.md](docs/unified-ts-framework-plan-v3.md) — 当前架构基线。
- [docs/unified-ts-framework-plan-v2.md](docs/unified-ts-framework-plan-v2.md) — 历史实现基线。
- [docs/model_catalog.md](docs/model_catalog.md) — Nixtla model catalog。
- [docs/LOG.md](docs/LOG.md) — 开发日志。
