# LOG.md

本文件用于记录 `tsforecasting` 框架开发日志。日志按时间倒序维护，只记录真实发生的开发、文档、验证和修复过程，不追溯伪造历史记录。

## 记录规则

- 每次实施完成后追加一条日志，优先记录用户可复查的事实。
- 方案范围、架构边界、MVP 目标等变化记录在当前方案版本文档的“方案调整记录”。
- 具体计划项状态记录在 `docs/PLAN.md` 的“计划项实现记录”。
- 日志条目应包含日期、类型、摘要、涉及文件、验证命令、结果和下一步。

## 2026-06-23 - P9 TourismSmall hierarchical reconciliation 完成（MVP-1 收尾）

- 类型：impl（mvp-1 / P9）
- 摘要：接入 TourismSmall 层级协调，**独立流程**（不复用 MVP-0 `Config`/`run_pipeline`，因数据源、配置结构与 artifact 契约均不同）。新增 `config/hierarchical.py`（`HierarchicalConfig`：`data.source/dataset/freq/cache_dir`、`base_forecast.backend/models/horizon`、`hierarchical.reconcilers/diagnostics`、`evaluation` 限 `[mse]`；不复用 `Config`，但复用 `ModelConfig`/`RuntimeConfig`/`ArtifactsConfig` 与 schema 的私有 builder）；`data/hierarchical.py`（`load_hierarchical` 取 `Y_df/S_df/tags` 并 `S_df.reset_index(names="unique_id")`）；`reconciliation.py`（`reconcile_pipeline`：StatsForecast wide base forecast → 逐 reconciler `HierarchicalReconciliation.reconcile` → coherence 自验 `S(nodes×bottom)@y_bottom ≈ y_rec`（atol 1e-6）+ mse vs hold-out；reconciler 用 importlib 从 `{name,class,params}` spec 实例化，**不进 REGISTRY**，同 MLForecast target_transforms 模式）；`orchestration/reconcile.py`（`run_reconciliation`：hold-out `horizon` 步 split + 全流程 + 写 artifact/manifest/run_config）；`artifacts/{schema,writer,__init__}` 增 `base_predictions`/`reconciled_predictions`/`reconciliation_diagnostics` 三契约 + hierarchical manifest；CLI 新增 `reconcile` 子命令（+run-level overrides/`--dry-run`）；示例 `configs/examples/tourism_small_hierarchical.yaml`（`seasonal_naive` base + BottomUp/MinTrace/TopDown/MiddleOut）。
- hierarchicalforecast 1.5.1 / datasetsforecast 1.0.1 spike 结论（关键）：
  - TourismSmall 实测**季度 `QE-DEC`**——v2 §8 的 `freq: QE` 正确（WebSearch 误指 monthly，已忽略）。
  - `HierarchicalData.load(directory, group, cache)` **实际返回 3 值 (Y_df, S_df, tags)**，签名标注错为 2 元组；`group="TourismSmall"`。
  - `S_df` 节点名在 index（`reset_index` 前无 `unique_id` 列），`reconcile` 要求 `unique_id` 为列 → adapter 内 `reset_index(names="unique_id")`。
  - `tags` 4 层 key：`Country`(1)/`Country/Purpose`(4)/`Country/Purpose/State`(28)/`Country/Purpose/State/CityNonCity`(56 bottom)，正是 v2 §8 MiddleOut `middle_level` 合法取值。
  - reconciler 构造：`BottomUp` 无参；`MinTrace(method=...)` method 必填；`TopDown(method=...)` 必填；`MiddleOut(middle_level, top_down_method)` 都必填。
  - **`top_down_method` 合法值 = `average_proportions`/`forecast_proportions`/`proportion_averages`**；`avg_proportions` 非法。v2 §8 原写 `avg_proportions`（P0.3 误把合法的 `proportion_averages` 当非法、改成非法的 `avg_proportions`）→ 本轮修回 `average_proportions` 并更新合法值清单（同步 §8 + §11 调整记录）。
  - `reconcile(..., diagnostics=True)` 原生做 coherence 验证；reconcile 输出 wide，列名 `{base_alias}/{reconciler}_{param}-{value}`（MiddleOut 的 middle_level 值含 `/` 故用 `split("/",1)[0]` 取 base_alias），逐 reconciler 单独 reconcile 以便用配置的 `spec.name` 标 reconciler 列。
