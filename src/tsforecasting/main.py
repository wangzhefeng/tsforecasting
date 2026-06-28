"""本地 forecast 主入口：面向 VSCode 直接运行和类式流程调试。"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import pandas as pd

from tsforecasting.artifacts.writer import (
    ForecastArtifactWriter,
    build_manifest,
)
from tsforecasting.config import ForecastArgs, load_config, resolve_overrides
from tsforecasting.data_provider import LoadedData, load_data
from tsforecasting.evaluation.metrics import (
    build_model_comparison,
    build_runtime_metrics,
    compute_metrics,
)
from tsforecasting.models import build_models
from tsforecasting.models.nixtla import StatsForecastAdapter
from tsforecasting.models.registry import BuiltModel
from tsforecasting.utils.runtime import configure_run_environment


def _build_adapter(
    backend: str,
    df: pd.DataFrame,
    group: list[BuiltModel],
    freq: str,
    run_id: str,
    args: ForecastArgs,
):
    """按 backend 创建适配器；可选 backend 在分支内延迟导入。"""
    levels = args.prediction_intervals.levels if args.prediction_intervals else None

    if backend == "statsforecast":
        return StatsForecastAdapter(df, group, freq, run_id, levels=levels)

    if backend == "mlforecast":
        from tsforecasting.models.nixtla.ml import MLForecastAdapter

        return MLForecastAdapter(df, group, freq, run_id, args.mlforecast, levels=levels)

    if backend == "neuralforecast":
        from tsforecasting.models.nixtla.neural import NeuralForecastAdapter

        return NeuralForecastAdapter(df, group, freq, run_id, levels=levels)

    raise ValueError(f"no adapter registered for backend '{backend}'")


class ForecastRunner:
    """普通预测流程编排器。

    阶段方法按用户可理解的建模流程命名；当前 feature engineering 和 test 阶段
    只记录边界，不新增未定义的数据契约。
    """

    def __init__(self, args: ForecastArgs, *, do_predict: bool = True) -> None:
        self.args = args
        self.do_predict = do_predict
        self.stage_order: list[str] = []
        self.loaded: LoadedData | None = None
        self.built_models: list[BuiltModel] = []
        self.groups: dict[str, list[BuiltModel]] = {}
        self.predictions: pd.DataFrame | None = None
        self.backtest: pd.DataFrame | None = None
        self.metrics: pd.DataFrame | None = None
        self.runtime_metrics: pd.DataFrame | None = None
        self.model_comparison: pd.DataFrame | None = None
        self.timings: dict[str, dict[str, float]] = {}
        self.skipped_stages: dict[str, str] = {
            "test": "独立 test split 尚未配置；当前沿用 rolling-origin valid 输出。"
        }

    def _mark(self, stage: str) -> None:
        self.stage_order.append(stage)

    def parse_args(self) -> ForecastArgs:
        """接收已经解析好的 ForecastArgs，不直接耦合 argparse。"""
        self._mark("parse_args")
        return self.args

    def load_data(self) -> LoadedData:
        """读取 CSV 并转换为 Nixtla 长表。"""
        self._mark("load_data")
        self.loaded = load_data(self.args.data)
        return self.loaded

    def preprocess(self) -> LoadedData:
        """数据预处理阶段；当前标准化已在 data_provider 完成。"""
        self._mark("preprocess")
        if self.loaded is None:
            raise RuntimeError("load_data must run before preprocess")
        return self.loaded

    def feature_engineering(self) -> LoadedData:
        """特征工程阶段；MLForecast 共享特征由 adapter 根据配置构造。"""
        self._mark("feature_engineering")
        if self.loaded is None:
            raise RuntimeError("load_data must run before feature_engineering")
        return self.loaded

    def train(self) -> list[BuiltModel]:
        """实例化模型并按 backend 分组。"""
        self._mark("train")
        self.built_models = build_models(self.args)
        groups: dict[str, list[BuiltModel]] = defaultdict(list)
        for built in self.built_models:
            groups[built.backend].append(built)
        self.groups = dict(groups)
        return self.built_models

    def valid(self) -> pd.DataFrame:
        """执行 rolling-origin backtest，作为当前 valid 语义。"""
        self._mark("valid")
        if self.loaded is None:
            raise RuntimeError("load_data must run before valid")
        parts: list[pd.DataFrame] = []
        do_forecast = self.do_predict and self.args.forecast is not None
        for backend, group in self.groups.items():
            adapter = _build_adapter(
                backend,
                self.loaded.df,
                group,
                self.loaded.meta["freq"],
                self.args.run_id,
                self.args,
            )
            if do_forecast:
                forecast_h = self.args.forecast.horizon
                self._append_prediction(adapter.predict(forecast_h))
            parts.append(
                adapter.cross_validation(
                    self.args.split.horizon,
                    self.args.split.n_windows,
                    self.args.split.step_size,
                )
            )
            self.timings[backend] = adapter.timing
        self.backtest = pd.concat(parts, ignore_index=True)
        return self.backtest

    def _append_prediction(self, prediction: pd.DataFrame) -> None:
        if self.predictions is None:
            self.predictions = prediction
        else:
            self.predictions = pd.concat(
                [self.predictions, prediction], ignore_index=True
            )

    def test(self) -> None:
        """当前未配置独立 test split；manifest 中记录为 skipped。"""
        self._mark("test")

    def forecast(self) -> pd.DataFrame | None:
        """返回未来预测结果；实际预测随 adapter 训练在 valid 阶段完成。"""
        self._mark("forecast")
        if not (self.do_predict and self.args.forecast is not None):
            self.skipped_stages["forecast"] = "命令未启用 forecast 输出。"
        return self.predictions

    def _evaluate(self) -> None:
        if self.loaded is None or self.backtest is None:
            raise RuntimeError("valid must run before evaluation")
        self.metrics = compute_metrics(self.backtest, self.args.run_id)
        self.runtime_metrics = build_runtime_metrics(
            self.args.run_id,
            self.built_models,
            self.timings,
            self.loaded.meta["n_series"],
            self.loaded.meta["n_rows"],
        )
        self.model_comparison = build_model_comparison(
            self.metrics, self.runtime_metrics, self.args.evaluation.rank_metric
        )

    def _write_outputs(self) -> Path:
        if (
            self.loaded is None
            or self.backtest is None
            or self.metrics is None
            or self.runtime_metrics is None
            or self.model_comparison is None
        ):
            raise RuntimeError("evaluation must run before writing outputs")
        run_dir = Path(self.args.output.dir) / self.args.run_id
        writer = ForecastArtifactWriter(run_dir)
        writer.write_artifacts(
            backtest_predictions=self.backtest,
            metrics=self.metrics,
            runtime_metrics=self.runtime_metrics,
            model_comparison=self.model_comparison,
            predictions=self.predictions,
        )
        writer.write_data_summary(self.loaded.meta)
        manifest = build_manifest(
            self.args,
            self.loaded.meta,
            self.built_models,
            run_dir,
            self.do_predict,
            skipped_stages=self.skipped_stages,
        )
        writer.write_manifest(manifest)
        writer.write_run_config(self.args)
        return run_dir

    def run(self) -> Path:
        """执行完整流程，并把 artifact 写到 output.dir/run_id。"""
        self.parse_args()
        logger = configure_run_environment(
            self.args.runtime.log_name, self.args.runtime.log_level, self.args.seed
        )
        logger.info("starting run_id=%s", self.args.run_id)

        loaded = self.load_data()
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

        self.preprocess()
        self.feature_engineering()
        self.train()
        self.valid()
        if self.backtest is not None:
            logger.info("produced %d backtest rows", len(self.backtest))
        self.test()
        self.forecast()
        if self.predictions is not None:
            logger.info("produced %d prediction rows", len(self.predictions))
        self._evaluate()
        run_dir = self._write_outputs()
        logger.info("artifacts written to %s", run_dir)
        self._mark("run")
        return run_dir


def run_pipeline(config: ForecastArgs, *, do_predict: bool = True) -> Path:
    """迁移期函数入口；内部委托给 ForecastRunner。"""
    return ForecastRunner(config, do_predict=do_predict).run()


def main() -> None:
    """VSCode 本地运行入口：按需在这里切换示例 YAML。"""
    config_path = "configs/examples/ett_small/stats.yaml"
    args = load_config(config_path)
    resolve_overrides(args)
    run_dir = ForecastRunner(args).run()
    print(f"run complete: {run_dir}")


if __name__ == "__main__":
    main()
