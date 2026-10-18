# 内移式制动器与电驱总成热耦合研究

硕士研究项目：减速器左右输出端内移式制动盘、多热源热耦合、隔热导流结构优化。

**研究状态：规划中。所有基准数值为假设，而非实测或厂家数据。**

- [研究总计划](docs/RESEARCH_PLAN.md)
- [关键参数与未知项](docs/PARAMETER_REGISTER.md)
- [Codex 分期实施与验收](docs/CODEX_EXECUTION.md)
- [验证与风险控制](docs/VALIDATION_AND_RISKS.md)
- [基准车型配置](configs/baseline_vehicle.yaml)
- [Codex 指令](AGENTS.md)

参考：Park et al., *Energy Conversion and Management* 325 (2025) 119406, DOI: 10.1016/j.enconman.2024.119406。该文研究轮边 EMB 执行电机；本项目研究主驱动电机、减速器及内移摩擦制动器，不照搬其 EMB 电机参数和温限。

## 建议目录
`src/matlab/` 热源与热网络；`src/python/` 可选代理模型；`configs/` 所有参数；`geometry/` CAD；`simulations/` ANSYS 设置；`tests/` 校验；`results/` 原始结果；`reports/` 阶段报告。由 Codex 在阶段任务中按需创建。