- 关键决策（用户四问四答）：(1) **独立形态**（新 `reconcile` 子命令 + 独立 config/pipeline/artifacts，不污染 MVP-0）；(2) **base 复用现有 `seasonal_naive`/`auto_ets`**（零 registry 改动，不为 P9 扩 naive/auto_arima）；(3) **4 个 reconciler 含 MinTrace**（业界标杆，spike 验证可用）；(4) **指标 `[mse]`**（忠于 v2 §8，不擅自扩展）。
- 涉及文件：`src/tsforecasting/config/hierarchical.py`（新）、`src/tsforecasting/data/hierarchical.py`（新）、`src/tsforecasting/reconciliation.py`（新）、`src/tsforecasting/orchestration/reconcile.py`（新）、`src/tsforecasting/artifacts/{schema,writer,__init__}.py`、`src/tsforecasting/data/__init__.py`、`src/tsforecasting/orchestration/__init__.py`、`src/tsforecasting/cli/__init__.py`、`configs/examples/tourism_small_hierarchical.yaml`（新）、`tests/unit/test_hierarchical.py`（新）、`tests/unit/test_reconciliation.py`（新）、`tests/integration/test_reconcile_smoke.py`（新）、`.gitignore`（`datasetsforecast_cache/`）、`docs/unified-ts-framework-plan-v2.md`（§8 top_down_method + §11 记录）。
- 验证命令：

```bash
uv sync --extra hierarchical
uv run tsforecasting reconcile --config configs/examples/tourism_small_hierarchical.yaml --dry-run
uv run tsforecasting reconcile --config configs/examples/tourism_small_hierarchical.yaml
uv run pytest -q          # hierarchical env：65 passed, 3 skipped；base env（uv sync）：59 passed, 6 skipped
uv run ruff check .       # All checks passed
```

- 结果：通过（TDD：contract→config→reconciliation→integration 四轮 RED-GREEN）。真实 reconcile on TourismSmall：89 series / 3204 rows / 4 levels，hold-out split train/test=2848/356（horizon=4），产出 5 个 artifact（3 CSV + manifest + run_config）；`reconciliation_diagnostics.csv` 四 reconciler 全 `coherent=True`，`middle_out_state` mse=674088 最优（< bottom_up/top_down/min_trace 的 677674）；manifest 含 4 层 `hierarchy_levels` 与 4 个 reconciler provenance。单元测试用合成 2 层层级（total=b1+b2）验证 reconcile+coherence+mse 逻辑、不下载。base env（无 hierarchical extra）base 包仍可 import（含 `run_reconciliation` 路径）、hierarchical/neural/ml 测试跳过，lazy-import 不变量成立。**MVP-1（P7-P9）全部达成**。
- 下一步：MVP-1 完成。P10 reporting（Phase 2，非阻塞）；P11 阶段性 smoke 验收与文档同步；之后可进入 Phase 2（full catalog / Jupyter reporting / 更多模型）。

## 2026-06-23 - P8 NeuralForecast CPU smoke backend 完成（MVP-1）

