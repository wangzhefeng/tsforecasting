# LOG.md

本文件用于记录 `tsforecasting` 框架开发日志。日志按时间倒序维护，只记录真实发生的开发、文档、验证和修复过程，不追溯伪造历史记录。

## 记录规则

- 每次实施完成后追加一条日志，优先记录用户可复查的事实。
- 方案范围、架构边界、MVP 目标等变化记录在当前方案版本文档的“方案调整记录”。
- 具体计划项状态记录在 `docs/PLAN.md` 的“计划项实现记录”。
- 日志条目应包含日期、类型、摘要、涉及文件、验证命令、结果和下一步。

## 2026-06-29 - 补 adapter/registry TODO 注释并清理格式

- 类型:docs(注释整理,P25 延续)
- 摘要:接手工作区 WIP,把 stats/ml/neural adapter(`predict`/`cross_validation` 各步)和 registry(`get_entry`/`build_model`)的 `# TODO 补充注释` 占位替换为 P25 风格中文注释,说明每块职责而非逐行翻译;顺带把 registry 多行空包裹 docstring(`RegistryError`/`build_models`)规范为单行,清理 stats/neural 的行尾空格,evaluation `__all__` 恢复单行。无行为变更。
- 涉及文件:
  - `src/tsforecasting/models/nixtla/ml.py`
  - `src/tsforecasting/models/nixtla/stats.py`
  - `src/tsforecasting/models/nixtla/neural.py`
  - `src/tsforecasting/models/registry.py`
  - `src/tsforecasting/evaluation/__init__.py`(恢复 committed 单行 `__all__`)
- 验证命令:

```bash
grep -rn "TODO 补充注释" src/ tests/ --include="*.py"   # 0 残留
grep -rnE ' +$' src/tsforecasting/models/ src/tsforecasting/evaluation/  # 无行尾空格
.venv/bin/ruff check .
.venv/bin/python -m pytest -q
```

- 结果:通过。0 TODO 残留、无行尾空格、ruff clean、pytest 93 passed / 20 warnings。
- 下一步:—

## 2026-06-28 - 修复 nixtla 包可选 backend import 泄漏

- 类型:fix(import 契约)
- 摘要:`models/nixtla/__init__.py` 顶部 import ml/neural adapter 会强制加载 mlforecast/neuralforecast,破坏 lazy-import-optional-backend 契约——base install(未装 ml/neural extra)无法 `import tsforecasting.main`(模拟 base 实测 ImportError)。改为 PEP 562 `__getattr__` 延迟暴露:stats 仍顶部 eager(base 依赖),ml/neural 仅在显式属性访问时加载。新增 `tests/unit/test_import_safety.py` 用子进程屏蔽可选 extra,锁住「base 可 import 主包」契约。保留用户暴露 ml/neural 接口的意图(包装级 import 仍可用)。
- 涉及文件:
  - `src/tsforecasting/models/nixtla/__init__.py`
  - `tests/unit/test_import_safety.py`
  - `docs/PLAN.md`
  - `docs/LOG.md`
- 验证命令:

```bash
.venv/bin/python -c "import sys;sys.modules['mlforecast']=None;sys.modules['neuralforecast']=None;import tsforecasting.main"
.venv/bin/ruff check .
.venv/bin/python -m pytest -q
```

- 结果:通过。模拟 base import OK;ruff clean;pytest 93 passed / 20 warnings。
- 下一步:—

## 2026-06-28 - 删除死代码 orchestration/ 包

- 类型:chore(死代码清理)
- 摘要:neat-freak 分析发现 `src/tsforecasting/orchestration/` 是 P29 重构遗漏清理的死代码包。`forecast_workflow.py`(`run_pipeline` + `_build_adapter`)的编排职责已被 `main.py` 的 `ForecastRunner` 完整复刻并增强(新增 `stage_order`/`skipped_stages` + `ForecastArtifactWriter`);`__init__.py` 仅是 `from main import run_pipeline` 的迁移垫片。两者活跃区 0 引用(grep 确认)、测试已直接用 `tsforecasting.main`。删除整个包,`main.py` 成为唯一编排入口,与 v3「类边界」(不再含 orchestration)对齐,并消除 v1 `Config` 与 v2 `ForecastArgs` 两套并行契约的误用隐患。
- 涉及文件:
  - `src/tsforecasting/orchestration/`(删除)
  - `docs/PLAN.md`
  - `docs/LOG.md`
- 验证命令:

```bash
.venv/bin/ruff check .
.venv/bin/python -m pytest -q
```

- 结果:通过。ruff clean;pytest 92 passed / 20 warnings(与删除前一致,无回归);`import tsforecasting.main` 冒烟通过。
- 下一步:—

## 2026-06-28 - neat-freak 收尾:验证、清理与 P29 提交

- 类型:docs(知识整理)+ chore
- 摘要:对 forecast-only v3 做 neat-freak 全量审查,确认 README/AGENTS/CLAUDE/PLAN/v3/model_catalog/pyproject/configs/scripts/tests/orchestration/记忆 均已对齐 forecast-only v3,无过期或矛盾,规则文档相对时间清零。改动:CLAUDE/AGENTS 去掉 `currently` 时态词(三-backend 为 v3 固化架构,非临时);修复 nixtla `__init__` import 排序(I001,改字母序 ml/neural/stats);清理活跃区与 tests 指向已迁走 hierarchical/reconciliation 模块的 8 个孤儿 `.pyc`。全量验证 ruff clean + pytest 92 passed,将 P29 重构(59 files)提交至分支 `chore/forecast-only-restructure`。精简 `[report]` extra 冗余 `nbformat` 因 pypi 网络不可达(`uv lock` 失败)暂缓并回退 pyproject。
- 涉及文件:
  - `CLAUDE.md`
  - `AGENTS.md`
  - `src/tsforecasting/models/nixtla/__init__.py`
  - `docs/PLAN.md`
  - `docs/LOG.md`
- 验证命令:

```bash
.venv/bin/ruff check .
.venv/bin/python -m pytest -q
```

- 结果:通过。ruff All checks passed;pytest 92 passed / 20 warnings(均为 pytorch_lightning 上游弃用提示)。
- 下一步:将 `chore/forecast-only-restructure` fast-forward merge 回 main;网络恢复后再做 `[report]` extra 精简(`uv lock`)。

## 2026-06-28 - forecast-only 类式运行结构重构

