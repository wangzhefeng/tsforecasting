"""Artifact 写入器：统一落盘 CSV、manifest.json、run_config.yaml 和摘要。"""

from __future__ import annotations

import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from tsforecasting.artifacts.schema import validate_columns
from tsforecasting.config import ForecastArgs
from tsforecasting.models.registry import BuiltModel
from tsforecasting.utils.serialization import dataclass_to_yaml, write_json

FORECAST_ARTIFACT_PATHS = {
    "predictions.backtest": Path("predictions/backtest.csv"),
    "metrics.metrics": Path("metrics/metrics.csv"),
    "metrics.runtime": Path("metrics/runtime.csv"),
    "metrics.model_comparison": Path("metrics/model_comparison.csv"),
}


class ForecastArtifactWriter:
    """forecast run artifact 写入器。"""

    def __init__(self, run_dir: Path) -> None:
        self.run_dir = Path(run_dir)

    def write_artifacts(
        self,
        *,
        backtest_predictions: pd.DataFrame,
        metrics: pd.DataFrame,
        runtime_metrics: pd.DataFrame,
        model_comparison: pd.DataFrame,
        predictions: pd.DataFrame | None = None,
    ) -> None:
        """校验并写出普通 forecast 运行的全部 CSV artifact。"""
        frames: dict[str, tuple[str, Path, pd.DataFrame]] = {
            "backtest_predictions": (
                "backtest_predictions",
                FORECAST_ARTIFACT_PATHS["predictions.backtest"],
                backtest_predictions,
            ),
            "metrics": ("metrics", FORECAST_ARTIFACT_PATHS["metrics.metrics"], metrics),
            "runtime_metrics": (
                "runtime_metrics",
                FORECAST_ARTIFACT_PATHS["metrics.runtime"],
                runtime_metrics,
            ),
            "model_comparison": (
                "model_comparison",
                FORECAST_ARTIFACT_PATHS["metrics.model_comparison"],
                model_comparison,
            ),
        }
        if predictions is not None:
            frames["predictions"] = (
                "predictions",
                Path("predictions/forecast.csv"),
                predictions,
            )
        for contract, rel_path, df in frames.values():
            validate_columns(df, contract)
            out = self.run_dir / rel_path
            out.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(out, index=False)

    def write_data_summary(self, loaded_meta: dict[str, Any]) -> None:
        """写出数据读取摘要，供人工检查和报告复用。"""
        out = self.run_dir / "data" / "summary.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        write_json(out, loaded_meta)

    def write_manifest(self, manifest: dict[str, Any]) -> None:
        write_json(self.run_dir / "manifest.json", manifest)

    def write_run_config(self, config: ForecastArgs) -> None:
        """把解析后的最终配置写成 YAML，包括 CLI override 后的值。"""
        out = self.run_dir / "config" / "run_config.yaml"
        out.parent.mkdir(parents=True, exist_ok=True)
        dataclass_to_yaml(out, config)


def write_artifacts(
    run_dir: Path,
    *,
    backtest_predictions: pd.DataFrame,
    metrics: pd.DataFrame,
    runtime_metrics: pd.DataFrame,
    model_comparison: pd.DataFrame,
    predictions: pd.DataFrame | None = None,
) -> None:
    """函数式兼容入口；内部委托 ForecastArtifactWriter。"""
    ForecastArtifactWriter(run_dir).write_artifacts(
        backtest_predictions=backtest_predictions,
        metrics=metrics,
        runtime_metrics=runtime_metrics,
        model_comparison=model_comparison,
        predictions=predictions,
    )


def write_data_summary(run_dir: Path, loaded_meta: dict[str, Any]) -> None:
    """函数式兼容入口；内部委托 ForecastArtifactWriter。"""
    ForecastArtifactWriter(run_dir).write_data_summary(loaded_meta)


def build_manifest(
    config: ForecastArgs,
    loaded_meta: dict[str, Any],
    built_models: list[BuiltModel],
    run_dir: Path,
    do_predict: bool,
    skipped_stages: dict[str, str] | None = None,
) -> dict[str, Any]:
    """组装 forecast manifest，记录来源、字段映射、产物路径和运行环境。"""
    has_forecast = do_predict and config.forecast is not None
    artifacts = {
        key: path.as_posix() for key, path in FORECAST_ARTIFACT_PATHS.items()
    }
    if has_forecast:
        artifacts["predictions.forecast"] = "predictions/forecast.csv"
    artifacts["config.run_config"] = "config/run_config.yaml"
    artifacts["data.summary"] = "data/summary.json"

    levels = config.prediction_intervals.levels if config.prediction_intervals else []
    backends = sorted({b.backend for b in built_models})
    stages = {
        "parse_args": {"status": "completed"},
        "load_data": {"status": "completed"},
        "preprocess": {"status": "completed"},
        "feature_engineering": {"status": "completed"},
        "train": {"status": "completed"},
        "valid": {"status": "completed"},
        "test": {"status": "skipped"},
        "forecast": {"status": "completed" if has_forecast else "skipped"},
    }
    for stage, reason in (skipped_stages or {}).items():
        stages[stage] = {"status": "skipped", "reason": reason}

    return {
        "run_id": config.run_id,
        "run_id_rule": "tsforecasting-<UTC YYYYmmddHHMMSS>-<random8>",
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
            "unique_id_source": loaded_meta["id_col"]
            if loaded_meta["id_col"]
            else "series_0 (auto)",
        },
        "freq": loaded_meta["freq"],
        "freq_inferred": loaded_meta["freq_inferred"],
        "missing_points": loaded_meta["missing_points"],
        "split": {
            "horizon": config.split.horizon,
            "n_windows": config.split.n_windows,
            "step_size": config.split.step_size,
        },
        "backtest": {
            "horizon": config.split.horizon,
            "n_windows": config.split.n_windows,
            "step_size": config.split.step_size,
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
        "forecast": {"horizon": config.forecast.horizon} if has_forecast else None,
        "prediction_intervals": {"levels": levels} if levels else None,
        "interval_columns": [
            col for level in levels for col in (f"lo-{level}", f"hi-{level}")
        ],
        "artifacts": artifacts,
        "reports": {"model_comparison": "reports/model_comparison.ipynb"},
        "stages": stages,
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
    ForecastArtifactWriter(run_dir).write_manifest(manifest)


def write_run_config(config: ForecastArgs, run_dir: Path) -> None:
    """函数式兼容入口；内部委托 ForecastArtifactWriter。"""
    ForecastArtifactWriter(run_dir).write_run_config(config)
