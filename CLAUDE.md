# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## Project Status

`tsforecasting` MVP-0 (StatsForecast vertical slice) and the MVP-1 MLForecast, NeuralForecast, and HierarchicalForecast backends are all implemented. The package lives under `src/tsforecasting/` with a `tsforecasting` CLI (`validate-config` / `run` / `backtest` / `reconcile` / `report`), `pytest` + `ruff` in the dev group, and example configs at `configs/examples/ett_small_stats.yaml` (StatsForecast), `configs/examples/ett_small_ml.yaml` (mixed StatsForecast + MLForecast), `configs/examples/ett_small_neural.yaml` (mixed StatsForecast + NeuralForecast NHITS CPU smoke, all on hourly `ETTh1`), and `configs/examples/tourism_small_hierarchical.yaml` (TourismSmall hierarchical reconciliation). `run`/`backtest` dispatch one adapter per forecast backend so a single run ranks models across backends; hierarchical reconciliation is an independent `reconcile` flow with its own config and artifacts. NeuralForecast/HierarchicalForecast/notebook-reporting live behind the `[neural]`/`[hierarchical]`/`[report]` extras; see `docs/PLAN.md`.

Read these before implementation:

- `docs/PLAN.md` — executable development plan and implementation status.
- `docs/unified-ts-framework-plan-v2.md` — current implementation baseline. Build from this and `docs/PLAN.md`.
- `docs/unified-ts-framework-plan-v1.md` — v1 historical baseline, **superseded by v2**; kept for design history only. Do not implement from its module specs (§5 architecture / §6 catalog) and do not overwrite it.
- `docs/LOG.md` — development log.
- `docs/model_catalog.md` — full Nixtla model catalog (78 entries across stats/neural/ml with source + status), generated from `src/tsforecasting/models/catalog.py`.

## Toolchain

- Python `>=3.12`, managed by `uv`.
- `uv sync` installs base + the `dev` group (`pytest`, `ruff`); `uv sync --extra <ml|neural|hierarchical|plot|report>` adds an extras group (`report` = nbformat/nbconvert/ipykernel for notebook + HTML reporting).
- `uv add <pkg>` / `uv add --dev <pkg>` updates dependencies and `uv.lock`.
- Dev tooling: `uv run pytest`, `uv run ruff check .`.
- Dependency pins are load-bearing: Nixtla hard-pins `pandas<3`, and numba (transitive via `statsforecast`) caps `numpy<2.5`. Do not bump these without a spike (see `docs/LOG.md` P1).

## Current MVP Contract

- Package/project name is `tsforecasting`.
- Internal forecasting data contract is Nixtla long table: `unique_id / ds / y`.
- MVP-0 is Nixtla-only StatsForecast first: `SeasonalNaive` / `AutoETS`, UtilsForecast metrics, core artifacts, and manifest.
- MVP-1 adds MLForecast, NeuralForecast CPU smoke, and HierarchicalForecast with `TourismSmall`.
- Each **forecast** backend is an adapter under `src/tsforecasting/models/nixtla/` mirroring `StatsForecastAdapter` (`predict`/`cross_validation` returning the canonical long contracts with the dense-rank `horizon` column + a `timing` dict); `src/tsforecasting/orchestration/run.py` groups models by backend, builds one adapter per backend, and lazy-imports optional backends so the base install stays importable. **Hierarchical reconciliation is a separate flow** (`config/hierarchical.py` + `reconciliation.py` + `orchestration/reconcile.py` + the `reconcile` CLI subcommand) with its own `HierarchicalConfig` and artifact set (`base_predictions` / `reconciled_predictions` / `reconciliation_diagnostics`), not a forecast adapter.
- Full Nixtla catalog, Jupyter reporting, TimeGPT, legacy adapters, and local foundation models are future phases, not MVP-0 blockers.
- Reuse Nixtla native APIs for training, prediction, cross-validation, feature handling, evaluation, plotting, and reconciliation when available.
- Phase-2 opt-ins: `prediction_intervals.levels` appends `lo-/hi-` columns to predictions/backtest and `coverage-/width-` rows to metrics (statsforecast native `level=`, neuralforecast quantile loss via the `nhits_quantile` preset, mlforecast conformal — predict-only since MLForecast emits no cv intervals); `model_comparison` appends the interval columns but still ranks on the core point metric; `report --html` executes the notebook and exports HTML (needs the `[report]` extra + a registered `python3` kernel).
- `tsforecasting` should focus on config parsing, validation, field mapping, output normalization, logging, artifacts, and phase-appropriate reporting.

## Documentation Rules

- After implementation work, update `docs/PLAN.md` plan-item status and append `docs/LOG.md`.
- If architecture scope, MVP boundary, or module responsibilities change again, create a new scheme document such as `docs/unified-ts-framework-plan-v3.md` based on the latest baseline.
- Keep `CLAUDE.md` concise: hard rules only, no development history.

## Logging

- Logging is vendored at `src/tsforecasting/utils/logging.py`: lazy handlers (first `get_logger()` call), CWD-relative `logs/{LOG_NAME}/service*`, no duplicate handlers.
- `SERVICE_LOG_LEVEL` controls log level; `LOG_NAME` controls the subdirectory under `logs/`.
