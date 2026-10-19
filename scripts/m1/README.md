# M1 多热源与功率账本（V0.4，候选版）

基线是已验收的`M0-v1.0`，main合并提交`b13f265b1ff0add1f9e8b166d2c1bfa4ac8a8d16`。当前仅做M1，不建立温度求解器、ANSYS模型、CFD或优化。

## 运行

在仓库根目录：

```powershell
py scripts/m1/prepare_inputs.py
& 'F:\Program Files\MATLAB\R2025a\bin\matlab.exe' -batch "addpath('scripts/m1'); run_m1" -logfile results/m1/matlab_run.log
py scripts/m1/check_outputs.py
& 'F:\Program Files\MATLAB\R2025a\bin\matlab.exe' -batch "addpath('scripts/m1'); run_m1_sources" -logfile results/m1/source_run.log
py scripts/m1/check_sources.py
py scripts/m1/plot_sensitivity.py
```

Python依赖沿用`scripts/m0/requirements.txt`；MATLAB R2025a仅用基础函数，程序不依赖ALPHA/REVS类。MATLAB路径按实际安装调整。不修改M0配置及原结果；所有新假设位于`configs/m1_heat_sources.yaml`。Python程序禁止用`-O`关闭审查断言。

## 物理接口

- `m1_load(root,strict)`：读取M0原始数字和137个配对驱动效率点，构造无外推插值器。`strict=true`因缺已验证热源输入而明确拒绝。
- `m1_emot(c,rpm,T,active)`：单侧电机轴机械功率和直流功率均用带符号约定，联合热损失为`Pdc-T*omega`。正转矩驱动、负转矩再生；电机与逆变器的驱动热量只在原稀疏数据凸包内按测量损耗比估计，凸包之外及再生模式不拆分。绕组热源一律NaN，不能用于已验证温度求解。
- `m1_gear(c,Pwheel)`：方向分别采用驱动／反拖常数效率，作为S3估算接口；不称为真实减速器损耗图。
- `m1_point(c,v,a,o)`：单点纵向动力学、动态轴荷、前轴和左右独立后轮、再生／摩擦分配、总电池功率约束及能量账本。
- `m1_trace(...)`：恒减速／短时驱动的源项时序，明确输出需求是否可实现。附着或功率不足时保留未满足需求及其功率，不能仍称给定轨迹可实现。
- `m1_tests`：独立解析回归、物理符号、限值、严格模式拒绝、故障及步长检查。

不把未知数据填零：真实绕组损耗和已验证温限保持未知。停用电驱时采用“未计入拖曳和待机耗电”的显式零损耗假设，和已通电零转矩的地图损耗区分。常数齿轮效率在未传功时也不计空载拖曳／搅油损耗，不代表真实部件无发热。

## 结果与证据

`results/m1/inputs.json`记录配置和输入哈希；`case_summary.csv`为18组制动组合及5组补充案例；`traces/*.csv`为完整功率及转矩时序；`m1_results.mat`保留MATLAB结果；PNG/SVG为曲线；`tests.json`、`validation.json`及`independent_checks.json`分别记录MATLAB测试、整批算例和独立Python复核。

主要字段的单位由后缀明确：`_W`功率、`_kJ`能量、`_Nm`转矩、`_N`力、`_rpm`转速、`_rad_s`角速度。`_left`和`_right`表示各自一侧；`front_axle`为整个前轴；`total`为整车或两侧合计。`disc_contact`为盘片总接触摩擦功，`disc_deposited_heat_assumed`才是按假设份额分入盘的热。

电池功率上限是**左右两台合计的直流侧功率**。程序对每一时刻使用联合损耗图及共享功率预算求解，不能把“每侧30kW”当作“整车30kW”。高SOC／温度限充是明确标记的场景状态／乘数，不是真实BMS标定。

## 适用边界

EPA图仅650V、0–13000rpm，负转矩为镜像估计。左右轮速不同的案例是强加运动学接口测试，额外的带符号功率端口`lr_kinematic_exchange_W`防止把不对称功误算入纵向动能；不宣称建立了车辆横摆模型。驱动测试短于18秒，但这不是新的热能力证明。盘片热分配0.90及0.85–0.95区间、减速器0.96效率均为工程假设。

数值检查通过与真实资料齐备分开登记。阶段应保持`PARTIAL`，直至内部电机损耗、再生分配、减速器图、盘片分配和电池边界的证据达到相应要求。M1 PR未经用户批准不合并、不打M1正式Tag、不进入M2。

## 本轮工程分项接口

新增独立配置 `configs/m1_source_partition.yaml`，保留原数据NaN/null。可选 `py scripts/m1/collect_sources.py` 重新获取公开方法资料（会更新检索时间/哈希；应在prepare_inputs之前运行）；仓库已保存可离线复算的资料登记，无需每次重下。分项层用既有总损耗约束下的物理形状权重，不能解释为已标定的绝对3RI²或磁钢损耗。

`m1_sources(c,tr,'left','strict')` 当前按预期抛出 `m1:StrictEvidenceGap`；`engineering` 才能输出S3分项候选。所有16参数区间均必需，缺失/null或越界拒绝。完整接口合同见 `docs/M1_HEAT_SOURCE_INTERFACE.md`，方法与范围依据见 `docs/M1_SOURCE_REVIEW.md`。

`run_m1_sources` 必须使用刚由同一输入运行的 `run_m1` 输出。原23条trace之外，保存左右46对CSV/JSON、单侧能量、161×2敏感性运行、完整参数矩阵、MAT及分项/不确定性曲线到 `results/m1/engineering/`。新增11组检查与原18组分别登记。`check_sources.py` 独立复核原始NaN、分项与总量、区间、322次敏感性及M0受保护路径。`plot_sensitivity.py` 依赖matplotlib，仅绘制保存的MATLAB结果。

上下界以现有总损耗固定为条件，不是实测置信区间；各分项上界不能同时当作一个热源场景加载。需要联合场景时，把完整参数向量作为overrides传入，再输出整套守恒时序。逆变器默认外部热边界，盘/片是单盘两面合计，不能再乘2。本层不求解任何温度。

## 报告生成

```powershell
py scripts/m1/report_qa.py reference
& 'C:\Users\90521\.codex\skills\pandoc-report-word\scripts\Convert-PandocReport.ps1' -InputPath reports/M1_report.md -OutputPath reports/M1_report.docx -ReferenceDoc reports/M1_reference.docx
py scripts/m1/report_qa.py render
```

作者源为Markdown，DOCX由本地pandoc-report-word技能脚本转换；也可用仓库中保存的`scripts/m0/Convert-PandocReport.ps1`。后续仅整理表头、表格分页及字体间距，不修改数据或公式。Word独立隐藏实例导出PDF后，逐页目视检查并记录`results/m1/document_checks.json`，数学对象保持可编辑。
