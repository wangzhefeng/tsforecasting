# tsforecasting

`tsforecasting` 是基于 Nixtla 栈的统一时间序列预测框架。**MVP-0（StatsForecast 纵切面）已实现**：单 YAML 配置 → 校验 → CSV 转 Nixtla long table → `SeasonalNaive`/`AutoETS` 训练/回测 → UtilsForecast 统一评估 → 统一 artifacts + manifest。

## 当前状态

- Python 项目名 `tsforecasting`，Python `>=3.12`，包管理 `uv`。
- 源码在 `src/tsforecasting/`；CLI 入口 `tsforecasting`（`validate-config` / `run` / `backtest`）。
- Base 依赖：`statsforecast`、`utilsforecast`、`pyyaml`、`numpy`、`pandas`。
- Extras（MVP-1，尚未实现）：`ml` / `neural` / `hierarchical` / `plot`；dev 组：`pytest`、`ruff`。
- 依赖版本上限是硬约束：Nixtla 硬钉 `pandas<3`，numba（经 `statsforecast` 传递依赖）钉 `numpy<2.5`，升级前必须先做 spike。

## 快速开始

```bash
uv sync                                                                   # 安装 base + dev
uv run tsforecasting validate-config --config configs/examples/ett_small_stats.yaml
uv run tsforecasting run --config configs/examples/ett_small_stats.yaml   # 产物写到 runs/{run_id}/
uv run pytest                                                             # 测试
uv run ruff check .                                                       # lint
```

示例配置用小时级 `examples/ett_small/ETTh1.csv`（`freq: 1h` / `season_length: 24`）。`run` 默认跑回测 + 评估；配置含 `predict.horizon` 时额外产出 `predictions.csv`。运行级 override：`--run-id` / `--output-dir` / `--log-name` / `--log-level` / `--dry-run`。

## 产物（`runs/{run_id}/`）

`predictions.csv`、`backtest_predictions.csv`、`metrics.csv`、`runtime_metrics.csv`、`model_comparison.csv`、`manifest.json`、`run_config.yaml`（`metrics.json` 推迟到 MVP-0b）。

## 文档入口

- [docs/PLAN.md](docs/PLAN.md) — 可执行开发计划和计划项实现记录（MVP-0 P1–P6 done）。
- [docs/unified-ts-framework-plan-v2.md](docs/unified-ts-framework-plan-v2.md) — 当前实施基线（契约 / 架构）。
- [docs/unified-ts-framework-plan-v1.md](docs/unified-ts-framework-plan-v1.md) — v1 历史基线，**已被 v2 取代**，仅作设计史保留，勿据其 §5/§6 实施。
- [docs/LOG.md](docs/LOG.md) — 开发日志。

## MVP 方向

- MVP-0：StatsForecast `SeasonalNaive` / `AutoETS` 纵切面（已完成）。
- MVP-1：MLForecast、NeuralForecast CPU smoke、TourismSmall hierarchical reconciliation。
- Phase 2+：full Nixtla catalog、Jupyter reporting、TimeGPT、legacy adapter、本地 foundation model。
