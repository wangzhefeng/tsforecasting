"""Notebook code cell templates."""

MVP0_LOAD = """import pandas as pd
run_dir = "__RUN_DIR__"
comparison = pd.read_csv(run_dir + "/metrics/model_comparison.csv")
metrics = pd.read_csv(run_dir + "/metrics/metrics.csv")
backtest = pd.read_csv(run_dir + "/predictions/backtest.csv")
runtime = pd.read_csv(run_dir + "/metrics/runtime.csv")
"""

MVP0_RANK = "comparison.sort_values(\"rank\")"

MVP0_METRICS = """import matplotlib.pyplot as plt
pivot = metrics.pivot_table(index="model", columns="metric", values="value")
pivot.plot.bar()
plt.ylabel("error"); plt.title("Metrics by model"); plt.tight_layout(); plt.show()
"""

MVP0_BACKTEST = """import matplotlib.pyplot as plt
best = comparison.sort_values("rank")["model"].iloc[0]
sub = backtest[backtest["model"] == best].sort_values(["unique_id", "ds"])
for uid, g in sub.groupby("unique_id"):
    plt.figure()
    plt.plot(g["ds"], g["y"], label="actual")
    plt.plot(g["ds"], g["yhat"], label="forecast")
    plt.title(best + ": " + str(uid)); plt.legend(); plt.tight_layout(); plt.show()
"""

MVP0_RUNTIME = """import matplotlib.pyplot as plt
runtime.set_index("model")["total_seconds"].plot.bar()
plt.ylabel("seconds"); plt.title("Runtime by model"); plt.tight_layout(); plt.show()
"""
