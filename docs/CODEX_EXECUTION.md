> **V0.4权威架构提示（2026-10-18）**：本文件编写于更早的前驱/中央电驱方案，涉及 `front`、中央电机、差速器、前轴制动盘转矩的具体数值或指令已失效。当前方案为**后驱双独立电机**（每侧参考60kW/207Nm/13500rpm，研究软件限扭130Nm）、**每侧9.0独立减速器和内移盘**、**只分析单侧热场**。必须优先以 [V0.4权威研究说明](REAR_DRIVE_V04_SOURCED_BASELINE.md) 与 [当前配置](../configs/baseline_vehicle.yaml) 为准。以下仅保留通用方法及历史追溯；Codex不可执行与V0.4冲突的旧架构说明。

> **V0.3 架构变更通知（2026-10-18，必须先读）**：本文件原编写于“中央单电机+机械差速器+左右输出盘”阶段，其中**具体机械拓扑、单电机120 kW/260 N·m与差速器相关指令均已失效**。现行方案为左右各一台60kW/130N·m独立电机及9.0减速器、每侧输出端内移盘、**无差速器**、只分析单侧详细热场。现行权威资料为 [V0.3架构](DUAL_MOTOR_V03_ARCHITECTURE.md) 和 [V0.3配置](../configs/baseline_vehicle.yaml)。以下保留作为方法论/变更历史参考，Codex不得照搬失效指令。

# Codex 按阶段实施任务与验收

## 共同交付协议
每阶段需要：(1)可运行脚本及README命令；(2)输入配置和来源；(3)原始输出CSV/MAT；(4)图PNG+矢量格式；(5)物理单元测试/回归结果；(6) `reports/Mx_report.md` 包含运行环境、版本、git commit、已通过项、未知项、误差与下一步。没有商业软件时不能伪造运行结果。图表中标注 ASSUMED/VALIDATED/SYNTHETIC。禁止未经批准进入下一阶段。

| 阶段 | Codex工作 | 验收关卡 |
|---|---|---|
| M0 参数化 | 读取YAML或提供无额外依赖的MATLAB config adapter；字段/单位/范围审计；生成parameter_audit.csv；定义车辆-左右制动盘-电驱拓扑 | 必需字段缺失被明确报告；单位、速比、力矩方向与结构一致；提交M0报告 |
| M1 MATLAB热源 | 车辆纵向动力学、动态轴荷、前后轴及左右制动力矩；驱动/再生限制；制动盘/片热分配；电机正反向损耗；减速器正反拖损耗MAP接口 | 100→0解析能量校验；再生0/最大限值；盘角速度1:1；左右对称与不对称；能量残差定义并测试 |
| M2 MATLAB瞬态热网络 | 多节点C/R网络、辐射、对流、输出轴导热、温变参数、时间积分；热源时间序列输入 | 无热源时向环境温度收敛；封闭系统总能守恒；双向热流符号正确；时间步收敛；敏感性 |
| M3 结构方案 | 参数化接口定义，简单CAD/示意图；Case0/A/B/C/D定义、材料、安装约束、接触/间隙 | 可复建、无干涉及间隙可行性检查；未验证项列为blocker |
| M4 Mechanical | 结构热基准模型，瞬态导热、盘与壳体辐射、定量冷却边界、热流收支 | 网格无关性和时间步独立性；M2交叉校验；基准温度/热流结果可重复 |
| M5 Fluent | 选择典型工况的局部旋转流动、导流罩的风量和换热分析；计算不同结构传热系数 | 质量/能量收支、边界敏感性、网格收敛；不得称MRF静态等于完整瞬态 |
| M6 优化 | DOE、代理训练测试、NSGA-II、Pareto，回代高精度模型 | 独立验证误差阈值事前指定；优化解可行；至少3个代表解复核；质量/温度权衡说明 |
| M7 验证与论文 | C1-C4工况，初温/再生变化/材料不确定性，输出论文级图表与报告 | 完整复现链；不得没有实测称“实验验证”；明确风险及适用范围 |

## 建议实现的最小接口
- `load_config(path)` 返回结构体并拒绝错误单位/缺字段。
- `vehicle_braking_trace(config, t, v)` 返回轮端制动力、动态轴荷、SOC/再生约束。
- `brake_heat(left/right,t)` 返回摩擦生热及盘片分配。
- `motor_loss(torque,speed,mode,temp)`、`gear_loss(torque,speed,mode,temp)` 明确MAP缺失策略。
- `thermal_rhs(t,T,heat_sources,parameters)` 返回各节点温度变化率与各路径热流。
- `run_case(config,case_id)` 保存原始CSV/MAT、元数据、绘图和自动质量检查。

## 第一条可直接交给 Codex 的命令
“先阅读 AGENTS.md、README.md、docs/RESEARCH_PLAN.md、docs/PARAMETER_REGISTER.md、docs/CODEX_EXECUTION.md、docs/VALIDATION_AND_RISKS.md、configs/baseline_vehicle.yaml。**只做M0**：建立MATLAB R2025a兼容的配置读取、单位/数值/物理逻辑审计；生成 parameter_audit.csv 与 M0_report.md。所有未知值保持null，输出缺失的重要参数；不要开展M1、CAD或ANSYS。提交PR/commit，报告运行过和未运行的测试，并列出下一步需我确认的问题。”

## 阶段成果必须存Git版本
**强制阅读并遵守 [GIT_VERSIONING_POLICY.md](GIT_VERSIONING_POLICY.md)**：每个M0–M7阶段独立分支、分批commit、完整验收报告、PR审核、批准后合并main并创建固定Tag（例`M1-v1.0`），按`docs/STAGE_VERSIONS.md`登记。旧M0必须先确认实际完成及审核状态才能补打tag。无tag权限不得虚构结果。