- 类型：chore（架构重构 / 入口重构）
- 摘要：按用户方案将主线收敛到 StatsForecast、MLForecast、NeuralForecast 三类 forecast backend。新增 `ForecastRunner` 和 `MainCLI` 类式入口；YAML 改为 backend 分组 v2 schema 并输出 `ForecastArgs`；artifact 改为 run-local `config/ data/ predictions/ metrics/ reports/` 分区；新增 `ForecastArtifactWriter` 与 `ReportGenerator` 类；脚本改用 `uv run python -m tsforecasting.main_cli`；TourismSmall 层级协调全链路迁入 `src/tsforecasting/todo/hierarchical/`，从活跃入口、extras、配置、脚本、测试和 reporting 移除。
- 涉及文件：
  - `src/tsforecasting/main.py`
  - `src/tsforecasting/main_cli.py`
  - `src/tsforecasting/config/forecast.py`
  - `src/tsforecasting/artifacts/`
  - `src/tsforecasting/reporting/`
  - `configs/examples/ett_small/*.yaml`
  - `scripts/`
  - `src/tsforecasting/todo/hierarchical/`
  - `README.md`
  - `AGENTS.md`
  - `docs/PLAN.md`
  - `docs/unified-ts-framework-plan-v3.md`
- 验证命令：

```bash
uv run pytest -q tests/unit/test_config.py tests/unit/test_scripts.py tests/unit/test_reporting.py tests/integration/test_run_smoke.py::test_forecast_runner_records_stage_order
```

- 结果：通过，39 passed / 1 skipped。全量验证记录见本轮最终执行结果。
- 下一步：若后续恢复层级协调，先从 `todo/hierarchical/` 重新设计为独立 feature，不直接接回当前 forecast 主线。

## 2026-06-28 - neat-freak 知识入口同步

- 类型：docs（知识整理）+ memory
- 摘要：按 `neat-freak` 做会话收尾。尺寸体检确认 README/AGENTS/CLAUDE/docs 未膨胀；同步 README、AGENTS、CLAUDE 中的当前依赖与运行入口：base 依赖包含 `nbformat`，`report` extra 聚焦 HTML 导出，示例运行脚本按 `scripts/<dataset>/` 分类并由 `scripts/script_config_map.yaml` 维护；README 文档入口状态从 P25 更新到 P28，并补充 `ett_small/intervals.yaml` 示例配置。
- 涉及文件：
  - `README.md`
  - `AGENTS.md`
  - `CLAUDE.md`
  - `docs/PLAN.md`
  - `docs/LOG.md`
  - 记忆 note：`/Users/wangzf/.codex/memories/extensions/ad_hoc/notes/2026-06-28T21-20-34-tsforecasting-scripts-cli-sync.md`
- 验证命令：

```bash
wc -l AGENTS.md CLAUDE.md README.md docs/*.md
rg -n "今天|昨天|刚刚|最近|上周|today|yesterday|recently" AGENTS.md CLAUDE.md README.md docs/PLAN.md docs/unified-ts-framework-plan-v2.md
uv run pytest -q tests/unit/test_scripts.py tests/unit/test_config.py
uv run ruff check .
```

- 结果：通过。关键文档尺寸未超限；相对时间 grep 0 命中；脚本/config 单元测试通过；`ruff` All checks passed。
- 下一步：后续新增示例配置时同步 `scripts/<dataset>/`、`scripts/script_config_map.yaml`、README 示例表和脚本契约测试。

## 2026-06-28 - 手动占位注释清理与 CLI 分发恢复

- 类型：fix（占位注释清理 / CLI 兼容性）
- 摘要：分析手动修改后发现占位注释实际位于 CLI 与 config 模块。清理 `cli/main.py`、`cli/parser.py`、`config/common.py`、`config/hierarchical.py` 中的占位注释；恢复 `parser.py` 只构建 parser、`main.py` 统一 parse+dispatch 的边界；移除手动调试打印，避免不同子命令读取不存在的 argparse 字段导致 `AttributeError`。用户新增的 `utils/log_util.py` 保留，仅按 ruff 要求调整 import 顺序。
- 涉及文件：
  - `src/tsforecasting/cli/main.py`
  - `src/tsforecasting/cli/parser.py`
  - `src/tsforecasting/config/common.py`
  - `src/tsforecasting/config/hierarchical.py`
  - `src/tsforecasting/utils/log_util.py`
  - `docs/PLAN.md`、`docs/LOG.md`
- 验证命令：

```bash
rg -n "<占位标记正则>" . --glob '!./.venv/**' --glob '!./.git/**' --glob '!./results/**' --glob '!./logs/**'
uv run pytest -q tests/integration/test_run_smoke.py::test_cli_report_invalid_run_dir_fails_gracefully tests/integration/test_run_smoke.py::test_cli_dry_run_writes_nothing tests/unit/test_config.py tests/unit/test_scripts.py
uv run ruff check .
```

- 结果：通过。占位标记搜索 0 命中；相关 CLI/config/script 测试 32 passed；`ruff` All checks passed。
- 下一步：后续临时调试 CLI 参数时使用测试或局部日志，避免在 `main()` 中直接打印并读取非所有子命令共有的字段。

## 2026-06-28 - 示例配置运行脚本

- 类型：chore（运行脚本）
- 摘要：按 `configs/` 下 6 个示例配置新增一一对应的 `scripts/` 运行脚本，并按配置目录结构分类。`scripts/script_config_map.yaml` 保存配置到脚本的映射状态；`ett_small` forecast 脚本归入 `scripts/ett_small/`，`tourism_small` 层级协调脚本归入 `scripts/tourism_small/`；脚本统一从自身位置定位并进入仓库根目录，再调用 `uv run tsforecasting`，透传额外 CLI 参数，不直接依赖 `.venv/bin/tsforecasting`，不设置 `UV_CACHE_DIR`，也不引用 `.uv_cache`。
- 涉及文件：
  - `scripts/script_config_map.yaml`
  - `scripts/ett_small/run_stats.sh`
  - `scripts/ett_small/run_ml.sh`
  - `scripts/ett_small/run_neural.sh`
  - `scripts/ett_small/run_intervals.sh`
  - `scripts/ett_small/run_intervals_mixed.sh`
  - `scripts/tourism_small/run_hierarchical.sh`
  - `tests/unit/test_scripts.py`
  - `docs/PLAN.md`、`docs/LOG.md`
- 验证命令：

```bash
uv run pytest -q tests/unit/test_scripts.py
uv run python - <<'PY'
from pathlib import Path
import subprocess
import yaml
mapping = yaml.safe_load(Path("scripts/script_config_map.yaml").read_text())
for group in mapping["groups"].values():
    for entry in group["entries"]:
        subprocess.run([entry["script"], "--dry-run"], check=True)
PY
uv run ruff check .
```

- 结果：通过。脚本契约测试覆盖映射完整性、分类目录和 `uv run` 调用契约；6 个映射脚本 dry-run 均返回 0；`ruff` All checks passed。
- 下一步：后续新增配置时同步新增对应分类脚本和 `scripts/script_config_map.yaml` 映射项，并保持脚本通过 `uv run tsforecasting` 调用项目 CLI。