- 类型：impl（mvp-1 / P8）
- 摘要：接入 NeuralForecast CPU smoke 后端，进入统一 metrics/comparison。`config/schema.py` `SUPPORTED_BACKENDS` 增 `neuralforecast`（**无顶层 section**——与 MLForecast 不同，NeuralForecast 的训练超参挂在每个模型实例上，走现有 `models[].params` → `build_model(cls(**params))` 路径）。`models/registry.py` 注册 `nhits`+`nbeats` 两个 preset（`dependency_group="neural"`、`class_path` 指向 `neuralforecast.models.NHITS`/`NBEATS`、`model_type="neural"`）。新增 `models/nixtla/neural.py` `NeuralForecastAdapter`，逐行镜像 `StatsForecastAdapter`/`MLForecastAdapter`：相同 `predict`/`cross_validation` surface、wide→long melt、按列序位置映射 model 名、dense-rank `horizon` 派生、batched 计时；复用 stats.py 的 `NON_MODEL_COLS_*`。`orchestration/run.py` `_build_adapter` 增 `neuralforecast` 分支（lazy import，签名同 StatsForecastAdapter，无额外 config）。不改 CLI、不改 manifest 结构（模型已带 `backend`）。新示例 `configs/examples/ett_small_neural.yaml`（statsforecast `seasonal_naive` + `nhits`，`h:24`/`input_size:48`/`max_steps:50`/`enable_progress_bar:false`/`random_seed:0`）。
- neuralforecast 3.1.9 API spike 结论（关键）：
  - `NeuralForecast(models, freq, ...)` 构造只需 `freq`（adapter 接 `loaded.meta["freq"]`），训练超参（`h`/`input_size`/`max_steps`/`enable_progress_bar`/`random_seed`）都在模型实例上。
  - `inspect.signature` 显示 NHITS/NBEATS 的 `trainer_kwargs` 为必填，但实测 `NHITS(h=24, input_size=48, max_steps=5)` 可正常构造（内部有默认）；`enable_progress_bar=False` 作为模型参数被接受（保持 pytest 输出干净）。
  - `predict(df=None, h=None, ...)` 与 `cross_validation(df=None, h=None, n_windows=1, step_size=1, val_size=0, refit=False, ...)` **都接受 `h`** → adapter 显式传 `h`（解决「predict 长度由模型 h 决定」的歧义，统一用 config 的 horizon）。
  - `val_size` 默认 0；adapter 给 `fit` 与 `cross_validation` 都传 `val_size=h`，开始处理 NeuralForecast 验证语义但不改 MVP-0 backtest 契约。
  - 依赖：`neuralforecast 3.1.9` / `torch 2.12.1`（Mac MPS 可用），`uv sync --extra neural` 无版本冲突（P1 spike 已锁 `pandas<3`/`numpy<2.5`）。
- 关键决策（用户三问三答均选 A）：(1) 配置形态=模型级参数无顶层 section（因 NeuralForecast 超参挂模型实例，非 MLForecast 那种框架共享 lags）；(2) 验证=现在 `uv sync --extra neural` + 全量 smoke；(3) 预设=注册 `nhits`+`nbeats` 两个、smoke 只跑 `nhits`。device 不强制 CPU（MPS 可用），测试靠 `seed`/`random_seed`+小 `max_steps` 保证可复现。
- 涉及文件：`src/tsforecasting/config/schema.py`、`src/tsforecasting/models/registry.py`、`src/tsforecasting/models/nixtla/neural.py`（新）、`src/tsforecasting/orchestration/run.py`、`configs/examples/ett_small_neural.yaml`（新）、`tests/unit/test_neural_backend.py`（新）、`tests/unit/test_registry.py`、`tests/unit/test_config.py`。
- 验证命令：

```bash
uv sync --extra neural
uv run tsforecasting validate-config --config configs/examples/ett_small_neural.yaml
uv run tsforecasting run --config configs/examples/ett_small_neural.yaml
uv run pytest -q          # neural env：50 passed, 3 skipped；base env（uv sync）：47 passed, 4 skipped
uv run ruff check .       # All checks passed
```

- 结果：通过（TDD：config→registry→adapter 三轮 RED-GREEN）。混合 run 在 ETTh1 产出 7 个 artifact；`model_comparison.csv` 跨 backend 统一排名——`nhits`（neuralforecast）mae=0.938 rank1 胜 `seasonal_naive`（statsforecast）mae=1.422 rank2；训练 `Trainer.fit stopped: max_steps=50 reached`（受控）；`runtime_metrics` 按 backend 分别计时（nhits ~4.0s 含 fit 2.4s + cv 1.6s，seasonal_naive ~0.02s）；48 prediction rows（24×2）、144 backtest rows（24×3×2）。base env（无 neural extra）base 包仍可 import、neural/ml 测试跳过，lazy-import 不变量成立。skip 计数差异（neural env 3 vs base env 4）由模块级 `importorskip` 在 neuralforecast 缺失时把 3 个 neural 测试折叠为 1 个 skip item 造成，行为正确。
- 下一步：P9 TourismSmall hierarchical reconciliation（加载 `Y_df`/`S_df`/`tags`，调用 HierarchicalForecast reconciliation，保存 base/reconciled forecasts 与 coherence diagnostics）。

## 2026-06-23 - P7 MLForecast backend 完成（MVP-1）

