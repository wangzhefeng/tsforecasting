"""层级预测协调工作流：加载层级数据、切分 holdout、协调并写产物。"""

from __future__ import annotations

from pathlib import Path

from tsforecasting.artifacts.writer import (
    build_hierarchical_manifest,
    write_hierarchical_artifacts,
    write_manifest,
)
from tsforecasting.config.hierarchical import HierarchicalConfig
from tsforecasting.data_provider import load_hierarchical
from tsforecasting.models import build_model
from tsforecasting.reconciliation import reconcile_pipeline
from tsforecasting.utils.runtime import configure_run_environment
from tsforecasting.utils.serialization import dataclass_to_yaml


def run_reconciliation(config: HierarchicalConfig) -> Path:
    """执行层级协调流程，并把 artifact 写到 ``output_dir/run_id``。"""
    logger = configure_run_environment(
        config.runtime.log_name, config.runtime.log_level, config.seed
    )

    logger.info("starting reconciliation run_id=%s", config.run_id)
    loaded = load_hierarchical(config.data)
    logger.info(
        "loaded %s: %d series / %d rows / %d levels",
        config.data.dataset,
        loaded.meta["n_series"],
        loaded.meta["n_rows"],
        len(loaded.meta["levels"]),
    )

    horizon = config.base_forecast.horizon
    # 使用最后 horizon 个时间点作为 holdout；train 用于 base forecast 和 reconcile。
    last = sorted(loaded.Y_df["ds"].unique())[-horizon:]
    train = loaded.Y_df[~loaded.Y_df["ds"].isin(last)].copy()
    test = loaded.Y_df[loaded.Y_df["ds"].isin(last)].copy()
    logger.info(
        "split: %d train / %d test rows (horizon=%d)", len(train), len(test), horizon
    )

    built = [build_model(m) for m in config.base_forecast.models]
    base_long, rec_long, diag = reconcile_pipeline(
        train=train,
        test=test,
        built_models=built,
        freq=config.data.freq,
        horizon=horizon,
        reconciler_specs=config.hierarchical.reconcilers,
        S_df=loaded.S_df,
        tags=loaded.tags,
        run_id=config.run_id,
        diagnostics=config.hierarchical.diagnostics,
    )
    logger.info(
        "reconciled: %d base / %d reconciled rows / %d diagnostics rows",
        len(base_long),
        len(rec_long),
        len(diag),
    )

    run_dir = Path(config.artifacts.output_dir) / config.run_id
    write_hierarchical_artifacts(
        run_dir,
        base_predictions=base_long,
        reconciled_predictions=rec_long,
        reconciliation_diagnostics=diag,
    )
    manifest = build_hierarchical_manifest(config, loaded.meta, run_dir)
    write_manifest(manifest, run_dir)
    dataclass_to_yaml(run_dir / "run_config.yaml", config)
    logger.info("artifacts written to %s", run_dir)
    return run_dir


def run_reconciliation_workflow(config: HierarchicalConfig) -> Path:
    """更清晰的 workflow 别名；保留 run_reconciliation 兼容旧导入。"""
    return run_reconciliation(config)