## 2026-06-28 - neat-freak 知识同步收尾

- 类型：docs（知识整理）+ memory
- 摘要：按 `neat-freak` 对模块职责重构、删除 `config/schema.py`、中文注释整理后的知识入口做收尾审查。尺寸体检确认 `AGENTS.md` / `CLAUDE.md` 未膨胀；README 文档入口从 P24 更新到 P25；根规则文件新增一条长期规则，要求源码 docstring/comment 优先用中文说明非显然职责、数据契约和约束，并避免为注释整理改变 CLI/artifact 文本。
- 涉及文件：
  - `README.md`、`AGENTS.md`、`CLAUDE.md`、`docs/LOG.md`
  - 记忆 note：`/Users/wangzf/.codex/memories/extensions/ad_hoc/notes/2026-06-28-tsforecasting-refactor-comments-sync.md`
- 验证命令：

```bash
wc -l AGENTS.md CLAUDE.md README.md docs/*.md
rg -n "今天|昨天|刚刚|最近|上周|today|yesterday|recently" AGENTS.md CLAUDE.md README.md docs/PLAN.md docs/unified-ts-framework-plan-v2.md
UV_CACHE_DIR=.uv_cache uv run ruff check .
```

- 结果：通过。尺寸未超限；活跃文档相对时间 grep 0 命中；`ruff` All checks passed。
- 下一步：继续保持 `docs/PLAN.md` 记录实施状态、`docs/LOG.md` 记录事实日志，AGENTS/CLAUDE 只放长期规则。

## 2026-06-27 - 主要函数和关键代码中文注释整理

- 类型：chore（可读性整理，行为保持）
- 摘要：按用户要求，为项目主要函数和关键代码路径补充中文 docstring 与关键块注释，并把原有英文注释尽量改为中文。覆盖 CLI、config、workflow、data_provider、artifacts、evaluation、models、reconciliation、reporting、utils 等主线模块；保留 CLI help、notebook 标题、catalog 生成内容等用户可见输出文本，避免改变外部行为。
- 涉及文件：
  - `src/tsforecasting/{__init__,artifacts,cli,config,data_provider,evaluation,models,orchestration,reconciliation,reporting,utils}/`
  - `docs/PLAN.md`、`docs/LOG.md`
- 验证命令：

```bash
UV_CACHE_DIR=.uv_cache uv run ruff check src/tsforecasting
UV_CACHE_DIR=.uv_cache uv run pytest -q tests/unit/test_config.py tests/unit/test_hierarchical.py
UV_CACHE_DIR=.uv_cache uv run pytest -q tests/unit/test_reconciliation.py tests/unit/test_reporting.py tests/unit/test_stats_backend.py tests/unit/test_ml_backend.py tests/unit/test_neural_backend.py
```

- 结果：通过。`ruff` All checks passed；配置/层级单元测试 41 passed；核心拆分与后端 adapter 单元测试 16 passed / 1 skipped / 20 warnings（warnings 来自 NeuralForecast/PyTorch Lightning 小样本训练设置）。
- 下一步：后续新增模块时继续保持注释解释职责、输入输出契约和非显然约束，避免逐行翻译显而易见代码。

## 2026-06-27 - 模块职责重构

- 类型：chore（结构重组）
- 摘要：按用户 review 对 config、workflow、reconciliation、reporting 与通用工具函数做职责拆分。`config/common.py` 承载公共解析、运行 override 与 run_id；`config/forecast.py` 承载普通 forecast 配置；删除重构后与 `config/__init__.py` 重复的 `schema.py` 兼容残留；`config/hierarchical.py` 不再引用 forecast schema 私有函数。`orchestration/run.py` / `reconcile.py` 改为 `forecast_workflow.py` / `reconciliation_workflow.py`，并保留 `run_pipeline` / `run_reconciliation` 公开导出。根层 `reconciliation.py` 与 `reporting.py` 拆为 package；新增 `utils/imports.py`、`utils/frames.py`、`utils/runtime.py`、`utils/serialization.py`，承接动态 import、wide-to-long 归一、运行环境初始化和 JSON/YAML 写入。
- 涉及文件：
  - `src/tsforecasting/config/{common,forecast,hierarchical,__init__}.py`
  - `src/tsforecasting/orchestration/{forecast_workflow,reconciliation_workflow,__init__}.py`
  - `src/tsforecasting/reconciliation/{__init__,core,diagnostics,resolvers}.py`
  - `src/tsforecasting/reporting/{__init__,detect,notebook,templates,export,generate}.py`
  - `src/tsforecasting/utils/{imports,frames,runtime,serialization}.py`
  - `src/tsforecasting/models/{registry,nixtla/stats,nixtla/ml,nixtla/neural}.py`
  - `src/tsforecasting/artifacts/writer.py`
  - `AGENTS.md`、`CLAUDE.md`、`README.md`、`docs/unified-ts-framework-plan-v2.md`、`docs/PLAN.md`、`docs/LOG.md`
- 验证命令：

```bash
UV_CACHE_DIR=.uv_cache uv run ruff check .
UV_CACHE_DIR=.uv_cache uv run pytest -q tests/unit/test_config.py tests/unit/test_hierarchical.py
UV_CACHE_DIR=.uv_cache uv run pytest -q tests/unit/test_reconciliation.py tests/unit/test_reporting.py
UV_CACHE_DIR=.uv_cache uv run pytest -q tests/unit/test_stats_backend.py tests/unit/test_ml_backend.py tests/unit/test_neural_backend.py
UV_CACHE_DIR=.uv_cache uv run pytest -q tests/integration/test_run_smoke.py tests/integration/test_reconcile_smoke.py
UV_CACHE_DIR=.uv_cache uv run tsforecasting validate-config --config configs/examples/ett_small/stats.yaml
UV_CACHE_DIR=.uv_cache uv run tsforecasting run --config configs/examples/ett_small/stats.yaml --dry-run
UV_CACHE_DIR=.uv_cache uv run tsforecasting reconcile --config configs/examples/tourism_small/hierarchical.yaml --dry-run
UV_CACHE_DIR=.uv_cache uv run tsforecasting report --run-dir /tmp/nonexistent
UV_CACHE_DIR=.uv_cache uv run pytest -q
```

- 结果：通过。`ruff` All checks passed；目标测试通过；integration smoke `8 passed`；全量 `pytest` 为 98 passed / 1 skipped / 20 warnings（warnings 来自 NeuralForecast/PyTorch Lightning 小样本训练设置）；三个正向 CLI smoke 均返回 0；`report --run-dir /tmp/nonexistent` 在 base 环境友好返回 1 且无 traceback。
- 下一步：后续新增跨子系统 helper 时优先放入 `utils/`；新增 workflow 时采用 `*_workflow.py` 命名并通过包 `__init__.py` 保留稳定公开导出。