- 类型：impl（mvp-1 / P7）
- 摘要：接入 MLForecast sklearn preset 后端，进入统一 metrics/comparison。`config/schema.py` 增 `mlforecast` backend 与顶层 `MLForecastConfig`（`lags`/`date_features`/`target_transforms`，后者为可序列化 `{class,args?,kwargs?}` spec，由 adapter 解析实例化，保持 `run_config.yaml` YAML-safe）；校验：有 `mlforecast` 模型则必须有顶层 `mlforecast.lags` 非空。`models/registry.py` 注册 6 个 sklearn preset（`linear_regression`/`ridge`/`lasso`/`elastic_net`/`random_forest`/`hist_gradient_boosting`，`dependency_group="ml"`，`class_path` 指向 sklearn regressor，`build_model` 用 `cls(**params)` 实例化、adapter 再包进 `MLForecast`）。新增 `models/nixtla/ml.py` `MLForecastAdapter`，逐行镜像 `StatsForecastAdapter`：相同 `predict`/`cross_validation`、wide→long melt、按列序位置映射 model 名、dense-rank `horizon` 派生、batched 计时。`orchestration/run.py` 改为按 backend 分组建适配器（`mlforecast` 分支 lazy import），concat predictions/backtest 后统一评估排名。`evaluation/metrics.py` `build_runtime_metrics` 改 `timings: dict[backend->timing]`。`artifacts/writer.py` manifest 增条件 `mlforecast` provenance 键。新示例 `configs/examples/ett_small_ml.yaml`（statsforecast + mlforecast 混合 + `Differences([24])` target transform）。
- mlforecast 1.0.31 API spike 结论（关键）：
  - 构造函数 `MLForecast(models, freq, lags=None, lag_transforms=None, date_features=None, num_threads=1, target_transforms=None, ...)` —— **`freq` 为必填位置参数**（adapter 接 `loaded.meta["freq"]`）。
  - `predict(h)` 位置参数；`cross_validation(df, n_windows, h, step_size=None, ...)`（`n_windows` 在 `h` 前，故用关键字调用）。
  - predict 产 `unique_id, ds, <模型列>`；cv 产 `unique_id, ds, cutoff, y, <模型列>`；**输出列序与 `models=` 列表序一致** → stats.py 的按位置 `_name_map` 直接复用，无需改动。列名按 class 名（同类重复加数字后缀，6 个不同 preset 不冲突）。
  - 依赖：`mlforecast 1.0.31` / `scikit-learn 1.9.0` / `utilsforecast 0.2.16` 已在 `uv.lock`，`uv sync --extra ml` 无版本冲突（P1 spike 已锁 `pandas<3`/`numpy<2.5` 兼容）。
- 关键决策：用户确认范围为「full multi-backend mixed run」+「full v1 preset list」+「本轮接入 target_transforms」。lazy import 保证无 `ml` extra 时包仍可 import；ml 相关测试用 `pytest.importorskip("mlforecast"/"sklearn")` 跳过。
- 涉及文件：`src/tsforecasting/config/schema.py`、`src/tsforecasting/config/__init__.py`、`src/tsforecasting/models/registry.py`、`src/tsforecasting/models/nixtla/ml.py`（新）、`src/tsforecasting/orchestration/run.py`、`src/tsforecasting/evaluation/metrics.py`、`src/tsforecasting/artifacts/writer.py`、`configs/examples/ett_small_ml.yaml`（新）、`tests/unit/test_ml_backend.py`（新）、`tests/unit/test_registry.py`、`tests/unit/test_config.py`、`tests/integration/test_run_smoke.py`。
- 验证命令：

```bash
uv sync --extra ml
uv run tsforecasting validate-config --config configs/examples/ett_small_ml.yaml
uv run tsforecasting run --config configs/examples/ett_small_ml.yaml --run-id ml-smoke
uv run pytest -q          # 51 passed（with ml extra）；base env 45 passed, 3 skipped
uv run ruff check .       # All checks passed
```

- 结果：通过。混合 run 在 ETTh1 产出 7 个 artifact；`model_comparison.csv` 跨 backend 排名（`linear_regression` mae=1.241 rank1 胜 `seasonal_naive` mae=1.422 rank2 胜 `random_forest` mae=1.453 rank3）；`runtime_metrics` 按 backend 分别计时（statsforecast 0.013s，mlforecast 9.49s 两模型共享）；manifest 含 `mlforecast` provenance 键与 `per_backend_seed={statsforecast,mlforecast}`；`target_transforms` `Differences([24])` 正常。base env（无 ml extra）ml 测试跳过、stats/config 测试全绿，lazy-import 不变量成立。
- 下一步：P8 NeuralForecast CPU smoke（`NHITS`/`NBEATS`，受控训练步数 + `val_size` 语义）。

