# AGENTS.md

This file provides guidance to Codex when working in this repository.

## Project Status

`tsforecasting` is still pre-implementation. The repository currently has project metadata, documentation, `utils/log_util.py`, and no `src/`, `configs/`, `examples/`, `tests/`, CLI entrypoint, test runner, or linter.

Read these before implementation:

- `docs/PLAN.md` — executable development plan and implementation status.
- `docs/unified-ts-framework-plan-v1.md` — v1 architecture baseline. Do not overwrite it; create a new version document for future scheme changes.
- `docs/LOG.md` — development log.

## Toolchain

- Python `>=3.12`, managed by `uv`.
- `uv sync` installs the current environment.
- `uv add <pkg>` / `uv add --dev <pkg>` updates dependencies and `uv.lock`.
- Do not assume `pytest`, `ruff`, or other dev tools exist until the plan adds them.

## Current MVP Contract

- Package/project name is `tsforecasting`.
- Internal forecasting data contract is Nixtla long table: `unique_id / ds / y`.
- MVP is Nixtla-only: StatsForecast, MLForecast, NeuralForecast, UtilsForecast, HierarchicalForecast with `TourismSmall`.
- TimeGPT, legacy adapters, and local foundation models are future phases, not MVP.
- Reuse Nixtla native APIs for training, prediction, cross-validation, feature handling, evaluation, plotting, and reconciliation when available.
- `tsforecasting` should focus on config parsing, validation, field mapping, output normalization, logging, artifacts, and reporting.

## Documentation Rules

- After implementation work, update `docs/PLAN.md` plan-item status and append `docs/LOG.md`.
- If architecture scope, MVP boundary, or module responsibilities change, create a new scheme document such as `docs/unified-ts-framework-plan-v2.md` based on v1.
- Keep `AGENTS.md` concise: hard rules only, no development history.

## Logging

- Reuse `utils.log_util.logger`.
- `SERVICE_LOG_LEVEL` controls log level.
- `LOG_NAME` controls the log directory under `logs/{LOG_NAME}/service*`.
- Do not create duplicate logger handlers in feature modules.
