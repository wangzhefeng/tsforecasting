"""Notebook code cell templates."""

MVP0_LOAD = """import pandas as pd
run_dir = "__RUN_DIR__"
comparison = pd.read_csv(run_dir + "/model_comparison.csv")
metrics = pd.read_csv(run_dir + "/metrics.csv")
backtest = pd.read_csv(run_dir + "/backtest_predictions.csv")
runtime = pd.read_csv(run_dir + "/runtime_metrics.csv")
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

HIER_LOAD = """import pandas as pd
run_dir = "__RUN_DIR__"
diag = pd.read_csv(run_dir + "/reconciliation_diagnostics.csv")
base = pd.read_csv(run_dir + "/base_predictions.csv")
reconciled = pd.read_csv(run_dir + "/reconciled_predictions.csv")
"""

HIER_LEVELS = """import json
manifest = json.load(open(run_dir + "/manifest.json"))
manifest["hierarchy_levels"]
"""

HIER_DIAG = "diag.sort_values(\"mse\")"

HIER_MSE = """import matplotlib.pyplot as plt
diag.set_index("reconciler")["mse"].plot.bar()
plt.ylabel("mse"); plt.title("Reconciler MSE"); plt.tight_layout(); plt.show()
"""

HIER_RECONCILED = """import matplotlib.pyplot as plt
total = reconciled[reconciled["unique_id"] == "total"].sort_values(["reconciler", "ds"])
for rec, g in total.groupby("reconciler"):
    plt.plot(g["ds"], g["yhat"], label=rec)
base_total = base[base["unique_id"] == "total"].sort_values("ds")
plt.plot(base_total["ds"], base_total["yhat"], label="base", linestyle="--")
plt.title("Reconciled vs base (total)"); plt.legend(); plt.tight_layout(); plt.show()
"""