## 2026-06-23 - P2–P6 MVP-0 纵切面完成

- 类型：impl（mvp-0 / P2–P6）
- 摘要：完成 StatsForecast 端到端纵切面。P2：`src/tsforecasting/config/schema.py`（stdlib dataclasses + 手写校验，无 pydantic；`load_config`/`validate`/`generate_run_id`/`resolve_overrides`）+ 示例配置 `configs/examples/ett_small_stats.yaml` + CLI `validate-config`。P3：`src/tsforecasting/data/loader.py`（CSV→`unique_id/ds/y`；字段映射；`id_col` 空→`series_0`；重复时间戳报错；freq 显式或可推断；缺失点计数不填充）+ `artifacts/schema.py` 列契约。P4：`src/tsforecasting/models/registry.py`（注册 `seasonal_naive`/`auto_ets`，`build_models` 动态 import）。P5：`src/tsforecasting/models/nixtla/stats.py`（`StatsForecastAdapter` 复用原生 `fit`/`predict`/`cross_validation`，wide→long 归一，`horizon` 由 dense rank 派生，batched 计时）。P6：`evaluation/metrics.py`（UtilsForecast `evaluate`→4 核心 metrics long + ranking wide）+ `artifacts/writer.py`（5 CSV + manifest + run_config）+ `orchestration/run.py` + CLI `run`/`backtest`/`--dry-run`。
- 关键决策：CLI 用 stdlib argparse；`metrics.csv` long form（`run_id,backend,model,metric,value`），`model_comparison.csv` 由其 pivot+排名+join 耗时；计时 batch-shared（StatsForecast 一次 fit 多模型，runtime_metrics 每模型复用同一计时，文档化）；`run_dir = output_dir/run_id`。
- 修复点：data loader 空 DataFrame 标量赋值导致 `unique_id` 为 NaN（改 `index=range(n)` 预建行数）；`yaml.safe_dump` 不接受 `allow_nan`（移除）；logging 单测在集成测试污染全局 logger/env 后失败（autouse fixture 重置 env + 清默认 logger handler；lazy 保证改用 subprocess 进程隔离验证，避免 pytest `LogCaptureHandler` 干扰）。
- 涉及文件：`src/tsforecasting/{config,data,models,evaluation,artifacts,orchestration,utils,cli}/**`、`configs/examples/ett_small_stats.yaml`、`tests/unit/test_{config,data_loader,registry,stats_backend,logging}.py`、`tests/integration/test_run_smoke.py`。
- 验证命令：

```bash
uv run tsforecasting validate-config --config configs/examples/ett_small_stats.yaml
uv run tsforecasting run --config configs/examples/ett_small_stats.yaml
uv run pytest -q          # 40 passed
uv run ruff check .       # All checks passed
```

- 结果：通过。端到端 `run` 在 ETTh1 上产出 7 个 artifact；`auto_ets`（mae=1.054, rank1）胜 `seasonal_naive`（mae=1.42）；manifest 含全部 provenance 键。MVP-0 成功标准全部达成。
- 下一步：MVP-1（P7 MLForecast、P8 NeuralForecast CPU smoke、P9 TourismSmall 层级验证）。

## 2026-06-23 - P1 工程脚手架与 dependency spike