## 2026-06-27 - CLI 模块职责拆分

- 类型：chore（结构重组）+ fix
- 摘要：按用户 review 将 `src/tsforecasting/cli/__init__.py` 从单文件 CLI 实现拆成职责清晰的子模块。`__init__.py` 只保留 `main` 公开导出；`main.py` 负责 dispatch；`parser.py` 负责 argparse；`forecast.py`、`validate.py`、`hierarchical.py`、`report.py` 分别承载对应子命令实现。外部入口 `tsforecasting.cli:main`、命令名、参数、输出文本和返回码保持不变。验证时发现并修复 `Config` dataclass 字段顺序问题：必填 `runtime`/`artifacts` 不能位于默认字段 `predict` 之后，否则测试收集阶段会失败。
- 涉及文件：
  - `src/tsforecasting/cli/__init__.py`
  - `src/tsforecasting/cli/{main,parser,forecast,validate,hierarchical,report}.py`
  - `src/tsforecasting/config/schema.py`
  - `AGENTS.md`、`CLAUDE.md`
  - `docs/unified-ts-framework-plan-v2.md`、`docs/PLAN.md`、`docs/LOG.md`
- 验证命令：

```bash
UV_CACHE_DIR=.uv_cache uv run ruff check src/tsforecasting/cli tests/unit/test_config.py tests/unit/test_hierarchical.py tests/integration/test_run_smoke.py tests/integration/test_reconcile_smoke.py
UV_CACHE_DIR=.uv_cache uv run pytest -q tests/unit/test_config.py tests/unit/test_hierarchical.py tests/integration/test_run_smoke.py tests/integration/test_reconcile_smoke.py
UV_CACHE_DIR=.uv_cache uv run tsforecasting validate-config --config configs/examples/ett_small/stats.yaml
UV_CACHE_DIR=.uv_cache uv run tsforecasting run --config configs/examples/ett_small/stats.yaml --dry-run
UV_CACHE_DIR=.uv_cache uv run tsforecasting reconcile --config configs/examples/tourism_small/hierarchical.yaml --dry-run
```

- 结果：通过。`ruff` All checks passed；CLI 相关测试 `49 passed in 53.43s`；三个 CLI smoke check 均返回 0。
- 下一步：后续新增 CLI 子命令时继续沿用模块拆分边界，避免把命令实现放回 `cli/__init__.py`。

## 2026-06-27 - neat-freak 知识同步收尾

- 类型：docs（知识整理）+ memory
- 摘要：按 `neat-freak` 对本阶段修复后的知识入口做收尾审查。尺寸体检确认 `AGENTS.md` / `CLAUDE.md` 未膨胀；根规则文件新增一条长期规则，要求 config validation 保持 metadata-only、dependency-light，并在 CLI override 后复校验；`docs/unified-ts-framework-plan-v2.md` 修正仍残留的早期预实现口径、旧 `<短hash>` run_id 描述、过时 MVP-0 CLI 限定、旧依赖分组与 logging vendor 表述，新增 2026-06-27 方案调整记录；写入 Codex ad-hoc memory note，要求后续记忆把 `tsforecasting` 从 pre-implementation 状态更新为已实现可运行框架。
- 涉及文件：
  - `AGENTS.md`、`CLAUDE.md`
  - `docs/unified-ts-framework-plan-v2.md`、`docs/LOG.md`
  - 记忆 note：`/Users/wangzf/.codex/memories/extensions/ad_hoc/notes/2026-06-27-tsforecasting-implemented-config-reliability.md`
- 验证命令：

```bash
wc -l AGENTS.md CLAUDE.md README.md docs/PLAN.md docs/LOG.md docs/model_catalog.md docs/unified-ts-framework-plan-v1.md docs/unified-ts-framework-plan-v2.md
rg -n "预实现|尚未|短hash|不暴露|MVP-0 CLI 只|utils/log_util.py|avg_proportions|dependency_group.*torch" docs/unified-ts-framework-plan-v2.md README.md AGENTS.md CLAUDE.md docs/PLAN.md
rg -n "今天|昨天|刚刚|最近|上周|today|yesterday|recently" AGENTS.md CLAUDE.md README.md docs/PLAN.md docs/unified-ts-framework-plan-v2.md
UV_CACHE_DIR=.uv_cache uv run ruff check .
UV_CACHE_DIR=.uv_cache uv run pytest -q tests/unit/test_config.py tests/unit/test_hierarchical.py
```

- 结果：通过。尺寸未超限；相对时间 grep 0 命中；stale grep 仅剩历史记录语境；`ruff` clean；目标单元测试通过。主记忆索引未直接编辑，只新增 ad-hoc note 等待记忆系统归并。
- 下一步：若后续继续推进 P16/P18/P19，仍按“代码事实 → README/docs → AGENTS/CLAUDE → memory note”顺序收尾。

## 2026-06-27 - 配置可靠性、run_id 唯一性与文档契约一致性修复

- 类型：fix（配置校验 + CLI 错误处理 + 文档一致性）
- 摘要：修复项目复查发现的 5 类问题。`validate-config` 现在会用 `REGISTRY` 元数据校验 `models[].name` 与 backend 匹配，未知模型和 backend mismatch 在配置校验阶段提前失败，且不 import 可选 backend、不实例化模型；`run`/`backtest` 与 `reconcile` 的 CLI override 后都会重新执行配置校验，非法 `--log-level` 在 dry-run 阶段返回 `config invalid` 而不是进入运行期 traceback；默认 `run_id` 保持 `tsforecasting-YYYYmmddHHMMSS-xxxxxxxx` 形态，但后缀改为随机 8 位，避免同秒碰撞；manifest 的 `run_id_rule` 同步为 `<random8>`；README/v2 明确当前 `metrics.csv` 始终输出四个 core metrics，`evaluation.metrics` 不是输出筛选器；v2 MVP-0 验收移除当前 `metrics.json` 必产要求（仍保留 P16）。
- 涉及文件：
  - `src/tsforecasting/config/schema.py`、`src/tsforecasting/config/hierarchical.py`、`src/tsforecasting/cli/__init__.py`、`src/tsforecasting/models/registry.py`、`src/tsforecasting/artifacts/writer.py`
  - `tests/unit/test_config.py`、`tests/unit/test_hierarchical.py`
  - `README.md`、`docs/unified-ts-framework-plan-v2.md`、`docs/PLAN.md`、`docs/LOG.md`
- 验证命令：

