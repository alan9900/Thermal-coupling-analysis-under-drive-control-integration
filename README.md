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
Toyota 2010 Prius MG2（参考单侧永磁电机）：60kW、207Nm、13500rpm，来源Toyota与ORNL。EPA的MG2 EMOT（电机+逆变器，不含减速器）原始包已完成下载与M0审计：数值表0–13000rpm、−200至200Nm，**再生区域为驱动损耗镜像估计**。独立电机及逆变器有137个配对驱动效率点，绕组损耗图仍未知。大众ID.3车身（2765mm轴距、160km/h目标、215/55R18轮胎）仅用于外形量级参考。Brembo 09.9908.21后制动盘280×22mm仅用于几何参考，需重新设计内移安装并验证制动力与热容量。资料URL、来源等级及推导见权威V0.4文件。

## M0交付（2026-10-18）

**验收待批准**：[M0验收摘要](reports/M0_ACCEPTANCE_SUMMARY.md)，[验收PR #1](https://github.com/alan9900/Thermal-coupling-analysis-under-drive-control-integration/pull/1)。原成果提交`2ba858b`仅为历史候选；本次在`stage/M0-parameter-audit`补齐复核证据及PR，正式Tag尚未创建。技术交付完成不代表用户已批准。

- [参数审查报告 Markdown](reports/M0_report.md) / [Word](reports/M0_report.docx) / [PDF](reports/M0_report.pdf)
- [运行命令与输出说明](scripts/m0/README.md)，优先MATLAB R2025a完成参数及制动积分复核
- [官方来源和下载哈希](data/raw/m0/manifest.json)、[EPA包内文件清单](results/m0/epa_zip_inventory.json)
- [配置参数审查CSV](results/m0/parameter_audit.csv)、[制动转矩/功率/能量CSV](results/m0/braking_review.csv)、[实际校验结果](results/m0/validation.json)

0.6g、100→0km/h、无路阻及零再生时，后轴单盘752.84N·m、初始63.37kW、摩擦功149.53kJ。160km/h转速与峰值包络筛查通过，连续高速能力未验证。修正了旧V0.4稿件后驱加速附着公式的分母符号。39项配置值保持null。**当前停在M0，未经用户确认不开始M1、ANSYS或优化。**

## 历史资料
- `configs/archive/baseline_vehicle_v01_central_motor.yaml`：单电机+差速器，废弃。
- `configs/archive/baseline_vehicle_v03_front_dual_motor.yaml`：前驱双电机，废弃。
- `docs/DUAL_MOTOR_V03_ARCHITECTURE.md`、`docs/BASELINE_V02_AUDIT.md`、`configs/screening_scenarios_v02.yaml`：旧轴型、旧前后制动力分配，只能用来追溯设计变化，不能被程序当作运行输入。

## 阶段
M0单位和参数审计/新后轴动力学→M1 MATLAB再生/摩擦热源→M2单侧热阻网络→M3 CAD概念及安装约束→M4 ANSYS瞬态传热→M5局部Fluent→M6多目标代理优化→M7极端工况、验证及论文图表。

## 阶段版本与回退
每个阶段均使用独立开发分支、Git提交、PR人工验收与**批准后不可移动的里程碑Tag**（`M0-v1.0`到`M7-v1.0`）。详见 [Git阶段版本管理制度](docs/GIT_VERSIONING_POLICY.md) 和 [里程碑版本登记](docs/STAGE_VERSIONS.md)。未通过验收不能标记为已完成。既有M0报告与输出不代表已获用户批准打正式Tag。
