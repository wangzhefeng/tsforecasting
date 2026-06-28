# AGENTS.md

This file provides guidance to Codex when working in this repository.

## Project Status

`tsforecasting` focuses on three forecast backends: StatsForecast, MLForecast, and NeuralForecast. The package lives under `src/tsforecasting/` with class-based entrypoints: `ForecastRunner` in `main.py` for local VSCode runs and `MainCLI` in `main_cli.py` for shell/script runs (`validate-config` / `run` / `backtest` / `report`). TourismSmall hierarchical reconciliation is paused and stored under `src/tsforecasting/todo/hierarchical/`; do not wire it back into active configs, scripts, tests, artifacts, or reporting unless explicitly requested.

Read these before implementation:

- `docs/PLAN.md` — executable development plan and implementation status.
- `docs/unified-ts-framework-plan-v3.md` — current implementation baseline. Build from this and `docs/PLAN.md`.
- `docs/unified-ts-framework-plan-v2.md` — historical implementation baseline before the runner/CLI restructure.
- `docs/unified-ts-framework-plan-v1.md` — v1 historical baseline, **superseded by v2**; kept for design history only. Do not implement from its module specs (§5 architecture / §6 catalog) and do not overwrite it.
- `docs/LOG.md` — development log.
- `docs/model_catalog.md` — full Nixtla model catalog (78 entries across stats/neural/ml with source + status), generated from `src/tsforecasting/models/catalog.py`.

## Toolchain

- Python `>=3.12`, managed by `uv`.
- `uv sync` installs base + the `dev` group (`pytest`, `ruff`); base includes `nbformat` for static notebook generation. `uv sync --extra <ml|neural|plot|report>` adds an extras group (`report` = nbconvert/ipykernel for HTML reporting).
- `uv add <pkg>` / `uv add --dev <pkg>` updates dependencies and `uv.lock`.
- Dev tooling: `uv run pytest`, `uv run ruff check .`.
- Curated example scripts live under `scripts/<dataset>/` and call `uv run python -m tsforecasting.main_cli`; keep `scripts/script_config_map.yaml` in sync with `configs/examples/**`.
- Dependency pins are load-bearing: Nixtla hard-pins `pandas<3`, and numba (transitive via `statsforecast`) caps `numpy<2.5`. Do not bump these without a spike (see `docs/LOG.md` P1).

## Current MVP Contract

- Package/project name is `tsforecasting`.
- Internal forecasting data contract is Nixtla long table: `unique_id / ds / y`.
- CLI public entrypoint is `tsforecasting.main_cli:main`; keep CLI parsing in `MainCLI` and workflow logic in `ForecastRunner`.
- MVP-0 is Nixtla-only StatsForecast first: `SeasonalNaive` / `AutoETS`, UtilsForecast metrics, core artifacts, and manifest.
- MVP-1 forecast scope adds MLForecast and NeuralForecast CPU smoke. HierarchicalForecast with `TourismSmall` is archived under `todo/`.
- Each **forecast** backend is an adapter under `src/tsforecasting/models/nixtla/` mirroring `StatsForecastAdapter` (`predict`/`cross_validation` returning the canonical long contracts with the dense-rank `horizon` column + a `timing` dict); `ForecastRunner` groups models by backend, builds one adapter per backend, and lazy-imports optional backends so the base install stays importable.
- Shared helpers belong in `src/tsforecasting/utils/` once used across subsystem boundaries (`imports.py`, `frames.py`, `runtime.py`, `serialization.py`); do not hide cross-backend helpers inside one adapter module.
- Full Nixtla catalog, Jupyter reporting, TimeGPT, legacy adapters, and local foundation models are future phases, not MVP-0 blockers.
- Reuse Nixtla native APIs for training, prediction, cross-validation, feature handling, evaluation, and plotting when available.
- Phase-2 opt-ins: `prediction_intervals.levels` appends `lo-/hi-` columns to predictions/backtest and `coverage-/width-` rows to metrics (statsforecast native `level=`, neuralforecast quantile loss via the `nhits_quantile` preset, mlforecast conformal — predict-only since MLForecast emits no cv intervals); `model_comparison` appends the interval columns but still ranks on the core point metric; `report --html` executes the notebook and exports HTML (needs the `[report]` extra + a registered `python3` kernel).
- Config validation must stay metadata-only and dependency-light: `validate-config` rejects unknown registry model names and backend mismatches without importing optional backend packages; CLI run-level overrides are revalidated before dry-run or execution.
- `tsforecasting` should focus on config parsing, validation, field mapping, output normalization, logging, artifacts, and phase-appropriate reporting.

## Documentation Rules

- After implementation work, update `docs/PLAN.md` plan-item status and append `docs/LOG.md`.
- If architecture scope, MVP boundary, or module responsibilities change again, create a new scheme document such as `docs/unified-ts-framework-plan-v3.md` based on the latest baseline.
- Keep `AGENTS.md` concise: hard rules only, no development history.
- Source docstrings/comments should use Chinese for non-obvious responsibilities, data contracts, and constraints; do not translate obvious code line by line or change CLI/artifact text just for comment cleanup.

## Logging

- Logging is vendored at `src/tsforecasting/utils/logging.py`: lazy handlers (first `get_logger()` call), CWD-relative `logs/{LOG_NAME}/service*`, no duplicate handlers.
- `SERVICE_LOG_LEVEL` controls log level; `LOG_NAME` controls the subdirectory under `logs/`.
