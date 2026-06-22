# tsforecasting

`tsforecasting` 是一个预实现阶段的统一时间序列预测框架项目。当前仓库尚未创建 `src/`、`configs/`、`examples/`、`tests/` 或 CLI 入口，现阶段的权威内容是设计文档和执行计划。

## 当前状态

- Python 项目名：`tsforecasting`
- Python 版本：`>=3.12`
- 包管理：`uv`
- 当前依赖：`pandas`、`numpy`、`scikit-learn`、`scipy`、`statsmodels`、`matplotlib`
- 尚未加入 Nixtla MVP 依赖：`statsforecast`、`mlforecast`、`neuralforecast`、`hierarchicalforecast`、`utilsforecast`、`datasetsforecast`
- 尚未配置测试运行器或 linter

## 文档入口

- [docs/unified-ts-framework-plan-v2.md](docs/unified-ts-framework-plan-v2.md)：当前实施基线，已将第一阶段拆成 MVP-0/MVP-1。
- [docs/unified-ts-framework-plan-v1.md](docs/unified-ts-framework-plan-v1.md)：v1 历史基线，**已被 v2 取代**，仅作设计演进记录保留。不要按其模块图/catalog 实施，也不直接覆盖。
- [docs/PLAN.md](docs/PLAN.md)：可执行开发计划和计划项实现记录。后续构建从这里开始。
- [docs/LOG.md](docs/LOG.md)：开发日志，只记录真实执行过程、验证结果和下一步。

## MVP 方向

MVP 聚焦 Nixtla-only 方案：

- MVP-0：先跑通 StatsForecast `SeasonalNaive` / `AutoETS` 纵切面，固定 YAML、Nixtla long table、UtilsForecast 指标、artifacts 和 manifest。
- MVP-1：再接入 MLForecast、NeuralForecast CPU smoke，以及 TourismSmall hierarchical reconciliation。
- Phase 2：full Nixtla model catalog、Jupyter notebook reporting、更多模型与诊断报告。
- 后续阶段：TimeGPT、legacy adapter、本地 foundation model。

## 基本命令

```bash
uv sync
```

当前没有可运行的框架入口。实现前先阅读 `docs/PLAN.md` 和 `docs/unified-ts-framework-plan-v2.md`。