```bash
UV_CACHE_DIR=.uv_cache uv run pytest -q tests/unit/test_config.py
UV_CACHE_DIR=.uv_cache uv run pytest -q tests/unit/test_hierarchical.py
UV_CACHE_DIR=.uv_cache uv run pytest -q tests/integration/test_run_smoke.py tests/integration/test_reconcile_smoke.py
UV_CACHE_DIR=.uv_cache uv run ruff check .
UV_CACHE_DIR=.uv_cache uv run pytest -q
UV_CACHE_DIR=.uv_cache uv run tsforecasting validate-config --config configs/examples/ett_small/stats.yaml
UV_CACHE_DIR=.uv_cache uv run tsforecasting reconcile --config configs/examples/tourism_small/hierarchical.yaml --dry-run
```

- 结果：通过。目标测试分别为 `27 passed`、`14 passed`、`8 passed`；`ruff` All checks passed；全量 `pytest` 为 98 passed / 1 skipped / 20 warnings（warnings 来自 NeuralForecast/PyTorch Lightning 小样本训练设置）；正向 CLI 校验通过。负向手工检查：未知模型返回 `config invalid: model 'does_not_exist' not in registry`；forecast 与 hierarchical 的非法 `--log-level NOTALEVEL` 均返回 `config invalid` 且无 traceback；同秒连续生成 10 个 `run_id` 无重复。
- 下一步：P16 `metrics.json` 是否实现仍按 backlog 决策；P18 MLForecast CV 区间仍受上游限制。

## 2026-06-25 - 示例配置按数据集分类（ett_small/ + tourism_small/）

- 类型：chore（配置目录重组）+ docs
- 摘要：把 `configs/examples/` 下 6 个扁平 YAML 按数据集分两组子目录：`ett_small/`（5 个，基于 ETTh1 小时数据）放 stats/ml/neural/intervals/intervals_mixed；`tourism_small/`（1 个，TourismSmall 季度层级）放 hierarchical。按用户选择**去掉与目录重复的数据集前缀**（目录已表数据集，且内部 `log_name`/`output_dir`/`run_id` 不受文件位置影响，身份信息保留）。`git mv` 6 个已跟踪文件；同步 4 处测试引用、README 快速开始+配置表、CLAUDE/AGENTS L7 散文、v2 目录树。**注**：PLAN.md P1–P15 历史记录与 v1 文档保持原扁平路径（历史快照，不重写）。
- 涉及文件：
  - `git mv`：`configs/examples/ett_small_{stats,ml,neural,intervals,intervals_mixed}.yaml` → `configs/examples/ett_small/{stats,ml,neural,intervals,intervals_mixed}.yaml`；`configs/examples/tourism_small_hierarchical.yaml` → `configs/examples/tourism_small/hierarchical.yaml`
  - `tests/integration/{test_run_smoke,test_reconcile_smoke}.py`、`tests/unit/test_config.py`、`README.md`、`CLAUDE.md`、`AGENTS.md`、`docs/unified-ts-framework-plan-v2.md`、`docs/PLAN.md`、`docs/LOG.md`
- 验证命令：

```bash
uv run ruff check .
uv run pytest tests/unit tests/integration -q
uv run tsforecasting validate-config --config configs/examples/ett_small/stats.yaml
git grep -nE "configs/examples/(ett_small_stats|ett_small_ml|ett_small_neural|ett_small_intervals|ett_small_intervals_mixed|tourism_small_hierarchical)\.yaml" -- src tests README.md CLAUDE.md AGENTS.md docs/unified-ts-framework-plan-v2.md  # 0
```

- 结果：通过。`ruff` All checks passed；`pytest` 90 passed/1 skipped；`validate-config` 新路径通过；grep 旧扁平路径在活跃文件中 0 命中。
- 下一步：本次为纯配置重组、无功能影响。

## 2026-06-25 - 目录结构统一治理（results / dataset / data_provider + 缓存与 lightning 日志归并）

- 类型：chore（重命名 + 归并，零业务逻辑变更）+ docs
- 摘要：按用户 5 项需求统一治理仓库目录。① `runs/`→`results/`（运行输出，纯配置驱动，源码无字面量）；② `examples/`→`dataset/`（示例数据；注意 `configs/examples/` 是另一个"examples"配置目录，未动）；③ `datasetsforecast_cache/`→`dataset/datasetsforecast_cache/`（层级数据下载缓存归入 dataset/ 统一管理，改 `config/hierarchical.py` 默认值 + `tourism_small_hierarchical.yaml`）；④ `src/tsforecasting/data/`→`data_provider/`（数据加载模块，5 处 import 同步）；⑤ `lightning_logs/`→`logs/lightning/`（NeuralForecast 的 PyTorch Lightning 遥测归入 logs/ 统一管理）。⑤ 是唯一行为性改动：`neural.py` 新增 `_make_lightning_logger()` 返回 `TensorBoardLogger(save_dir="logs", name="lightning")`，合并进每个模型实例的 `trainer_kwargs`——**此版本 NeuralForecast 的 `__init__` 不接受顶层 `trainer_kwargs`**，logger 必须挂模型实例上（每个模型的 `trainer_kwargs` 才被转发给 Lightning Trainer）。同步 6 个示例 YAML、测试、`.gitignore`、README、v2 目录树/路径。**注**：PLAN.md P1–P15 历史记录条目与 v1 文档保持原路径（历史快照，不重写历史）。
- 涉及文件：
  - 目录：`runs`→`results`、`examples`→`dataset`、`datasetsforecast_cache`→`dataset/datasetsforecast_cache`、`lightning_logs`→`logs/lightning`、`src/tsforecasting/data`→`src/tsforecasting/data_provider`（后两者 `git mv` 保留历史，前三者普通 `mv`）
  - `src/tsforecasting/models/nixtla/neural.py`（logger 注入）、`src/tsforecasting/config/hierarchical.py`（cache_dir 默认值）、`data_provider/{__init__,hierarchical}.py` + `orchestration/{run,reconcile}.py`（import）
  - 6 个 `configs/examples/*.yaml`（path / output_dir / cache_dir）、`.gitignore`、`tests/unit/*`、`tests/integration/*`、`README.md`、`docs/unified-ts-framework-plan-v2.md`
- 验证命令：

```bash
uv run ruff check .
uv run pytest tests/unit tests/integration -q
git grep -nE "tsforecasting\.data\b" -- src tests               # 0
git grep -n "output_dir: runs/" -- configs                       # 0
git grep -n "examples/ett_small/ETTh1.csv" -- src tests configs  # 0
uv run tsforecasting run --config configs/examples/ett_small_stats.yaml   # results/
```

