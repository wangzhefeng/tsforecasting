# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

**Pre-implementation.** The repository currently contains only scaffolding (`pyproject.toml`, `uv.lock`, `LICENSE`) and a design document. There is no source code, test suite, or linter yet. `docs/unified-ts-framework-plan.md` is the authoritative design draft — it is explicitly marked a review draft ("暂不进入代码实现", not yet entering implementation). **Read it before any implementation work.** The notes below summarize only the decisions that constrain code.

## Toolchain

- Python 3.12, managed with **uv** (`uv.lock` + `pyproject.toml`); pinned via `.python-version`.
- `uv sync` — install dependencies into `.venv`
- `uv add <pkg>` / `uv add --dev <pkg>` — add a runtime / dev dependency and refresh the lockfile
- `uv run python <script>` — run a script in the project environment
- No test runner or linter is configured. Do not assume `pytest`/`ruff`/etc. work — add them via `uv add --dev` only when the plan calls for it.

## Architecture intent (from the plan)

Goal: a **unified time-series forecasting framework** modeled on the Nixtla ecosystem, spanning statistical, ML, deep-learning, and foundation/API backends, and gradually absorbing four existing legacy projects. Load-bearing constraints:

- **Internal data contract = Nixtla long table:** `unique_id / ds / y`. Every backend speaks this; adapters convert to and from it.
- **Light core + isolated backends.** The core stays low-dependency. Backends split into in-process (StatsForecast, MLForecast), API (TimeGPT), and subprocess / isolated-env (DL, local LTSFM). Do not merge heavy deps (Torch, Transformers) into one environment.
- **Unify external contracts first, not training internals.** Standardize data → config → split/backtest → prediction output → metrics → artifacts → manifest. The plan explicitly lists a universal `Trainer` / `FeatureEngineer` abstraction as a stage-1 anti-pattern — do not build one prematurely.
- **Adapter-first migration.** Legacy projects (`tsproj_stat` → `tsproj_ml` → `tsproj_dl` → `tsproj_ltsfm`, in that order) join as adapters that translate standard config into their native YAML/CLI and their output back to the unified artifact contract. Promote shared logic to core only after the same pattern repeats across ≥2 backends.
- **MVP (stage 1) scope:** forecasting only; ETT small data; backends StatsForecast + MLForecast + TimeGPT (mock-by-default — real API calls require explicit opt-in and `NIXTLA_API_KEY`).

See `docs/unified-ts-framework-plan.md` §5 for the full target layout (`src/tsforecast_lab/...`), the `ForecastBackend` protocol (`fit` / `predict` / `cross_validate` / `save` / `load`), and the standard per-run artifact structure (`runs/{run_id}/...` with `manifest.json`, `predictions.csv`, `backtest_predictions.csv`, `metrics.{json,csv}`, `plots/`, `model/`, `logs/`).

## Gaps to be aware of before implementing

- `pyproject.toml` currently lists only `statsmodels`, `scikit-learn`, `pandas`, `numpy`, `scipy`, `matplotlib` — **none of the Nixtla ecosystem packages** the MVP depends on (`statsforecast`, `mlforecast`, the Nixtla SDK). These must be added.
- The repo/package is named `tsforecasting`, but the plan refers to the framework as `tsforecast_lab` and proposes a `src/tsforecast_lab/` layout. Confirm the intended package name before creating package directories.
