"""端到端 workflow 公开入口。"""

from tsforecasting.main import run_pipeline


def run_forecast_workflow(config, *, do_predict: bool = True):
    """迁移期别名：普通 forecast workflow 统一委托给 ForecastRunner。"""
    return run_pipeline(config, do_predict=do_predict)

__all__ = [
    "run_forecast_workflow",
    "run_pipeline",
]