- 结果：通过。`ruff` All checks passed；`pytest tests/unit` 82 passed/1 skipped、`pytest tests/integration` 8 passed；grep 守卫全 0 命中；真实 `run ett_small_stats` 产物落 `results/ett_small_stats/`（7 artifact 齐）；`reconcile` 缓存落 `dataset/datasetsforecast_cache/hierarchical/`（TourismSmall 已下载到新路径）；neural 遥测落 `logs/lightning/`（version 目录 96→101，根目录 `lightning_logs/` 不再生成）。修正一处 ruff I001（`data_provider/__init__.py` 的 import 因模块名变长超 88 列，自动改多行）。
- 下一步：本次为纯重构、无功能影响。可选：在文档里说明根目录 `dataset/`（数据）与 `configs/examples/`（示例配置）的双命名关系，或评估是否改 `configs/examples/`。

## 2026-06-25 - 移除遗留 utils/log_util.py + 立项 P16–P19 backlog

- 类型：chore + docs
- 摘要：删除已被 `src/tsforecasting/utils/logging.py` 取代的仓库顶层遗留模块 `utils/log_util.py`（代码零运行时引用，ruff 早以 `extend-exclude=["utils"]` 标 superseded），连带清理 `pyproject.toml` 孤儿 ruff 排除项与 `CLAUDE.md`/`AGENTS.md` Logging 段失效规则；并在 `docs/PLAN.md` 将 5 个 Phase 2 尾巴落成 P16–P19（`not_started`）：metrics.json（MVP-0b 收尾）、四项目架构诊断报告、区间 rank_metric + MLForecast CV（上游限制）、模型与图表扩展。
- 涉及文件：
  - `utils/log_util.py`（删除）
  - `pyproject.toml`、`CLAUDE.md`、`AGENTS.md`、`docs/PLAN.md`、`docs/LOG.md`
- 验证命令：

```bash
git status --short
uv run ruff check .
uv run pytest -q
```

- 结果：通过。`git status` 显示 5 文件改动（`utils/log_util.py` deleted；pyproject/CLAUDE/AGENTS/PLAN modified）；`ruff` All checks passed；`pytest` 90 passed/1 skipped（与 P15 基线一致）。
- 下一步：可从 P16（metrics.json，最小闭环）或 P18（区间 rank_metric）启动；utils 清理与 PLAN 立项建议拆两个 commit。

## 2026-06-24 - intervals 扩展到 neural/ml + comparison 完成（Phase 2 / P15）

- 类型：impl（phase-2 / P15）
- 摘要：把 P14 的 prediction intervals 从 statsforecast 扩到三个 backend，并把区间指标纳入 model_comparison。从 `stats.py` 提取共享 `melt_forecast_long`/`interval_columns`/`_is_pure_model_col` helper，ml/neural adapter 复用。
- **neural**：新 preset `nhits_quantile`（`neuralforecast.models.NHITS`，`model_type=neural_quantile`，注册 REGISTRY+catalog）。`build_model` 增 loss spec 解析：`models[].params.loss = {class, kwargs?}` → importlib 实例化（如 `MQLoss(quantiles=[0.1,0.5,0.9])`），保持 `run_config.yaml` YAML-safe。`NeuralForecastAdapter` 归一列名：`NHITS-lo-80.0`→`NHITS-lo-80`（去 `.0`）、`NHITS-median`→`NHITS`（point col，interval 列基于 model alias 而非 median col，spike 发现的坑），`yhat`=median。
- **ml**：`MLForecastAdapter.fit` 传 `PredictionIntervals(h=h)`（conformal），`predict(h, level=)` 产 `{model}-lo-{l}`/`hi-{l}`（列名同 stats，无 `.0`）。**MLForecast 限制**：conformal interval 仅 `predict` 产，`cross_validation(level=)` 不产（warning rerun fit，实测 cv 输出无 lo/hi）——故 ml 仅 predictions.csv 有区间，backtest 无（coverage/width 对 ml 为 NaN）。
- **comparison**：`build_model_comparison` 当 metrics 含 `coverage-`/`width-` 行时，pivot 后把这些列追加到 `model_comparison`（展示）；`rank_metric` 仍是点指标（mae 等），排名语义不变。
- 关键决策（用户）：neural **新 preset `nhits_quantile`**（不改现有 nhits 的 MAE 默认，quantile 版 point=median 与 MAE 点预测口径分离）；comparison **只加列展示**（不引入 coverage 排名，避免改 sort 方向）。
- 涉及文件：`src/tsforecasting/models/nixtla/{stats,ml,neural}.py`（提取 helper + levels）、`src/tsforecasting/models/registry.py`（`nhits_quantile` + loss spec）、`src/tsforecasting/orchestration/run.py`（levels 传三 backend）、`src/tsforecasting/evaluation/metrics.py`（comparison 区间列）、`src/tsforecasting/models/catalog.py`（+ `nhits_quantile`）、`configs/examples/ett_small_intervals_mixed.yaml`（新）、`tests/unit/test_{neural_backend,ml_backend,stats_backend,registry,catalog,evaluation}.py`、`docs/model_catalog.md`（重新生成）。
- 验证命令：

```bash
uv sync --extra neural --extra ml --extra hierarchical --extra plot
uv run tsforecasting run --config configs/examples/ett_small_intervals_mixed.yaml
uv run pytest -q          # 90 passed, 1 skipped（reporting/nbconvert 未装）
uv run ruff check .       # All checks passed
```

- 结果：通过。mixed run（stats+ml+neural quantile + levels=[80]）：predictions.csv 三 backend 都有 `lo-80`/`hi-80` 非空；metrics 含 `coverage-80`/`width-80`（ml 因 cv 无区间，其 coverage 为 NaN，符合 MLForecast 限制）；model_comparison 追加 `coverage-80`/`width-80` 列展示，排名仍按 mae。catalog 增 `nhits_quantile`（共 78 条）。
- 下一步：ml cv intervals（受 MLForecast 限制，可能需 StatsForecast-style 重算）；区间 `rank_metric`（按 coverage 排名，需改 sort 方向）；tsproj_* 架构诊断（推迟）。

## 2026-06-24 - HTML 报告导出 + 概率预测/区间指标 完成（Phase 2 / P13-P14）

