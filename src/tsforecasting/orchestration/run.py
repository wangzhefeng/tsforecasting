"""Run orchestration: data -> models -> predict/backtest -> eval -> artifacts."""

from __future__ import annotations

import os
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

from tsforecasting.artifacts.writer import (
    build_manifest,
    write_artifacts,
    write_manifest,
    write_run_config,
)
from tsforecasting.config import Config
from tsforecasting.data_provider import load_data
from tsforecasting.evaluation.metrics import (
    build_model_comparison,
    build_runtime_metrics,
    compute_metrics,
)
from tsforecasting.models import build_models
from tsforecasting.models.nixtla import StatsForecastAdapter
from tsforecasting.utils.logging import get_logger


def _build_adapter(backend: str, df, group, freq: str, run_id: str, config: Config):
    """Instantiate the adapter for ``backend`` (lazy-importing optional backends)."""
    levels = config.prediction_intervals.levels if config.prediction_intervals else None
    if backend == "statsforecast":
        return StatsForecastAdapter(df, group, freq, run_id, levels=levels)
    if backend == "mlforecast":
        from tsforecasting.models.nixtla.ml import MLForecastAdapter

        return MLForecastAdapter(df, group, freq, run_id, config.mlforecast, levels=levels)
    if backend == "neuralforecast":
        from tsforecasting.models.nixtla.neural import NeuralForecastAdapter

        return NeuralForecastAdapter(df, group, freq, run_id, levels=levels)
    raise ValueError(f"no adapter registered for backend '{backend}'")


def run_pipeline(config: Config, *, do_predict: bool = True) -> Path:
    """Execute the full pipeline and write artifacts under ``output_dir/run_id``."""
    os.environ["LOG_NAME"] = config.runtime.log_name
    os.environ["SERVICE_LOG_LEVEL"] = config.runtime.log_level
    logger = get_logger()
    np.random.seed(config.seed)

    logger.info("starting run_id=%s", config.run_id)
    loaded = load_data(config.data)
    logger.info(
        "loaded %d rows / %d series (freq=%s, inferred=%s, missing=%d)",
        loaded.meta["n_rows"],
        loaded.meta["n_series"],
        loaded.meta["freq"],
        loaded.meta["freq_inferred"],
        loaded.meta["missing_points"],
    )
    if loaded.meta["missing_points"]:
        logger.warning(
            "data has %d missing time points (not filled)", loaded.meta["missing_points"]
        )

    built = build_models(config)
    # Group models by backend; one batched adapter per backend (each backend
    # fits its models in one object). Predictions/backtest are concatenated so a
    # single run ranks models across backends.
    groups: dict[str, list] = defaultdict(list)
    for b in built:
        groups[b.backend].append(b)

    prediction_parts: list[pd.DataFrame] = []
    backtest_parts: list[pd.DataFrame] = []
    timings: dict[str, dict[str, float]] = {}
    do_predict = do_predict and config.predict is not None
    for backend, group in groups.items():
        adapter = _build_adapter(
            backend, loaded.df, group, loaded.meta["freq"], config.run_id, config
        )
        if do_predict:
            prediction_parts.append(adapter.predict(config.predict.horizon))
        backtest_parts.append(
            adapter.cross_validation(
                config.backtest.horizon,
                config.backtest.n_windows,
                config.backtest.step_size,
            )
        )
        timings[backend] = adapter.timing

    predictions = (
        pd.concat(prediction_parts, ignore_index=True) if prediction_parts else None
    )
    backtest = pd.concat(backtest_parts, ignore_index=True)
    if do_predict:
        logger.info("produced %d prediction rows", len(predictions))
    logger.info("produced %d backtest rows", len(backtest))

    metrics = compute_metrics(backtest, config.run_id)
    runtime_metrics = build_runtime_metrics(
        config.run_id, built, timings, loaded.meta["n_series"], loaded.meta["n_rows"]
    )
    model_comparison = build_model_comparison(
        metrics, runtime_metrics, config.evaluation.rank_metric
    )

    run_dir = Path(config.artifacts.output_dir) / config.run_id
    write_artifacts(
        run_dir,
        backtest_predictions=backtest,
        metrics=metrics,
        runtime_metrics=runtime_metrics,
        model_comparison=model_comparison,
        predictions=predictions,
    )
    manifest = build_manifest(config, loaded.meta, built, run_dir, do_predict)
    write_manifest(manifest, run_dir)
    write_run_config(config, run_dir)
    logger.info("artifacts written to %s", run_dir)
    return run_dir