- 类型：impl（mvp-0 / P1）
- 摘要：开 `feat/mvp-0-statsforecast` 分支，落地 MVP-0 工程脚手架并跑通 dependency spike 闸门。重写 `pyproject.toml`（hatchling + `src/` 布局、`[project.scripts] tsforecasting`、base=`statsforecast`/`utilsforecast`/`pyyaml`/`numpy`/`pandas`、extras `ml`/`neural`/`hierarchical`/`plot`、dev=`pytest`/`ruff`、ruff+pytest 配置）。Vendor `utils/log_util.py` 行为契约到 `src/tsforecasting/utils/logging.py`：lazy（首调 `get_logger()` 才建 handler/mkdir）、幂等（不重复挂 handler）、日志根目录 CWD 相对、保留 `SERVICE_LOG_LEVEL`/`LOG_NAME`。argparse CLI 骨架暴露 `validate-config`/`run`/`backtest`（run/backtest 含 `--run-id`/`--output-dir`/`--log-name`/`--log-level`/`--dry-run`）。下载完整 `examples/ett_small/ETTh1.csv`。
- dependency spike 结论（关键）：
  - `statsforecast` 与 `utilsforecast` 上游硬钉 `pandas<3.0.0`（已核实 main 分支 pyproject），原 `pandas>=3.0.3` 无法解析 → pin `pandas>=2.2,<3`（解析为 2.3.3）。
  - `statsforecast 2.0.3` 经 marker 在 py3.12 上传递依赖 `numba>=0.55.0`；numba 0.65.1 钉 `numpy<2.5`，而项目 resolver 默认取最新 `numpy 2.5.0` 导致 (numba, numpy) 冲突并错误回退到 `statsforecast 0.7.1`（numba 0.53.1 / llvmlite 0.36.0 在 py3.12 构建失败）→ pin `numpy>=1.26,<2.5`（解析为 2.4.6）。
  - 最终解析：`statsforecast 2.0.3` / `utilsforecast 0.2.16` / `pandas 2.3.3` / `numpy 2.4.6` / `numba 0.65.1` / `llvmlite 0.47.0` / `scipy 1.15.3`。pandas-3 升级单列为后续独立任务。
- 涉及文件：
  - `pyproject.toml`
  - `uv.lock`
  - `.gitignore`
  - `examples/ett_small/ETTh1.csv`
  - `src/tsforecasting/__init__.py`
  - `src/tsforecasting/utils/__init__.py`、`src/tsforecasting/utils/logging.py`
  - `src/tsforecasting/cli/__init__.py`
  - `tests/__init__.py`、`tests/unit/__init__.py`、`tests/integration/__init__.py`、`tests/unit/test_logging.py`
- 验证命令：

```bash
uv sync
uv run python -c "from statsforecast import StatsForecast; from statsforecast.models import SeasonalNaive, AutoETS; from utilsforecast.evaluation import evaluate; from utilsforecast.losses import mae, rmse, mape, smape; print('ok')"
uv run tsforecasting --help
uv run tsforecasting run --help
uv run pytest -q
```

- 结果：通过。`uv sync` 解析 statsforecast 2.0.3（pandas 2.3.3 / numpy 2.4.6 / numba 0.65.1）；导入与 SeasonalNaive 微 forecast 正常；`tsforecasting --help` 列出三子命令；`pytest` 7 passed（logging：lazy、幂等、env 生效、不传播）。
- 下一步：P2 — YAML schema + `validate-config` + run_id/seed。

## 2026-06-23 - 知识入口 neat-freak 同步

- 类型：docs
- 摘要：按 neat-freak 审查知识入口一致性。v1 已被 v2 取代，但 `CLAUDE.md` / `AGENTS.md` / `README.md` 的 v1 指针只写了"不要覆盖"，未传达"不要按 v1 §5 模块图 / §6 catalog 实施"的硬规则。收紧三处 v1 指针为"已被 v2 取代，仅作设计史保留，勿据其 §5/§6 实施"。无新增历史叙事、净行数 0。
- 涉及文件：
  - `CLAUDE.md`
  - `AGENTS.md`
  - `README.md`
- 验证命令：

```bash
git --no-pager diff -- CLAUDE.md AGENTS.md README.md
git diff --check -- CLAUDE.md AGENTS.md README.md
rg -n "今天|昨天|最近|today|yesterday|recently" CLAUDE.md AGENTS.md README.md docs/*.md
```

- 结果：通过。三处 v1 指针已标注 superseded；净行数 0（同行改写）；全仓无相对时间引用；`git diff --check` 无报错。
- 下一步：从 P1 开始 MVP-0 工程脚手架。

## 2026-06-23 - v2 方案与计划评审修订

- 类型：docs
- 摘要：按方案评审结论修订 v2/v1/PLAN，修复 P0 硬 bug（示例数据 ETTm1→ETTh1 频率、TourismSmall MiddleOut 参数取值），补依赖 extras 分组、MVP-0 CLI 语义、输出契约派生规则（horizon/rank_metric）、manifest seed/run_id，v1 加 SUPERSEDED banner，`metrics.json` 推迟 MVP-0b，P1 增 dependency spike + logging vendor 子动作。
- 涉及文件：
  - `docs/unified-ts-framework-plan-v2.md`
  - `docs/unified-ts-framework-plan-v1.md`
  - `docs/PLAN.md`
  - `docs/LOG.md`
