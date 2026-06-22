# LOG.md

本文件用于记录 `tsforecasting` 框架开发日志。日志按时间倒序维护，只记录真实发生的开发、文档、验证和修复过程，不追溯伪造历史记录。

## 记录规则

- 每次实施完成后追加一条日志，优先记录用户可复查的事实。
- 方案范围、架构边界、MVP 目标等变化记录在当前方案版本文档的“方案调整记录”。
- 具体计划项状态记录在 `docs/PLAN.md` 的“计划项实现记录”。
- 日志条目应包含日期、类型、摘要、涉及文件、验证命令、结果和下一步。

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
