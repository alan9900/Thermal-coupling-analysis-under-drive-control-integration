# 分布式双电机驱制融合热耦合研究

**当前有效架构 V0.3：** 1800 kg 前驱概念纯电乘用车，**前轴左右各1台60 kW /130 N·m独立电机 + 9.0减速器 + 输出端内移摩擦制动器，无机械差速器**。只对**一侧电机—减速器—制动器**做详细热网络与三维热耦合仿真；整车动力学仍包含左右两台电机及后轴常规制动。

**所有基准参数是未经实车验证的工程假设**，不代表厂家车型及验证结果。

## 当前必须阅读
1. [V0.3双电机架构、验算与M0要求](docs/DUAL_MOTOR_V03_ARCHITECTURE.md)（**权威最新架构**）
2. [V0.3基准配置](configs/baseline_vehicle.yaml)
3. [Codex执行规则](AGENTS.md)
4. [研究工作路线](docs/RESEARCH_PLAN.md)、[参数缺口](docs/PARAMETER_REGISTER.md)、[阶段验收](docs/CODEX_EXECUTION.md)、[验证风险](docs/VALIDATION_AND_RISKS.md)

**历史资料：** `configs/archive/baseline_vehicle_v01_central_motor.yaml`、`docs/BASELINE_V02_AUDIT.md`、`configs/screening_scenarios_v02.yaml` 均描述或依据旧单电机+差速器概念，不作为当前单侧电驱输入；保留作设计变更追溯。

## 推荐顺序
M0 参数登记与运动学/能量校验 → M1 MATLAB整车制动和单侧热源 → M2单侧瞬态热网络 → M3隔热罩参数化 → M4 ANSYS瞬态热分析 → M5 Fluent局部换热 → M6代理模型优化 → M7多工况验证。缺商业软件环境时只创建未运行脚本/模板，不能声称得到求解结果。

参考研究：Park et al., *Energy Conversion and Management* 325 (2025) 119406，DOI:10.1016/j.enconman.2024.119406。原论文研究轮边EMB执行电机，不能将其电机温限与参数直接用到本项目主牵引电机。

目录将由Codex按需创建：`src/matlab/`、`src/python/`、`geometry/`、`simulations/`、`tests/`、`results/`、`reports/`。