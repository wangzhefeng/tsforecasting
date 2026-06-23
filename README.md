# tsforecasting

基于 Nixtla 栈的统一时间序列预测框架。**MVP-0（StatsForecast 纵切面）与 MVP-1（MLForecast / NeuralForecast / HierarchicalForecast）已实现**，Phase 2 已交付 notebook reporting、full model catalog、概率预测/区间指标：单 YAML 配置 → 校验 → CSV 转 Nixtla long table → 训练/回测/协调 → UtilsForecast 统一评估 → 统一 artifacts + manifest。

## 当前状态

- Python 项目名 `tsforecasting`，Python `>=3.12`，包管理 `uv`。
- 源码在 `src/tsforecasting/`；CLI 入口 `tsforecasting`：
  - `validate-config` / `run` / `backtest` — MVP-0 多 backend 预测/回测，跨 backend 统一排名。
  - `reconcile` — P9 TourismSmall 层级协调（独立流程）。
  - `report` — P10 从 run artifacts 生成 notebook（`--html` 执行导出 HTML）。
- Base 依赖：`statsforecast`、`utilsforecast`、`pyyaml`、`numpy`、`pandas`。
- Extras：`ml`（MLForecast + scikit-learn）/ `neural`（NeuralForecast）/ `hierarchical`（HierarchicalForecast + datasetsforecast）/ `plot`（matplotlib）/ `report`（nbformat/nbconvert/ipykernel）；dev 组：`pytest`、`ruff`。**三 backend 均已实现**。
- 依赖版本上限是硬约束：Nixtla 硬钉 `pandas<3`，numba（经 `statsforecast` 传递依赖）钉 `numpy<2.5`，升级前必须先做 spike（见 `docs/LOG.md` P1）。

## 快速开始

```bash
uv sync                                                                   # base + dev
uv run tsforecasting validate-config --config configs/examples/ett_small_stats.yaml
uv run tsforecasting run --config configs/examples/ett_small_stats.yaml   # runs/{run_id}/
uv run pytest && uv run ruff check .
```

示例配置（均基于小时级 `examples/ett_small/ETTh1.csv`，`freq: 1h` / `season_length: 24`，TourismSmall 除外）：

| 配置 | 说明 | 需 extra |
| --- | --- | --- |
| `ett_small_stats.yaml` | StatsForecast `SeasonalNaive`/`AutoETS` | base |
| `ett_small_ml.yaml` | 混合 StatsForecast + MLForecast | `ml` |
| `ett_small_neural.yaml` | 混合 StatsForecast + NeuralForecast NHITS（CPU smoke） | `neural` |
| `ett_small_intervals_mixed.yaml` | 三 backend + 预测区间（levels 80） | `neural`+`ml` |
| `tourism_small_hierarchical.yaml` | TourismSmall 层级协调（季度） | `hierarchical` |

运行级 override：`--run-id` / `--output-dir` / `--log-name` / `--log-level` / `--dry-run`。

## 产物

- `run`/`backtest` → `runs/{run_id}/`：`predictions.csv`、`backtest_predictions.csv`、`metrics.csv`、`runtime_metrics.csv`、`model_comparison.csv`、`manifest.json`、`run_config.yaml`（含 `prediction_intervals` 时追加 `lo-/hi-` 列与 `coverage-/width-` 指标）。
- `reconcile` → `base_predictions.csv`、`reconciled_predictions.csv`、`reconciliation_diagnostics.csv`、`manifest.json`、`run_config.yaml`。
- `report` → `reports/{run_id}/model_comparison.ipynb`（或 `reconciliation.ipynb`），`--html` 额外导出 `.html`。

## 文档入口

- [docs/PLAN.md](docs/PLAN.md) — 可执行开发计划与计划项实现记录（**P1–P15 全 done**）。
- [docs/model_catalog.md](docs/model_catalog.md) — full Nixtla model catalog（78 条 stats/neural/ml 模型 + 来源 + 验证状态）。
- [docs/unified-ts-framework-plan-v2.md](docs/unified-ts-framework-plan-v2.md) — 当前实施基线（契约 / 架构）。
- [docs/unified-ts-framework-plan-v1.md](docs/unified-ts-framework-plan-v1.md) — v1 历史基线，**已被 v2 取代**，仅作设计史保留，勿据其 §5/§6 实施。
- [docs/LOG.md](docs/LOG.md) — 开发日志。

## 路线图

- MVP-0：StatsForecast `SeasonalNaive`/`AutoETS` 纵切面 — **完成**。
- MVP-1：MLForecast / NeuralForecast CPU smoke / TourismSmall hierarchical — **完成**。
- Phase 2：notebook reporting（`report`）✓、full model catalog ✓、概率预测/区间指标（三 backend）✓；**待做**：tsproj_* 架构诊断报告、TimeGPT、legacy adapter、本地 foundation model。
