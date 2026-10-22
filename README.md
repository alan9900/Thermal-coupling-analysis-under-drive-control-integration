# 后驱分布式双电机驱制融合热耦合研究（V0.4）

**当前权威研究架构**：1800kg概念纯电动车，后轴左右各一套独立电驱单元（单侧60kW参考电机+两级约9:1减速器+减速器输出端内移式盘式摩擦制动器），**无机械差速器**；只对单侧电机—减速器—制动盘进行详细热网络/三维传热分析，整车制动模型保留前轴常规制动以及两侧后轴。**不等于任何真实量产车已安装此总成。**

## 当前工作安排（2026-10-22）

**后续仿真等工作暂不考虑再生制动。** 当前计划为[无再生制动热耦合研究工作计划](docs/NO_REGEN_WORK_PLAN.md)，重点是驱动预热后零再生摩擦制动下，各部件温升、制动附加热影响及传热路径。先完成Case0数值验证，再按批准的阶段开展空气换热与结构比较。现有三轴、两级斜齿9:1、50mm输出轴及Case0/A/B/C几何保持。

M0—M3已限定验收并归档；M4仍为PARTIAL，位于`stage/M4-ansys`和草稿[PR #5](https://github.com/alan9900/Thermal-coupling-analysis-under-drive-control-integration/pull/5)。**当前仅更新计划和GitHub，仿真继续暂停，等待研究者新的执行命令。** 没有新增零再生热源或温度场；既有30kW再生限制下的报告/云图保留历史含义，不改名或覆盖。当前[M4报告](reports/M4_report.md)、[云图Word讲解](reports/M4_contour_explained.docx)及[阶段登记](docs/STAGE_VERSIONS.md)可供回顾。下文按交付时序保留历史介绍，当前状态以上述安排及最新阶段登记为准。

## 首先读
- [**当前无再生制动工作计划及暂停执行边界**](docs/NO_REGEN_WORK_PLAN.md)
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

**2026-10-20当前状态**：M0经用户授权简验通过，[PR #1](https://github.com/alan9900/Thermal-coupling-analysis-under-drive-control-integration/pull/1)已合并，附注Tag `M0-v1.0`已推送并验证，固定指向`b13f265`。[历史验收摘要](reports/M0_ACCEPTANCE_SUMMARY.md)及工作安排图保留其生成时状态。M1与M2均按限定概念范围验收并正式归档；M3已获开发授权，独立PR #4送审，未经批准不合并M3或进入M4。

- [参数审查报告 Markdown](reports/M0_report.md) / [Word](reports/M0_report.docx) / [PDF](reports/M0_report.pdf)
- [运行命令与输出说明](scripts/m0/README.md)，优先MATLAB R2025a完成参数及制动积分复核
- [官方来源和下载哈希](data/raw/m0/manifest.json)、[EPA包内文件清单](results/m0/epa_zip_inventory.json)
- [配置参数审查CSV](results/m0/parameter_audit.csv)、[制动转矩/功率/能量CSV](results/m0/braking_review.csv)、[实际校验结果](results/m0/validation.json)

0.6g、100→0km/h、无路阻及零再生时，后轴单盘752.84N·m、初始63.37kW、摩擦功149.53kJ。160km/h转速与峰值包络筛查通过，连续高速能力未验证。修正了旧V0.4稿件后驱加速附着公式的分母符号。39项配置值保持null。

## M1数值模型交付（2026-10-19，概念范围APPROVED；真实标定PARTIAL）

经用户授权，从M0-v1.0创建 `stage/M1-heat-sources`。已实现左右独立动力学、EPA联合损耗、有限范围的电机/逆变器估计拆分、双向减速器功率、再生直流上限和盘片接触功账本。本轮进一步提供独立S3工程铜/铁/转子其他/逆变器、齿轮/轴承/其他及盘片分项，含16参数条件区间与敏感性。R2025a实际通过原18+新11测试组、23整车轨迹、46单侧接口和322次敏感性计算，Python独立复核通过。真实绕组数据仍NaN/null，严格数据模式明确拒绝，工程输出不冒称标定。

概念数值关卡已获研究者批准，真实部件标定仍为PARTIAL。接口及来源见 [输入合同](docs/M1_HEAT_SOURCE_INTERFACE.md)、[资料审查](docs/M1_SOURCE_REVIEW.md) 和 [验收表](reports/M1_ACCEPTANCE_CHECKLIST.md)。上下界以现有总损耗固定为条件，不代表真实置信区间；M1阶段不包含温度求解或实验验证。

- [M1报告](reports/M1_report.md) / [Word](reports/M1_report.docx) / [PDF](reports/M1_report.pdf)
- [复现说明](scripts/m1/README.md)、[模型配置](configs/m1_heat_sources.yaml)、[运行与曲线证据](results/m1/)
- [PR #2](https://github.com/alan9900/Thermal-coupling-analysis-under-drive-control-integration/pull/2)已合并；正式附注Tag `M1-v1.0`远端已核验，目标main提交`9d545ab39a3efcce857573af74f7e325b74a2b15`。

## M2概念瞬态热网络（2026-10-20，限定概念范围APPROVED）

13动态节点LPTN包含盘、片/钳、轴、轴承、齿轮、油、壳体、电机定子/绕组/转子其他、护罩和局部空气；环境与冷却液为边界。4基础场景、3路径移除、18敏感性场景已实际运行R2025a；11组测试及独立Python/SciPy复核通过。三种路径保留有符号热流、正向累计与净热量；全网络/电驱子域分别核算储热和边界。所有温度为S3概念预测，未取得实物标定。

- [M2报告](reports/M2_report.md) / [Word](reports/M2_report.docx) / [PDF](reports/M2_report.pdf) / [验收检查表](reports/M2_ACCEPTANCE_CHECKLIST.md)
- [复现说明](scripts/m2/README.md)、[配置](configs/m2_thermal_network.yaml)、[来源审查](docs/M2_SOURCE_REVIEW.md)、[结果与曲线](results/m2/)
- [PR #3](https://github.com/alan9900/Thermal-coupling-analysis-under-drive-control-integration/pull/3)已合并；M2-v1.0已实际推送并核验，目标`1d51c22d94577ff8f52be785300b5f6b4aadee37`。真实几何/热阻/换热/温度标定仍未完成。

## M3参数化几何（2026-10-20，概念CAD交付待验收）

CadQuery2.8/OpenCascade7.9已实际建立单侧电机、两级9:1减速器、内移通风盘、卡钳/支架、轴承支承与可拆罩体。Case0真正没有新增罩；CaseA单层、CaseB双层、CaseC一体通道，公共32体一致。56个STEP已回读，283候选对无正体积干涉；8组测试、18齿轮相位和几何/静力/视角筛查通过。2187解析组合中729被拒绝；45mm轴静力余量很小，制造、轴承寿命、热配合和实际装车仍未验证，不声称温降。

- [参数化源与复现](scripts/m3/README.md)、[配置](configs/m3_geometry.yaml)、[CAD与STEP](cad/m3/README.md)、[原始验证](results/m3/)
- [报告](reports/M3_report.md) / [Word](reports/M3_report.docx) / [PDF](reports/M3_report.pdf) / [验收表](reports/M3_ACCEPTANCE_CHECKLIST.md)
- [草稿PR #4](https://github.com/alan9900/Thermal-coupling-analysis-under-drive-control-integration/pull/4)待研究者审批；未合并、未Tag，M4 ANSYS/Fluent未开展。

## 历史资料
- `configs/archive/baseline_vehicle_v01_central_motor.yaml`：单电机+差速器，废弃。
- `configs/archive/baseline_vehicle_v03_front_dual_motor.yaml`：前驱双电机，废弃。
- `docs/DUAL_MOTOR_V03_ARCHITECTURE.md`、`docs/BASELINE_V02_AUDIT.md`、`configs/screening_scenarios_v02.yaml`：旧轴型、旧前后制动力分配，只能用来追溯设计变化，不能被程序当作运行输入。

## 阶段
M0参数审查→M1热源接口→M2单侧热网络→M3参数化几何→M4零再生Case0瞬态热耦合及数值验证→M5零再生热负荷下局部空气换热→M6隔热导流优化→M7综合验证及论文。后续热源和对照采用零再生场景，历史M0—M3版本不覆盖。

[工作安排图片（2026-10-19，图稿v1）](reports/planning/research_work_plan_v04_2026-10-19_v1.png)：M0–M7共8阶段，列明任务、交付物和验收流程。图中状态为生成时快照；当前以阶段登记和上文为准，工期尚未确定。

## 阶段版本与回退
每个阶段均使用独立开发分支、Git提交、PR人工验收与**批准后不可移动的里程碑Tag**（`M0-v1.0`到`M7-v1.0`）。详见 [Git阶段版本管理制度](docs/GIT_VERSIONING_POLICY.md) 和 [里程碑版本登记](docs/STAGE_VERSIONS.md)。M0—M3已正式归档；M4草稿待审且暂停计算，未经批准不合并M4、不创建M4正式Tag、不进入M5。
