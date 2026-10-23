# M4 P1-A 零再生单次制动热源基准

日期：2026-10-23。场景：`M4_P1A_NR_SINGLE_80KMH_06G_CASE0`。

**结论：P1-A概念热源基准及独立动力学/能量审计通过，等待研究者审查；M4整体仍为PARTIAL。** 本轮仅运行一次MATLAB单次场景生成和独立Python审计，没有ANSYS、Fluent、M2温度求解、预热、冷却、重复制动或优化。没有温度结果或降温结论。

## 1 输入、授权与复用边界

基线提交：`9eb27e074ce218da9843e241ea7e4cf21f49819b`；分支`stage/M4-ansys`，草稿[PR #5](https://github.com/alan9900/Thermal-coupling-analysis-under-drive-control-integration/pull/5)。本轮成果为该基线上的一个聚焦提交，最终交付SHA由Git和PR登记，不能将基线SHA冒称为新脚本已提交版本。

研究者本轮明确授权P1-A，取代旧文档对本项源项生成的暂停安排；其他计算继续暂停。本次没有修改已验收M0—M3的代码、配置、结果或标签，没有覆盖旧M1/M2或M4 studies数据。运行前工作区干净、分支正确；运行前后1404个既有受控文件哈希和全部阶段标签引用核对通过，当前阶段授权说明除外。

复用未修改的`m1_load`、`m1_options`、`m1_trace`、`m1_sources`及其内部`m1_point`等函数。M1模型目录最后提交为`ec134044c346e10cac3f7d31e0bfc99dc641ec13`。独立Python程序直接读取保存的CSV/JSON，并从原YAML参数重算物理关系，不调用MATLAB算法；MATLAB summary仅用于最后交叉核对。

| 项目 | 本次取值及来源 |
|---|---|
| 车型 | V0.4、1800 kg后驱双独立电机；单侧热域，无差速器 |
| 速度与减速度 | 80→0 km/h、0.6g；研究者指定单次制动 |
| 道路 | 平直，沿用M1风阻和滚阻，不忽略路阻 |
| 左右控制 | 轮速对称、后轴需求各半、两侧再生均关闭、充电上限命令0 kW |
| 前轴 | 保留整个前轴摩擦制动账本，不加载到单侧后盘 |
| 采样 | 原配置0.02 s；沿用`m1_trace`的均匀端点对齐，实际0.0199758571790134 s，共190点 |
| 制动时长 | 3.77543700683354 s，只有制动段，无预热或延长冷却段 |
| 热分配 | 原M1名义盘/片90%/10%，S3候选，非实测；保留原条件区间 |
| 再生回收 | 左右再生力、再生转矩、直流回收功率均严格为0 |

`configs/baseline_vehicle.yaml`、`configs/m1_heat_sources.yaml`和`configs/m1_source_partition.yaml`保持原样；首先核对其与既有M1 prepared inputs快照一致。输入参数、代码及输出的原始字节SHA256均已保存。M1旧来源登记使用的LF归一化文本SHA也另行核对，不混淆两种哈希定义。

## 2 独立动力学与功率结果

| 指标 | 结果 |
|---|---:|
| 动态后轴载荷比例 | 0.430650994575045 |
| 前轴法向载荷 | 10053.564738 N |
| 后轴法向载荷合计 | 7604.435262 N |
| 初始单侧后盘转矩 | 724.435358 N·m |
| 单侧后盘峰值转矩 | 737.782309 N·m |
| 初始/峰值单侧接触摩擦功率 | 48.783526 kW |
| 最高单台电机转速 | 5787.452476 rpm |
| 前后轮最大附着利用率F/N | 0.588，低于假设路面μ=0.8 |

Python逐点重算动态轴荷、`Froad = mg Crr + 0.5 ρ Cd A v²`及制动需求`B=ma−Froad`，前轴取`(1−fr)B`，每侧后轴取`fr B/2`。核对独立重构的减速度为−0.6g、无有效未满足需求、盘角速度等于本侧轮角速度、电机角速度为轮速9倍，以及`Pcontact=Fside v=Tdisc ωwheel`。左右全部对应列一致，包括NaN位置。

转矩低于旧忽略路阻的752.8 N·m筛查值，原因是本次明确计入风阻和滚阻；速度下降时风阻减少，摩擦转矩略增。停止端点的力/转矩沿用M1左极限制动需求表示，角速度和功率为零，不代表随后继续施加运动制动或建立驻车工况。

目标减速度在**假设轮胎附着和理想分配模型内**可实现；实际制动转矩容量、卡钳夹紧力及硬件控制尚未验证，不能据此作实车制动能力或安全认证。

## 3 整车能量账本

下表来自新CSV的独立积分，前轴为整轴，左右后轴分别计入一次。

| 能量项 | kJ |
|---|---:|
| 整车动能减少 | 444.444444444 |
| 前轴摩擦功 | 245.739973410 |
| 左后盘片接触摩擦功 | 92.937866711 |
| 右后盘片接触摩擦功 | 92.937866711 |
| 风阻及滚阻耗散 | 12.828737613 |
| 电池净能量/再生回收 | 0 |
| 已建模电机—逆变器及减速器损耗预算 | 0（省略未知空载项的模型近似） |

每侧盘片接触能量92.937866711 kJ中，盘沉积83.644080040 kJ，配对摩擦片沉积9.293786671 kJ。均为单盘两面合计，不能再乘2；其和不是整车444.444 kJ。前轴热未被错误计入单侧后盘。

电机铜耗、铁耗、转子/其他、逆变器以及减速器齿轮/轴承/其他工程分项在本次均为零预算；逐时分项分别闭合自身总预算，不把总损耗与其分项重复加载。分配模型的原始铁耗/转子形状权重只是归一化辅助量，**不是可以追加的热源**。逆变器仍独立记账、不加到绕组；转子/其他不能解读为磁钢单独损耗。

## 4 预登记阈值、实际检查与误差

阈值在MATLAB运行前写入独立配置并由preflight登记哈希，运行后未放宽。

| 检查 | 阈值 | 实际结果 |
|---|---:|---:|
| 独立单点功率最大残差 | 0.001 W（原M1） | 9.313225746×10⁻¹⁰ W，PASS |
| 整个时间窗累计能量最大相对残差 | 10⁻⁶（原M1） | 4.452886060×10⁻¹⁵，PASS |
| 累计整车能量最大绝对残差 | 对应上项动能归一化 | 1.979060471×10⁻⁹ J；末端0 J |
| 电机/减速器/盘片分项闭合 | 10⁻⁷ W（原接口） | 全部PASS |
| 动力学需求与附着 | 力容差10⁻⁶ N，附着容差10⁻¹⁰ | PASS |
| 速度比例、左右对称 | 绝对容差10⁻⁸ | PASS |
| 关闭再生的端口 | 严格为0 | PASS |
| 独立解析路阻功与梯形积分差 | 相对初始整车动能≤10⁻⁶ | 0.110291941 J，即2.481568677×10⁻⁷，PASS |

最后一项是有限采样的解析积分交叉核对误差，不能与几乎机器精度的离散整车闭合残差混为一项。解析路阻耗散为12.828627321 kJ；保存时序梯形积分为12.828737613 kJ。报告同时保留两者，没有用离散闭合掩盖积分误差。

共14组独立物理/接口检查通过；另外进行5项**内存副本故障注入**，不修改真实输出：非零再生、盘热重复加载、将校准绕组NaN改0、不可行标志、错误电机速比，均被程序正确拒绝。原始校准绕组两侧各190个采样点全部保持NaN；配置及JSON中的真实未知参数保持null。

失败项：本轮实际运行无失败项。未执行项：ANSYS/Fluent/M2温度、预热、冷却、重复制动、热源扩展或优化；未完成的真实损耗及硬件标定未被列为数值PASS。

## 5 实际命令与复现

以下三条均在仓库根目录实际执行，退出码均为0；未运行`run_m1`、`run_m1_sources`或任何温度求解入口。

```powershell
& 'C:/Users/90521/AppData/Local/Programs/Python/Python313/python.exe' scripts/m4/check_no_regen_brake.py --preflight
& 'F:/Program Files/MATLAB/R2025a/bin/matlab.exe' -batch "addpath('scripts/m4'); prepare_no_regen_brake" -logfile 'tmp/m4_p1a_matlab.log'
& 'C:/Users/90521/AppData/Local/Programs/Python/Python313/python.exe' scripts/m4/check_no_regen_brake.py
```

软件实际为MATLAB 25.1.0.2943329 / R2025a、Python 3.13.12、NumPy 2.5.3。输出入口拒绝覆盖已有场景，preflight也拒绝覆盖既有登记；不能直接在当前已交付目录重复执行生成命令。

完整重新生成应使用独立的交付前基线副本：从上述父提交`9eb27e0...`创建独立克隆/工作副本，分支名为`stage/M4-ansys`，仅将本次新增配置及两个生成/检查脚本复制进去，再执行这三条命令。这样保留本仓库首次结果和证据不动，且复算副本没有旧的本任务输出/登记。源码以preflight的逐文件SHA256识别，结果中的父提交不冒充脚本交付提交。

## 6 文件入口、未知量和停止边界

- [独立配置](../configs/m4_no_regen_brake_baseline.json)
- [MATLAB生成入口](../scripts/m4/prepare_no_regen_brake.m)、[独立Python审计](../scripts/m4/check_no_regen_brake.py)
- [运行前登记](../results/m4/no_regen_p1a_preflight.json)
- [整车时序](../results/m4/no_regen_baseline/vehicle_trace.csv)
- [左侧CSV](../results/m4/no_regen_baseline/left_sources.csv)、[左侧JSON](../results/m4/no_regen_baseline/left_sources.json)
- [右侧CSV](../results/m4/no_regen_baseline/right_sources.csv)、[右侧JSON](../results/m4/no_regen_baseline/right_sources.json)
- [运行快照](../results/m4/no_regen_baseline/run_metadata.json)、[MATLAB日志](../results/m4/no_regen_baseline/matlab_generation.log)
- [独立检查结果](../results/m4/no_regen_baseline/independent_checks.json)、[累计能量时序](../results/m4/no_regen_baseline/independent_energy_history.csv)、[故障拒绝记录](../results/m4/no_regen_baseline/checker_regression_tests.json)
- [生成文件SHA](../results/m4/no_regen_baseline/generated_files.json)、[审计文件SHA](../results/m4/no_regen_baseline/audit_files.json)

真实绕组内部损耗图、停用电机铁耗/拖曳、逆变器待机功率、空载齿轮/轴承/搅油损耗均未知。零传递功率下分项预算为0来自现有M1近似，**不代表旋转实物无发热**；盘片90/10、μ=0.8、车身参数和等附着分配仍为概念假设或有限来源参照。原分项配置的100°C绕组温度只是形状权重参数，不是本次初温或驱动预热结果；本次没有温度状态。

本次只交付P1-A，停止执行并等待研究者审查。下一步建议先审核源项与未建模拖曳边界，再另行授权匹配零再生的M2对照或Case0温度计算；本报告不授权其启动。PR #5保持草稿，不合并、不创建M4-v1.0、不进入M5。
