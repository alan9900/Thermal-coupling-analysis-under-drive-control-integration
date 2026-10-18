# 后驱分布式双电机驱制融合热耦合研究（V0.4）

**当前权威研究架构**：1800kg概念纯电动车，后轴左右各一套独立电驱单元（单侧60kW参考电机+两级约9:1减速器+减速器输出端内移式盘式摩擦制动器），**无机械差速器**；只对单侧电机—减速器—制动盘进行详细热网络/三维传热分析，整车制动模型保留前轴常规制动以及两侧后轴。**不等于任何真实量产车已安装此总成。**

## 首先读
- [**V0.4有来源的基准参数及动力/制动校核（最新权威）**](docs/REAR_DRIVE_V04_SOURCED_BASELINE.md)
- [V0.4参数文件](configs/baseline_vehicle.yaml)
- [Codex执行约束](AGENTS.md)
- [研究方法（旧版主体，需按V0.4替换前驱/差速器内容）](docs/RESEARCH_PLAN.md)
- [参数缺口（旧版主体，需按V0.4替换）](docs/PARAMETER_REGISTER.md)
- [Codex阶段规范](docs/CODEX_EXECUTION.md)
- [验证与风险](docs/VALIDATION_AND_RISKS.md)

## 公开数据线索
Toyota 2010 Prius MG2（参考单侧永磁电机）：60kW、207Nm、13500rpm，来源Toyota与ORNL。EPA有MG2 EMOT（电机+逆变器，不含减速器）ALPHA地图数据包；本仓库**尚未下载/验证地图内容**。大众ID.3车身（2765mm轴距、160km/h目标、215/55R18轮胎）仅用于外形量级参考。Brembo 09.9908.21后制动盘280×22mm仅用于几何参考，需重新设计内移安装并验证制动力与热容量。资料URL、来源等级及推导见权威V0.4文件。

## 历史资料
- `configs/archive/baseline_vehicle_v01_central_motor.yaml`：单电机+差速器，废弃。
- `configs/archive/baseline_vehicle_v03_front_dual_motor.yaml`：前驱双电机，废弃。
- `docs/DUAL_MOTOR_V03_ARCHITECTURE.md`、`docs/BASELINE_V02_AUDIT.md`、`configs/screening_scenarios_v02.yaml`：旧轴型、旧前后制动力分配，只能用来追溯设计变化，不能被程序当作运行输入。

## 阶段
M0单位和参数审计/新后轴动力学→M1 MATLAB再生/摩擦热源→M2单侧热阻网络→M3 CAD概念及安装约束→M4 ANSYS瞬态传热→M5局部Fluent→M6多目标代理优化→M7极端工况、验证及论文图表。
