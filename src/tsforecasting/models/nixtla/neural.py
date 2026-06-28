"""NeuralForecast 后端适配器。

负责调用 NeuralForecast 原生 ``fit`` / ``predict`` / ``cross_validation``，
并把 wide 输出归一到统一长表 artifact 契约。类接口与 stats/ml adapter 对齐，
让 workflow 可以统一调度不同 backend。

预测区间来自 quantile-loss 模型（例如 ``NHITS(loss=MQLoss)``）。上游列名
形如 ``NHITS-lo-80.0`` / ``NHITS-median``；适配器会去掉 ``.0``，并把
``median`` 归一成点预测列，再复用共享 melt helper。

耗时语义：同一 backend 的所有模型被放进一个 NeuralForecast 对象中批量执行，
因此 ``runtime_metrics`` 中这些模型共享同一组耗时。

本模块只会在 workflow 的 ``neuralforecast`` 分支里被导入，所以基础安装环境
未安装 ``neural`` extra 时仍能 import 主包。
"""

from __future__ import annotations

import time

import pandas as pd
from neuralforecast import NeuralForecast

from tsforecasting.artifacts.schema import (
    BACKTEST_PREDICTIONS_COLUMNS,
    PREDICTIONS_COLUMNS,
)
from tsforecasting.models.registry import BuiltModel
from tsforecasting.utils.frames import (
    NON_MODEL_COLS_CV,
    NON_MODEL_COLS_FORECAST,
    add_dense_horizon,
    interval_columns,
    is_pure_model_col,
    melt_forecast_long,
)


def _make_lightning_logger():
    """把 Lightning TensorBoard 日志归并到 ``logs/lightning/``。

    如果不设置，上游默认写到根目录 ``./lightning_logs/``。当前
    NeuralForecast 版本要求把 ``trainer_kwargs`` 挂到每个模型实例上，
    因此这里返回 logger 后由 adapter 合并到每个模型的 trainer_kwargs。
    """
    try:
        from lightning.pytorch.loggers import TensorBoardLogger
    except ImportError:  # 兼容较旧的 neuralforecast 依赖组合。
        from pytorch_lightning.loggers import TensorBoardLogger
    return TensorBoardLogger(save_dir="logs", name="lightning")


def _normalize_neural_cols(wide: pd.DataFrame) -> pd.DataFrame:
    """归一 NeuralForecast 列名，使共享 melt helper 能正确识别模型和区间列。

    - 区间列去掉尾部 ``.0``：``NHITS-lo-80.0`` -> ``NHITS-lo-80``。
    - quantile 模型的点预测 ``NHITS-median`` 归一为 ``NHITS``。
    """
    rename: dict[str, str] = {}
    for c in wide.columns:
        if ("-lo-" in c or "-hi-" in c) and c.endswith(".0"):
            rename[c] = c[:-2]
        elif c.endswith("-median"):
            rename[c] = c[: -len("-median")]
    return wide.rename(columns=rename) if rename else wide


class NeuralForecastAdapter:
    """把 NeuralForecast 批量输出适配成统一预测/回测长表。"""

    backend = "neuralforecast"

    def __init__(
        self,
        df: pd.DataFrame,
        built_models: list[BuiltModel],
        freq: str,
        run_id: str,
        levels: list[int] | None = None,
    ) -> None:
        self._df = df
        self._built = built_models
        self._freq = freq
        self.run_id = run_id
        self._levels = list(levels) if levels else None
        # 当前上游从每个模型的 trainer_kwargs 构造 Lightning Trainer；这里逐个
        # 合并 logger，避免遥测散落到根目录 lightning_logs/。
        lightning_logger = _make_lightning_logger()
        for m in built_models:
            tk = dict(getattr(m.instance, "trainer_kwargs", {}) or {})
            tk["logger"] = lightning_logger
            m.instance.trainer_kwargs = tk
        self._nf = NeuralForecast(models=[m.instance for m in built_models], freq=freq)
        self.timing: dict[str, float] = {
            "fit_seconds": 0.0,
            "predict_seconds": 0.0,
            "cross_validation_seconds": 0.0,
        }

    def _name_map(self, model_cols: list[str]) -> dict[str, str]:
        if len(model_cols) != len(self._built):
            raise ValueError(
                f"model column count {len(model_cols)} != built models {len(self._built)}"
            )
        return {col: self._built[i].name for i, col in enumerate(model_cols)}

    def predict(self, h: int) -> pd.DataFrame:
        t0 = time.perf_counter()
        self._nf.fit(self._df, val_size=h)
        self.timing["fit_seconds"] += time.perf_counter() - t0

        t0 = time.perf_counter()
        # quantile-loss 模型按自身 quantile 输出 lo/hi；predict 阶段不再传 level。
        fcst = self._nf.predict(h=h)
        self.timing["predict_seconds"] += time.perf_counter() - t0

        fcst = _normalize_neural_cols(fcst)
        pure = [
            c
            for c in fcst.columns
            if c not in NON_MODEL_COLS_FORECAST and is_pure_model_col(c)
        ]
        long = melt_forecast_long(fcst, NON_MODEL_COLS_FORECAST, self._name_map(pure), self._levels)
        long["backend"] = self.backend
        long["run_id"] = self.run_id
        return long[list(PREDICTIONS_COLUMNS) + interval_columns(self._levels)]

    def cross_validation(
        self, h: int, n_windows: int, step_size: int
    ) -> pd.DataFrame:
        t0 = time.perf_counter()
        if self._levels:
            cv = self._nf.cross_validation(
                df=self._df, h=h, n_windows=n_windows, step_size=step_size,
                val_size=h, level=self._levels,
            )
        else:
            cv = self._nf.cross_validation(
                df=self._df, h=h, n_windows=n_windows, step_size=step_size, val_size=h
            )
        self.timing["cross_validation_seconds"] += time.perf_counter() - t0

        cv = _normalize_neural_cols(cv)
        pure = [
            c
            for c in cv.columns
            if c not in NON_MODEL_COLS_CV and is_pure_model_col(c)
        ]
        long = melt_forecast_long(cv, NON_MODEL_COLS_CV, self._name_map(pure), self._levels)
        long["backend"] = self.backend
        long["run_id"] = self.run_id
        long = long.sort_values(["unique_id", "cutoff", "model", "ds"]).reset_index(
            drop=True
        )
        long = add_dense_horizon(long)
        return long[list(BACKTEST_PREDICTIONS_COLUMNS) + interval_columns(self._levels)]

    @property
    def model_types(self) -> dict[str, str]:
        return {m.name: m.model_type for m in self._built}
