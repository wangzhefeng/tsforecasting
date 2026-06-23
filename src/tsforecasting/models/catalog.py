"""Full Nixtla model catalog (Phase 2).

A data-only registry of the Nixtla model directories (statsforecast /
neuralforecast / mlforecast-sklearn) tracked by ``tsforecasting``, with each
model's source URL and validation status. This is the documentation/tracking
layer for plan §6/§9 ("full catalog with source and status"); it is independent
of ``REGISTRY`` (the ``build_model`` mvp presets) — ``cataloged`` models are not
necessarily buildable without per-model verification.

Status lifecycle: ``cataloged`` (listed, not verified) -> ``mvp_smoke``
(smoke-tested) -> ``validated`` | ``blocked`` | ``deprecated``.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

VALID_STATUSES = ("cataloged", "mvp_smoke", "validated", "blocked", "deprecated")


@dataclass(frozen=True)
class CatalogEntry:
    name: str
    backend: str
    class_path: str
    model_type: str
    status: str
    source_url: str
    dependency_group: str


# Models already smoke-tested through REGISTRY/build_model (P3-P8).
_MVP_PRESETS = frozenset(
    {
        "seasonal_naive",
        "auto_ets",
        "linear_regression",
        "ridge",
        "lasso",
        "elastic_net",
        "random_forest",
        "hist_gradient_boosting",
        "nhits",
        "nbeats",
        "nhits_quantile",
    }
)

_BACKEND_DOC = {
    "statsforecast": "https://nixtlaverse.nixtla.io/statsforecast/docs/models.html",
    "neuralforecast": "https://nixtlaverse.nixtla.io/neuralforecast/docs/models.html",
}
_BACKEND_DEP = {"statsforecast": "core", "mlforecast": "ml", "neuralforecast": "neural"}

# (name, backend, class_path, model_type)
_RAW: list[tuple[str, str, str, str]] = [
    # --- statsforecast ---
    ("seasonal_naive", "statsforecast", "statsforecast.models.SeasonalNaive", "naive"),
    ("naive", "statsforecast", "statsforecast.models.Naive", "naive"),
    ("historic_average", "statsforecast", "statsforecast.models.HistoricAverage", "naive"),
    ("random_walk_with_drift", "statsforecast", "statsforecast.models.RandomWalkWithDrift", "naive"),
    ("window_average", "statsforecast", "statsforecast.models.WindowAverage", "naive"),
    ("seasonal_window_average", "statsforecast", "statsforecast.models.SeasonalWindowAverage", "naive"),
    ("auto_ets", "statsforecast", "statsforecast.models.AutoETS", "ets"),
    ("simple_exp_smoothing", "statsforecast", "statsforecast.models.SimpleExponentialSmoothing", "exponential"),
    ("simple_exp_smoothing_optimized", "statsforecast", "statsforecast.models.SimpleExponentialSmoothingOptimized", "exponential"),
    ("seasonal_exp_smoothing", "statsforecast", "statsforecast.models.SeasonalExponentialSmoothing", "exponential"),
    ("seasonal_exp_smoothing_optimized", "statsforecast", "statsforecast.models.SeasonalExponentialSmoothingOptimized", "exponential"),
    ("holt", "statsforecast", "statsforecast.models.Holt", "exponential"),
    ("holt_winters", "statsforecast", "statsforecast.models.HoltWinters", "exponential"),
    ("theta", "statsforecast", "statsforecast.models.Theta", "theta"),
    ("optimized_theta", "statsforecast", "statsforecast.models.OptimizedTheta", "theta"),
    ("dynamic_theta", "statsforecast", "statsforecast.models.DynamicTheta", "theta"),
    ("dynamic_optimized_theta", "statsforecast", "statsforecast.models.DynamicOptimizedTheta", "theta"),
    ("auto_theta", "statsforecast", "statsforecast.models.AutoTheta", "theta"),
    ("arima", "statsforecast", "statsforecast.models.ARIMA", "arima"),
    ("auto_arima", "statsforecast", "statsforecast.models.AutoARIMA", "arima"),
    ("auto_regressive", "statsforecast", "statsforecast.models.AutoRegressive", "arima"),
    ("auto_ces", "statsforecast", "statsforecast.models.AutoCES", "ces"),
    ("croston_classic", "statsforecast", "statsforecast.models.CrostonClassic", "croston"),
    ("croston_optimized", "statsforecast", "statsforecast.models.CrostonOptimized", "croston"),
    ("croston_sba", "statsforecast", "statsforecast.models.CrostonSBA", "croston"),
    ("adida", "statsforecast", "statsforecast.models.ADIDA", "croston"),
    ("imapa", "statsforecast", "statsforecast.models.IMAPA", "croston"),
    ("tsb", "statsforecast", "statsforecast.models.TSB", "croston"),
    ("auto_mfles", "statsforecast", "statsforecast.models.AutoMFLES", "mfles"),
    ("mfles", "statsforecast", "statsforecast.models.MFLES", "mfles"),
    ("mstl", "statsforecast", "statsforecast.models.MSTL", "decomposition"),
    ("tbats", "statsforecast", "statsforecast.models.TBATS", "tbats"),
    ("auto_tbats", "statsforecast", "statsforecast.models.AutoTBATS", "tbats"),
    ("garch", "statsforecast", "statsforecast.models.GARCH", "garch"),
    ("arch", "statsforecast", "statsforecast.models.ARCH", "garch"),
    # --- neuralforecast ---
    ("nhits", "neuralforecast", "neuralforecast.models.NHITS", "neural"),
    ("nhits_quantile", "neuralforecast", "neuralforecast.models.NHITS", "neural_quantile"),
    ("nbeats", "neuralforecast", "neuralforecast.models.NBEATS", "neural"),
    ("nbeatsx", "neuralforecast", "neuralforecast.models.NBEATSx", "neural"),
    ("dlinear", "neuralforecast", "neuralforecast.models.DLinear", "neural"),
    ("nlinear", "neuralforecast", "neuralforecast.models.NLinear", "neural"),
    ("mlp", "neuralforecast", "neuralforecast.models.MLP", "neural"),
    ("mlp_multivariate", "neuralforecast", "neuralforecast.models.MLPMultivariate", "neural"),
    ("rnn", "neuralforecast", "neuralforecast.models.RNN", "neural"),
    ("lstm", "neuralforecast", "neuralforecast.models.LSTM", "neural"),
    ("gru", "neuralforecast", "neuralforecast.models.GRU", "neural"),
    ("dilated_rnn", "neuralforecast", "neuralforecast.models.DilatedRNN", "neural"),
    ("tcn", "neuralforecast", "neuralforecast.models.TCN", "neural"),
    ("bitcn", "neuralforecast", "neuralforecast.models.BiTCN", "neural"),
    ("tft", "neuralforecast", "neuralforecast.models.TFT", "neural"),
    ("deepar", "neuralforecast", "neuralforecast.models.DeepAR", "neural"),
    ("deepnpts", "neuralforecast", "neuralforecast.models.DeepNPTS", "neural"),
    ("informer", "neuralforecast", "neuralforecast.models.Informer", "neural"),
    ("autoformer", "neuralforecast", "neuralforecast.models.Autoformer", "neural"),
    ("fedformer", "neuralforecast", "neuralforecast.models.FEDformer", "neural"),
    ("patchtst", "neuralforecast", "neuralforecast.models.PatchTST", "neural"),
    ("itransformer", "neuralforecast", "neuralforecast.models.iTransformer", "neural"),
    ("vanilla_transformer", "neuralforecast", "neuralforecast.models.VanillaTransformer", "neural"),
    ("timesnet", "neuralforecast", "neuralforecast.models.TimesNet", "neural"),
    ("timemixer", "neuralforecast", "neuralforecast.models.TimeMixer", "neural"),
    ("tsmixer", "neuralforecast", "neuralforecast.models.TSMixer", "neural"),
    ("tsmixerx", "neuralforecast", "neuralforecast.models.TSMixerx", "neural"),
    ("tide", "neuralforecast", "neuralforecast.models.TiDE", "neural"),
    ("timexer", "neuralforecast", "neuralforecast.models.TimeXer", "neural"),
    ("timellm", "neuralforecast", "neuralforecast.models.TimeLLM", "neural"),
    ("stemgnn", "neuralforecast", "neuralforecast.models.StemGNN", "neural"),
    ("softs", "neuralforecast", "neuralforecast.models.SOFTS", "neural"),
    ("kan", "neuralforecast", "neuralforecast.models.KAN", "neural"),
    ("rmok", "neuralforecast", "neuralforecast.models.RMoK", "neural"),
    ("xlstm", "neuralforecast", "neuralforecast.models.xLSTM", "neural"),
    # --- mlforecast (sklearn-compatible estimators) ---
    ("linear_regression", "mlforecast", "sklearn.linear_model.LinearRegression", "linear"),
    ("ridge", "mlforecast", "sklearn.linear_model.Ridge", "linear"),
    ("lasso", "mlforecast", "sklearn.linear_model.Lasso", "linear"),
    ("elastic_net", "mlforecast", "sklearn.linear_model.ElasticNet", "linear"),
    ("random_forest", "mlforecast", "sklearn.ensemble.RandomForestRegressor", "tree"),
    ("hist_gradient_boosting", "mlforecast", "sklearn.ensemble.HistGradientBoostingRegressor", "tree"),
    ("kneighbors", "mlforecast", "sklearn.neighbors.KNeighborsRegressor", "neighbors"),
    ("svr", "mlforecast", "sklearn.svm.SVR", "svm"),
]


def _source_url(backend: str, class_path: str) -> str:
    if backend == "mlforecast":
        return f"https://scikit-learn.org/stable/modules/generated/{class_path}.html"
    return _BACKEND_DOC[backend]


def _status(name: str) -> str:
    return "mvp_smoke" if name in _MVP_PRESETS else "cataloged"


CATALOG: list[CatalogEntry] = [
    CatalogEntry(
        name=name,
        backend=backend,
        class_path=class_path,
        model_type=model_type,
        status=_status(name),
        source_url=_source_url(backend, class_path),
        dependency_group=_BACKEND_DEP[backend],
    )
    for (name, backend, class_path, model_type) in _RAW
]


def list_catalog(
    backend: str | None = None, status: str | None = None
) -> list[CatalogEntry]:
    """Filter the catalog by backend and/or status."""
    return [
        e
        for e in CATALOG
        if (backend is None or e.backend == backend)
        and (status is None or e.status == status)
    ]


def generate_catalog_md() -> str:
    """Render the catalog as a markdown document (one table per backend)."""
    counts = Counter(e.status for e in CATALOG)
    status_line = ", ".join(f"{s}={counts.get(s, 0)}" for s in VALID_STATUSES)
    lines = [
        "# Model catalog",
        "",
        "Full Nixtla model directory tracked by `tsforecasting`, with source URL"
        " and validation status. Independent of the build-time `REGISTRY` presets"
        " — `cataloged` models are listed but not verified runnable.",
        "",
        f"**Status counts**: {status_line}  (total = {len(CATALOG)})",
        "",
    ]
    for backend in ("statsforecast", "mlforecast", "neuralforecast"):
        entries = sorted(list_catalog(backend=backend), key=lambda e: e.name)
        lines.append(f"## {backend} ({len(entries)})")
        lines.append("")
        lines.append("| name | class_path | model_type | status | source |")
        lines.append("| --- | --- | --- | --- | --- |")
        for e in entries:
            lines.append(
                f"| {e.name} | `{e.class_path}` | {e.model_type} | {e.status}"
                f" | [doc]({e.source_url}) |"
            )
        lines.append("")
    return "\n".join(lines)
