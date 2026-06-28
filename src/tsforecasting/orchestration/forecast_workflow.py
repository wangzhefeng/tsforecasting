"""普通预测工作流：数据加载 -> 模型构建 -> 预测/回测 -> 评估 -> 写产物。"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

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
from tsforecasting.utils.runtime import configure_run_environment


def _build_adapter(backend: str, df, group, freq: str, run_id: str, config: Config):
    """按 backend 创建适配器；可选 backend 在分支内延迟导入。"""
    levels = config.prediction_intervals.levels if config.prediction_intervals else None

    if backend == "statsforecast":
        return StatsForecastAdapter(df, group, freq, run_id, levels=levels)

    if backend == "mlforecast":
        from tsforecasting.models.nixtla.ml import MLForecastAdapter

        return MLForecastAdapter(
            df, group, freq, run_id, config.mlforecast, levels=levels
        )

    if backend == "neuralforecast":
        from tsforecasting.models.nixtla.neural import NeuralForecastAdapter

        return NeuralForecastAdapter(df, group, freq, run_id, levels=levels)

    raise ValueError(f"no adapter registered for backend '{backend}'")


def run_pipeline(config: Config, *, do_predict: bool = True) -> Path:
    """执行普通预测流程，并把 artifact 写到 ``output_dir/run_id``。"""
    logger = configure_run_environment(
        config.runtime.log_name, config.runtime.log_level, config.seed
    )
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
            "data has %d missing time points (not filled)",
            loaded.meta["missing_points"],
        )

    built = build_models(config)
    groups: dict[str, list] = defaultdict(list)
    for b in built:
        groups[b.backend].append(b)

    # 同一 backend 的模型交给一个 adapter 批量执行，之后再合并成长表 artifact。
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
    if do_predict:
        logger.info("produced %d prediction rows", len(predictions))
    backtest = pd.concat(backtest_parts, ignore_index=True)
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


def run_forecast_workflow(config: Config, *, do_predict: bool = True) -> Path:
    """更清晰的 workflow 别名；保留 run_pipeline 兼容旧导入。"""
    return run_pipeline(config, do_predict=do_predict)