- 验证命令：

```bash
python3 - <<'PY'
from pathlib import Path
for path in ["docs/unified-ts-framework-plan-v2.md", "docs/unified-ts-framework-plan-v1.md", "docs/PLAN.md", "docs/LOG.md"]:
    text = Path(path).read_text()
    fence = "`" * 3
    print(f"{path}: fence_even={text.count(fence) % 2 == 0}")
PY
rg -n "ETTh1|avg_proportions|SUPERSEDED|dependency spike|run_id" docs/unified-ts-framework-plan-v2.md docs/unified-ts-framework-plan-v1.md docs/PLAN.md
git diff --check -- docs
```

- 结果：通过。三份文档代码围栏闭合、无尾随空白、`git diff --check` 无报错；v2 §5.3 已用 `ETTh1.csv`、§8 MiddleOut 已用 `avg_proportions`、§4/§5.2/§7/§10 已补 extras/CLI/输出契约/seed-run_id/pandas 兼容风险、v1 顶部 SUPERSEDED banner 就位、PLAN.md P1 含 dependency spike + logging vendor、P0.3 评审记录与 MVP-0 标准已同步。
- 下一步：从 P1 开始 MVP-0 工程脚手架；第一动作执行 dependency spike 验证 Nixtla 栈与 pandas 兼容性。

## 2026-06-22 - v2 知识入口同步

- 类型：docs
- 摘要：按 `neat-freak` 审查项目知识入口，将 README、AGENTS、CLAUDE 从 v1/MVP 全量口径同步到 v2 当前实施基线和 MVP-0/MVP-1 分阶段口径。
- 涉及文件：
  - `README.md`
  - `AGENTS.md`
  - `CLAUDE.md`
  - `docs/PLAN.md`
  - `docs/LOG.md`
- 验证命令：

```bash
wc -l README.md AGENTS.md CLAUDE.md docs/*.md
rg -n "unified-ts-framework-plan-v1|unified-ts-framework-plan-v2|MVP-0|MVP-1|Jupyter|reporting|utils/log_util|src/tsforecasting/utils" README.md AGENTS.md CLAUDE.md docs/*.md
python3 - <<'PY'
from pathlib import Path
paths = ["README.md", "AGENTS.md", "CLAUDE.md", "docs/PLAN.md", "docs/LOG.md", "docs/unified-ts-framework-plan-v2.md"]
for path in paths:
    text = Path(path).read_text()
    fence = "`" * 3
    trailing = [i for i, line in enumerate(text.splitlines(), 1) if line.rstrip() != line]
    print(f"{path}: fence_even={text.count(fence) % 2 == 0}, trailing_ws={trailing[:5]}")
PY
git diff --check -- README.md AGENTS.md CLAUDE.md docs
```

- 结果：通过。README、AGENTS、CLAUDE 已指向 v2 当前实施基线；MVP-0/MVP-1、Phase 2、日志工具包边界、Markdown 围栏、尾随空白和 diff 检查通过。
- 下一步：从 `docs/PLAN.md` 的 P1 开始实施 MVP-0 工程脚手架与测试基础。

## 2026-06-22 - 方案与计划优化

- 类型：docs
- 摘要：根据方案评审结论新增 v2 当前实施基线，将过大的 Nixtla-only MVP 拆成 MVP-0/MVP-1，并同步重排 `docs/PLAN.md` 的执行计划。
- 涉及文件：
  - `docs/unified-ts-framework-plan-v2.md`
  - `docs/PLAN.md`
  - `docs/LOG.md`
- 验证命令：

```bash
test -f docs/unified-ts-framework-plan-v2.md
rg -n "MVP-0|MVP-1|Phase 2|unified-ts-framework-plan-v2" docs
python3 - <<'PY'
from pathlib import Path
paths = ["docs/unified-ts-framework-plan-v2.md", "docs/PLAN.md", "docs/LOG.md"]
for path in paths:
    text = Path(path).read_text()
    fence = "`" * 3
    print(f"{path}: fence_even={text.count(fence) % 2 == 0}")
PY
git diff --check -- docs
```

- 结果：通过。v2 方案文件已创建，`docs/PLAN.md` 已指向 v2；MVP-0/MVP-1/Phase 2 边界、Markdown 围栏和 diff 检查通过。
- 下一步：从 `docs/PLAN.md` 的 P1 开始实施 MVP-0 工程脚手架与测试基础。

## 2026-06-22 - 知识库整理

- 类型：docs
- 摘要：按 `neat-freak` 清理项目知识入口，修正 README、AGENTS、CLAUDE 中过期的 TimeGPT/legacy MVP 口径，并明确 v1 方案基线与 PLAN/LOG 职责。
- 涉及文件：
  - `README.md`
  - `AGENTS.md`
  - `CLAUDE.md`
  - `docs/PLAN.md`
  - `docs/LOG.md`
- 验证命令：

```bash
wc -l README.md AGENTS.md CLAUDE.md docs/*.md
python3 - <<'PY'
from pathlib import Path
paths = ["README.md", "AGENTS.md", "CLAUDE.md", "docs/PLAN.md", "docs/LOG.md", "docs/unified-ts-framework-plan-v1.md"]
for path in paths:
    text = Path(path).read_text()
    fence = "`" * 3
    print(f"{path}: fence_even={text.count(fence) % 2 == 0}")
PY
git diff --check -- README.md AGENTS.md CLAUDE.md docs/PLAN.md docs/LOG.md docs/unified-ts-framework-plan-v1.md
```

- 结果：通过。README、AGENTS、CLAUDE 已对齐 v1/PLAN/LOG 当前职责；旧 MVP 口径和旧方案路径无命中；Markdown 围栏和 diff 检查通过。
- 下一步：继续基于 `docs/PLAN.md` 的 P1 工程脚手架任务推进；如要扩展指标方案，先生成 v2 方案文档。

## 2026-06-22 - 方案文档固化为 v1

- 类型：docs
- 摘要：将统一时间序列预测框架方案文档重命名为 v1 基线，后续方案调整需要基于该版本生成新的方案文档。
- 涉及文件：
  - `docs/unified-ts-framework-plan-v1.md`
  - `docs/PLAN.md`
  - `docs/LOG.md`
- 验证命令：

```bash
test -f docs/unified-ts-framework-plan-v1.md
rg -n "unified-ts-framework-plan-v1\\.md" docs
git diff --check -- docs/unified-ts-framework-plan-v1.md docs/LOG.md docs/PLAN.md
```

- 结果：通过。v1 方案文件存在，旧方案文件不存在，旧路径引用已清理，diff 检查通过。
- 下一步：后续方案变更按 v2/v3 新文档生成，开发执行仍从 `docs/PLAN.md` 推进。

## 2026-06-22 - 文档职责拆分

- 类型：docs
- 摘要：新增开发日志与执行计划文档，将开发日志、计划项实现记录和架构方案变更记录拆分到不同文档中。
- 涉及文件：
  - `docs/LOG.md`
  - `docs/PLAN.md`
  - `docs/unified-ts-framework-plan-v1.md`
- 验证命令：

```bash
test -f docs/LOG.md
test -f docs/PLAN.md
rg -n "实施进度记录|每次实施后更新本文档的实施进度记录" docs/unified-ts-framework-plan-v1.md
rg -n "方案调整记录" docs/unified-ts-framework-plan-v1.md
rg -n "计划项实现记录|P0|P1|P11|updated_at|evidence" docs/PLAN.md
rg -n "开发日志|验证命令|下一步" docs/LOG.md
python3 - <<'PY'
from pathlib import Path
for path in [
    "docs/unified-ts-framework-plan-v1.md",
    "docs/LOG.md",
    "docs/PLAN.md",
]:
    text = Path(path).read_text()
    fence = "`" * 3
    print(f"{path}: fence_even={text.count(fence) % 2 == 0}")
PY
git diff --check -- docs/unified-ts-framework-plan-v1.md docs/LOG.md docs/PLAN.md
```

- 结果：通过。`docs/LOG.md`、`docs/PLAN.md` 已创建；方案文档不再维护任务执行进展；Markdown 围栏和 diff 检查通过。
- 下一步：按 `docs/PLAN.md` 从 Nixtla-only MVP 的工程脚手架开始构建。
