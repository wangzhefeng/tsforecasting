"""Hierarchical reconciliation orchestration (P9).

Independent of ``run_pipeline``: load a hierarchical dataset, hold out the last
``horizon`` steps, base-forecast + reconcile, then write the three P9 artifacts.
"""

from __future__ import annotations

import dataclasses
import os
from pathlib import Path

import numpy as np
import yaml

from tsforecasting.artifacts.writer import (
    build_hierarchical_manifest,
    write_hierarchical_artifacts,
    write_manifest,
)
from tsforecasting.config.hierarchical import HierarchicalConfig
from tsforecasting.data import load_hierarchical
from tsforecasting.models import build_model
from tsforecasting.reconciliation import reconcile_pipeline
from tsforecasting.utils.logging import get_logger


def run_reconciliation(config: HierarchicalConfig) -> Path:
    """Load -> base forecast -> reconcile -> diagnostics -> artifacts."""
    os.environ["LOG_NAME"] = config.runtime.log_name
    os.environ["SERVICE_LOG_LEVEL"] = config.runtime.log_level
    logger = get_logger()
    np.random.seed(config.seed)

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
    (run_dir / "run_config.yaml").write_text(
        yaml.safe_dump(dataclasses.asdict(config), sort_keys=False), encoding="utf-8"
    )
    logger.info("artifacts written to %s", run_dir)
    return run_dir