- 类型：impl（phase-2 / P13 HTML、P14 intervals）
- P13 摘要：notebook HTML 导出。`reporting.to_html(notebook_path)` 用 `nbconvert` `ExecutePreprocessor` 执行 notebook（运行 code cell，含 matplotlib 画图）+ `HTMLExporter` 转自包含 HTML。`generate_report(..., html=True)` 触发；CLI `report --html` flag。`generate_report` 把 run_dir resolve 为绝对路径（ExecutePreprocessor cwd 是 notebook 目录，相对路径会 FileNotFoundError——spike 实测修复）。kernel 缺失（`NoSuchKernel`）转 friendly `ImportError`，提示 `python -m ipykernel install --sys-prefix --name python3`。`[report]` extra += `nbconvert`/`ipykernel`。
- P13 spike 结论：`ExecutePreprocessor(kernel_name="python3")` 执行需注册的 python3 kernel（`ipykernel` 提供）；nbconvert 不自动注册，需手动 `ipykernel install --sys-prefix`（venv scope，不污染 user）。HTML 含 `<img>`（matplotlib inline 输出），372KB。
- P14 摘要：概率预测/区间指标。config 增 `PredictionIntervalsConfig(levels)`（顶层可选，校验 `(0,100)` 整数）；`StatsForecastAdapter` 接 `levels`，`predict`/`cross_validation` 传原生 `level=`，wide 输出按模型 concat 把 `{model}-lo-{l}`/`{model}-hi-{l}` rename 成 `lo-{l}`/`hi-{l}` **追加**到 long（必需列契约不变，`validate_columns` 只查必需列）；无 levels 时走原 melt（零行为变化）。`compute_metrics` 当 backtest 含 `lo-`/`hi-` 列时，per (model, level) 算 `coverage-{l}`（y∈[lo,hi] 比例）+ `width-{l}`（平均 hi-lo）加到 `metrics.csv`；`model_comparison` 只 pivot 4 个 core metrics，区间行天然不进排名。先支持 statsforecast（`SeasonalNaive`/`AutoETS` 原生 interval，spike 确认 `level=[80,95]` 输出 `*-lo-*`/`*-hi-*` 列）。
- 关键决策（用户）：HTML **执行后导出**（含图表，非静态）；区间 artifact **追加列**（不破坏 MVP-0 契约）；区间 backend **先 stats**（原生 level 成熟，不引入 extra）。
- 涉及文件：P13：`src/tsforecasting/reporting.py`（`to_html`+`generate_report(html=)`+resolve）、`src/tsforecasting/cli/__init__.py`（`--html`）、`pyproject.toml`（`[report]`+=nbconvert/ipykernel）、`tests/unit/test_reporting.py`。P14：`src/tsforecasting/config/{schema,__init__}.py`（`PredictionIntervalsConfig`）、`src/tsforecasting/models/nixtla/stats.py`（levels）、`src/tsforecasting/orchestration/run.py`（传 levels）、`src/tsforecasting/evaluation/metrics.py`（coverage/width）、`configs/examples/ett_small_intervals.yaml`（新）、`tests/unit/test_evaluation.py`（新）、`tests/unit/test_{config,stats_backend}.py`。
- 验证命令：

```bash
uv sync --extra report --extra hierarchical --extra plot
uv run tsforecasting report --run-dir runs/ett_small_stats/tsforecasting-* --html  # .ipynb + .html(含 <img>)
uv run tsforecasting run --config configs/examples/ett_small_intervals.yaml
uv run pytest -q          # 85 passed, 3 skipped（ml/neural 未装）
uv run ruff check .       # All checks passed
```

- 结果：通过（TDD）。HTML：MVP-0 run 执行导出 372KB HTML 含 matplotlib 图表。概率：ETTh1 + levels=[80,95]，predictions/backtest 追加 4 列，metrics 含 coverage/width（coverage-80=1.0 该数据区间宽），comparison 仅 core metrics（未被区间污染）。必需列契约不变，不开 `prediction_intervals` 时行为零变化。
- 下一步：概率预测扩到 neural（quantile loss）/ml（conformal）；区间指标纳入 model_comparison 排名；tsproj_* 架构诊断（推迟）。

## 2026-06-23 - full Nixtla model catalog 完成（Phase 2 / P12）

- 类型：impl（phase-2 / catalog）
- 摘要：落地 full Nixtla model catalog（plan §6/§9「full catalog 与官方模型目录有来源记录和 status」）。新增 `src/tsforecasting/models/catalog.py`（纯数据，无 heavy import，base env 可加载）：`CatalogEntry`(name/backend/class_path/model_type/status/source_url/dependency_group) + `CATALOG` 共 **77 条**（statsforecast 35 + neuralforecast 34 + mlforecast-sklearn 8），`list_catalog(backend/status)` 过滤、`generate_catalog_md` 生成 markdown 表。**独立于 `REGISTRY`**（后者是 `build_model` 的 mvp preset，不动）——cataloged 模型仅"已记录"不等于"可 build"，避免污染 build path。
- 范围（用户确认全覆盖三 backend）：statsforecast 主要预测模型（naive/ets/exponential/theta/arima/ces/croston/mfles/mstl/tbats/garch 家族，排除 `ConformalIntervals`/`NaNModel`/`SklearnModel` 等 helper）；neuralforecast（NHITS/NBEATS/NBEATSx/RNN/LSTM/GRU/TCN/TFT/DeepAR/Transformer 家族等，排除 `HINT` wrapper 与 `SOFTSSharp`/`XLinear` variant）；mlforecast（6 个已 mvp 的 sklearn 估计器 + `kneighbors`/`svr`，LGBM/XGB 需额外 extra 故暂略）。
- 状态映射：现有 10 个 mvp preset（`seasonal_naive`/`auto_ets`/6 sklearn/`nhits`/`nbeats`）标 `mvp_smoke`，其余 `cataloged`（plan §6「不得把全量验证作为阻塞项」）。`source_url`：stats/neural 指各 backend 的 models 文档总览页，mlforecast 指对应 sklearn generated 页。`status` 生命周期：cataloged → mvp_smoke → validated/blocked/deprecated。
- 关键决策（用户两问）：(1) **独立 catalog + 文档**（不扩 REGISTRY 统一，catalog 是文档/追踪层，不该和 build path 耦合）；(2) **三 backend 全覆盖**官方目录。
- 涉及文件：`src/tsforecasting/models/catalog.py`（新）、`tests/unit/test_catalog.py`（新）、`docs/model_catalog.md`（新，由 `generate_catalog_md` 生成）、`docs/PLAN.md`（P12 row）。
- 验证命令：

```bash
uv run pytest -q tests/unit/test_catalog.py   # 6 passed
uv run python -c "from tsforecasting.models.catalog import CATALOG; import importlib; \
bad=[e.name for e in CATALOG if not hasattr(__import__('importlib').import_module(e.class_path.rpartition('.')[0]), e.class_path.rpartition('.')[2])]; print(len(CATALOG),'entries,',len(bad),'bad')"  # 77 entries, 0 bad
uv run ruff check .                            # All checks passed
```

- 结果：通过（TDD RED→GREEN）。77 条 class_path **全量 import 验证 0 错**（准确性保证）；`generate_catalog_md` 产出 `docs/model_catalog.md`（三 backend 分节表，含来源 + status）。catalog 纯 stdlib，base env 直接可用。
- 下一步：Phase 2 余项——四项目架构诊断报告（tsproj_*，用户已说推迟）、概率预测/区间指标（会动 artifact 契约）、HTML 导出（`nbconvert`）；以及把更多 `cataloged` 模型逐步推进到 `mvp_smoke`（按需注册进 `REGISTRY`）。

