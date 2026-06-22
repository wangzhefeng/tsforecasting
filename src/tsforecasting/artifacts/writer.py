"""Artifact writer: persist CSVs, manifest.json, and run_config.yaml."""

from __future__ import annotations

import dataclasses
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from tsforecasting.artifacts.schema import validate_columns
from tsforecasting.config import Config
from tsforecasting.models.registry import BuiltModel

_CSV_ARTIFACTS = ["backtest_predictions", "metrics", "runtime_metrics", "model_comparison"]


def write_artifacts(
    run_dir: Path,
    *,
    backtest_predictions: pd.DataFrame,
    metrics: pd.DataFrame,
    runtime_metrics: pd.DataFrame,
    model_comparison: pd.DataFrame,
    predictions: pd.DataFrame | None = None,
) -> None:
    """Validate and write all per-run CSV artifacts to ``run_dir``."""
    run_dir.mkdir(parents=True, exist_ok=True)
    frames = {
        "backtest_predictions": backtest_predictions,
        "metrics": metrics,
        "runtime_metrics": runtime_metrics,
        "model_comparison": model_comparison,
    }
    if predictions is not None:
        frames["predictions"] = predictions
    for name, df in frames.items():
        validate_columns(df, name)
        df.to_csv(run_dir / f"{name}.csv", index=False)


def build_manifest(
    config: Config,
    loaded_meta: dict[str, Any],
    built_models: list[BuiltModel],
    run_dir: Path,
    do_predict: bool,
) -> dict[str, Any]:
    """Assemble the run manifest dict (provenance, mapping, artifacts, env)."""
    has_predict = do_predict and config.predict is not None
    artifacts: dict[str, str] = {
        name: str((run_dir / f"{name}.csv").resolve()) for name in _CSV_ARTIFACTS
    }
    if has_predict:
        artifacts["predictions"] = str((run_dir / "predictions.csv").resolve())
    backends = sorted({b.backend for b in built_models})
    return {
        "run_id": config.run_id,
        "run_id_rule": "tsforecasting-<UTC YYYYmmddHHMMSS>-<sha8>",
        "config_source": config.config_source,
        "run_command": " ".join(sys.argv),
        "seed": config.seed,
        "per_backend_seed": {backend: config.seed for backend in backends},
        "input": {
            "path": loaded_meta["path"],
            "n_rows": loaded_meta["n_rows"],
            "n_series": loaded_meta["n_series"],
        },
        "field_mapping": {
            "time_col": loaded_meta["time_col"],
            "target_col": loaded_meta["target_col"],
            "id_col": loaded_meta["id_col"],
            "unique_id_source": loaded_meta["id_col"] if loaded_meta["id_col"] else "series_0 (auto)",
        },
        "freq": loaded_meta["freq"],
        "freq_inferred": loaded_meta["freq_inferred"],
        "missing_points": loaded_meta["missing_points"],
        "backtest": {
            "horizon": config.backtest.horizon,
            "n_windows": config.backtest.n_windows,
            "step_size": config.backtest.step_size,
        },
        "models": [
            {"name": m.name, "backend": m.backend, "params": m.params}
            for m in config.models
        ],
        "mlforecast": (
            {
                "lags": config.mlforecast.lags,
                "date_features": config.mlforecast.date_features,
                "target_transforms": config.mlforecast.target_transforms,
            }
            if config.mlforecast is not None
            else None
        ),
        "evaluation": {
            "metrics": config.evaluation.metrics,
            "rank_metric": config.evaluation.rank_metric,
        },
        "predict": {"horizon": config.predict.horizon} if has_predict else None,
        "artifacts": artifacts,
        "log_path": str((Path("logs") / config.runtime.log_name).resolve()),
        "env": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "SERVICE_LOG_LEVEL": os.environ.get("SERVICE_LOG_LEVEL"),
            "LOG_NAME": os.environ.get("LOG_NAME"),
        },
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def write_manifest(manifest: dict[str, Any], run_dir: Path) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, default=str), encoding="utf-8"
    )


def write_run_config(config: Config, run_dir: Path) -> None:
    """Persist the resolved config (with CLI overrides) as YAML."""
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = dataclasses.asdict(config)
    (run_dir / "run_config.yaml").write_text(
        yaml.safe_dump(payload, sort_keys=False), encoding="utf-8"
    )
