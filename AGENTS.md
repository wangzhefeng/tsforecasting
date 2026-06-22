# AGENTS.md

This file provides guidance to Codex when working in this repository.

## Project Status

`tsforecasting` MVP-0 (StatsForecast vertical slice) is implemented. The package lives under `src/tsforecasting/` with a `tsforecasting` CLI (`validate-config` / `run` / `backtest`), `pytest` + `ruff` in the dev group, and an example config at `configs/examples/ett_small_stats.yaml` (hourly `ETTh1`). MVP-1 backends (MLForecast / NeuralForecast / HierarchicalForecast) are declared as extras but not yet implemented; see `docs/PLAN.md`.

Read these before implementation:

- `docs/PLAN.md` — executable development plan and implementation status.
- `docs/unified-ts-framework-plan-v2.md` — current implementation baseline. Build from this and `docs/PLAN.md`.
- `docs/unified-ts-framework-plan-v1.md` — v1 historical baseline, **superseded by v2**; kept for design history only. Do not implement from its module specs (§5 architecture / §6 catalog) and do not overwrite it.
- `docs/LOG.md` — development log.

## Toolchain

- Python `>=3.12`, managed by `uv`.
- `uv sync` installs base + the `dev` group (`pytest`, `ruff`); `uv sync --extra <ml|neural|hierarchical|plot>` adds an extras group.
- `uv add <pkg>` / `uv add --dev <pkg>` updates dependencies and `uv.lock`.
- Dev tooling: `uv run pytest`, `uv run ruff check .`.
- Dependency pins are load-bearing: Nixtla hard-pins `pandas<3`, and numba (transitive via `statsforecast`) caps `numpy<2.5`. Do not bump these without a spike (see `docs/LOG.md` P1).

## Current MVP Contract

- Package/project name is `tsforecasting`.
- Internal forecasting data contract is Nixtla long table: `unique_id / ds / y`.
- MVP-0 is Nixtla-only StatsForecast first: `SeasonalNaive` / `AutoETS`, UtilsForecast metrics, core artifacts, and manifest.
- MVP-1 adds MLForecast, NeuralForecast CPU smoke, and HierarchicalForecast with `TourismSmall`.
- Full Nixtla catalog, Jupyter reporting, TimeGPT, legacy adapters, and local foundation models are future phases, not MVP-0 blockers.
- Reuse Nixtla native APIs for training, prediction, cross-validation, feature handling, evaluation, plotting, and reconciliation when available.
- `tsforecasting` should focus on config parsing, validation, field mapping, output normalization, logging, artifacts, and phase-appropriate reporting.

## Documentation Rules

- After implementation work, update `docs/PLAN.md` plan-item status and append `docs/LOG.md`.
- If architecture scope, MVP boundary, or module responsibilities change again, create a new scheme document such as `docs/unified-ts-framework-plan-v3.md` based on the latest baseline.
- Keep `AGENTS.md` concise: hard rules only, no development history.

## Logging

- Logging is vendored at `src/tsforecasting/utils/logging.py`: lazy handlers (first `get_logger()` call), CWD-relative `logs/{LOG_NAME}/service*`, no duplicate handlers.
- `SERVICE_LOG_LEVEL` controls log level; `LOG_NAME` controls the subdirectory under `logs/`.
- The legacy `utils/log_util.py` is superseded — do not import the repo-top-level `utils/` from inside the package.