## 2026-06-23 - P11 阶段验收（MVP-0 / MVP-1 / Phase 2 首次全验收）

- 类型：acceptance（continuous / P11）
- 摘要：对已完成的 MVP-0（P1–P6）、MVP-1（P7–P9）、Phase 2 reporting（P10）做一次完整 smoke 验收，确认端到端可用、测试全绿。验收范围对照 plan §9 验收清单。
- 验收命令（全 extra env）：

```bash
uv sync --extra ml --extra neural --extra hierarchical --extra report --extra plot
# validate-config ×4
uv run tsforecasting validate-config --config configs/examples/ett_small_stats.yaml
uv run tsforecasting validate-config --config configs/examples/ett_small_ml.yaml
uv run tsforecasting validate-config --config configs/examples/ett_small_neural.yaml
uv run tsforecasting reconcile --config configs/examples/tourism_small_hierarchical.yaml --dry-run
# 端到端 smoke
uv run tsforecasting run --config configs/examples/ett_small_stats.yaml --run-id p11-stats --output-dir /tmp/p11
uv run tsforecasting run --config configs/examples/ett_small_ml.yaml --run-id p11-ml --output-dir /tmp/p11
uv run tsforecasting run --config configs/examples/ett_small_neural.yaml --run-id p11-neural --output-dir /tmp/p11
uv run tsforecasting reconcile --config configs/examples/tourism_small_hierarchical.yaml --run-id p11-hier --output-dir /tmp/p11
uv run pytest -q          # 79 passed, 0 skipped（全 extra，无 skip）
uv run ruff check .       # All checks passed
```

- 验收结果（对照 plan §9）：
  - **MVP-0**：`validate-config` ett_small_stats ✓；canonical 数据契约测试（无 `id_col`/重复时间戳/freq 缺失）✓（test_data_loader）；`run` ett_small_stats 产 7 artifact + `auto_ets` rank1 ✓；manifest 含完整 provenance ✓。
  - **MVP-1**：`run` ett_small_ml 跨 backend 排名（stats + ml）✓；`run` ett_small_neural CPU smoke `Trainer.fit stopped: max_steps=50`（训练步数受控）+ 跨 backend 排名 ✓；`reconcile` tourism_small_hierarchical 产 3 artifact + 4 reconciler `coherent=True` ✓。
  - **Phase 2**：`report` 生成 `model_comparison.ipynb` / `reconciliation.ipynb`（P10）✓。
  - **Phase 2 余项（未做，不阻塞）**：full Nixtla model catalog、四项目架构诊断报告、概率预测/区间指标、可选 HTML 导出（`nbconvert`）。
- 关键事实：全 extra env `pytest` **79 passed / 0 skipped**（neural/ml/hierarchical/report 测试全跑）；`ruff` clean。各 extra env 单独验证（见 P7/P8/P9 LOG）：base env 59p/6s、hierarchical env 65p/3s、neural env 50p/3s、ml env 51p。lazy-import 不变量始终成立（base `uv sync` 包可 import，optional backend 测试 skip）。
- 涉及文件：无代码改动，仅 `docs/PLAN.md`（P11 → done）、本日志。
- 下一步：P11 是持续项，后续每个阶段完成后再跑对应 smoke；Phase 2 余项按需推进。MVP-0 + MVP-1 + Phase 2 reporting 全部交付。

## 2026-06-23 - P10 notebook reporting 完成（Phase 2）

- 类型：impl（phase-2 / P10）
- 摘要：实现 notebook reporting，满足 plan §9「`reports/{run_id}/model_comparison.ipynb` 可由已存在 artifacts 生成」。新增 `reporting.py`：`detect_run_type` 按有无 `model_comparison.csv`/`reconciliation_diagnostics.csv` 区分 MVP-0 / hierarchical run；`build_mvp0_notebook` / `build_hierarchical_notebook` 用 `nbformat` **静态构造** notebook（不执行，code cell `outputs==[]`、`execution_count=None`）；`generate_report` 检测类型并写 `reports/{run_id}/model_comparison.ipynb`（MVP-0）或 `reconciliation.ipynb`（hierarchical）。MVP-0 notebook = markdown 元信息（run_id/config/freq/models/backtest）+ 5 个 code cell（排名表 / metrics 柱状图 / 最佳模型 backtest 曲线 / runtime 计时柱状图）；hierarchical notebook = 元信息（dataset/freq/levels/base/reconcilers）+ 5 个 code cell（层级表 / diagnostics 排名 / mse 柱状图 / reconciled vs base 曲线）。CLI 新增 `report --run-dir [--output-dir]` 子命令。
- 关键决策（用户三问三答）：(1) **静态构造**（`nbformat` 不执行，用户 Run All 渲染，CI 友好、不污染依赖隔离）；(2) **两类 run 都支持**（MVP-0 + hierarchical 分支，hierarchical notebook 形态独立）；(3) **新 `[report]` extra = `["nbformat"]`**（语义独立，绘图靠 `plot` extra 的 matplotlib，notebook 顶部注明运行依赖）。
- 实现细节：code cell 用 `__RUN_DIR__` 占位 + `str.replace` 注入绝对路径，避免 f-string/`.format` 的 `{}` 转义冲突；notebook 加 `kernelspec=python3` metadata；`generate_report` 捕获 `ValueError`（run_dir 不含识别 artifact）/`ImportError`（无 `[report]` extra）。
- 涉及文件：`pyproject.toml`（`[report]=["nbformat"]`）、`src/tsforecasting/reporting.py`（新）、`src/tsforecasting/cli/__init__.py`（`report` 子命令）、`tests/unit/test_reporting.py`（新）、`.gitignore`（`reports/`）、`docs/PLAN.md`。
- 验证命令：

```bash
uv sync --extra report --extra hierarchical --extra plot
uv run tsforecasting report --run-dir runs/ett_small_stats/tsforecasting-* --output-dir /tmp/reports
uv run pytest -q          # report+hierarchical+plot env：71 passed, 3 skipped
uv run ruff check .       # All checks passed
```

- 结果：通过（TDD：合成 run_dir RED→GREEN）。真实 report：MVP-0 stats run → `model_comparison.ipynb`（6 cells）、hierarchical run → `reconciliation.ipynb`（6 cells），均 `nbformat.read` 读回有效、code cell 全静态（outputs 空）。`reports/` 已 gitignore。base env（无 `[report]` extra）reporting 测试跳过，lazy import 不变量成立。
- 下一步：P11 阶段验收；Phase 2 余项（full catalog、更多模型、概率预测、四项目架构诊断报告、可选 HTML 导出 via nbconvert）。

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
