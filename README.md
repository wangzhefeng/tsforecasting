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

- [docs/unified-ts-framework-plan-v1.md](docs/unified-ts-framework-plan-v1.md)：v1 架构方案基线。后续方案修改应基于它生成新版本文档，不直接覆盖 v1。
- [docs/PLAN.md](docs/PLAN.md)：可执行开发计划和计划项实现记录。后续构建从这里开始。
- [docs/LOG.md](docs/LOG.md)：开发日志，只记录真实执行过程、验证结果和下一步。

## MVP 方向

MVP 聚焦 Nixtla-only 方案：

- 可运行主线：StatsForecast、MLForecast、NeuralForecast。
- 支撑能力：UtilsForecast 负责评估、losses、绘图和预处理。
- 层级验证：HierarchicalForecast 使用 Nixtla 官方 `TourismSmall` 示例独立验证 reconciliation。
- 后续阶段：TimeGPT、legacy adapter、本地 foundation model。

## 基本命令

```bash
uv sync
```

当前没有可运行的框架入口。实现前先阅读 `docs/PLAN.md` 和 `docs/unified-ts-framework-plan-v1.md`。
