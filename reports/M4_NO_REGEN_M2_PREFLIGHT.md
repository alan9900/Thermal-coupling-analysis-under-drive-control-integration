# M4 P2-A 零再生制动热源的M2输入适配与预检

日期：2026-10-23。场景：`M4_P2A_NR_SINGLE_80KMH_06G_M2_INPUT`。

**结论：单侧M2区间平均输入准备及独立预检通过，等待研究者审查；没有执行温度求解，M4仍PARTIAL。** P1-A输入、M2正式配置/代码/结果及M0—M3标签未改动。开始时工作区干净、分支为`stage/M4-ansys`，HEAD为指定P1-A提交`1db75d9f7cf58560b8ee01d444e2160a72d3545e`；本轮成果在其上形成一个聚焦提交，交付SHA由Git和草稿[PR #5](https://github.com/alan9900/Thermal-coupling-analysis-under-drive-control-integration/pull/5)登记。

## 输入与适配

读取P1-A的整车时序、左右CSV/JSON、原独立审计、运行快照及其哈希索引，核对本地字节与P1-A正式交付提交的Git文件一致，未重新生成P1-A。左侧用于单侧热域，右侧仅用于对称性检查；单侧及盘面倍数均为1，不计入前轴和另一侧热量。

复用原`m2_load`、`m2_network`和`m2_forcing`，时间步来自未修改的`configs/m2_thermal_network.yaml:numerics.maximum_step_s=0.25 s`。原`m2_forcing`将循环结构写在入口中，因此适配器仅使用其“零循环、唯一末尾表格、时间倍率1”的单段载体，传入实际P1-A制动表格；输出分段明确重命名为`single_brake`。这只复用原解析积分核，不新增冷却、停歇、驱动或循环，不改变13节点热网络参数。

沿用原端点对齐规则，区间边界为`linspace(0, 3.77543700683354, 17)`，共16个完整区间，实际均匀步长约0.235964812927096 s。每个区间对原始线性功率精确积分后除以区间长度，未抽点或跨工况插值。区间CSV沿用`m2_export`的源项列约定，但未调用该函数，避免构造虚假温度结果；另保存可直接读取的`f`结构和预期掩码至MAT文件，并实际回读核验。

## 源项与13节点映射

| 候选源项 | 原M2目标节点/位置 |
|---|---|
| 铜耗、铁耗、转子/其他 | winding、stator、rotor_other |
| 逆变器 | EXTERNAL，MATLAB目标索引0，不进入电驱热域 |
| 齿面、轴承、其他减速器损耗 | gears、output_bearing、oil |
| 单盘、配对摩擦片（两面已合计） | disc、pad_caliper |

映射索引从原`m2_simulate.m`文本读取为`[10 9 11 0 5 4 6 1 2]`，**没有执行该函数**。后续预期源项掩码为`[0,0,1]`，本次只导出其节点热功率预览，不积分温度。读取全部13节点、22条内部传热边、热容、边界系数及参数范围；Python同时核对原YAML和归档的编译网络，未修改任何热容、热阻、视角系数或冷却参数。

## 独立预检与数值误差

Python与MATLAB采用不同实现：MATLAB使用原函数内的分段线性累计解析积分；Python逐个裁剪原始采样区间与目标区间的交集，积分交集两端线性功率。输入哈希、时间覆盖、单位、左右对称、单侧倍数、原始未知量、节点映射和MATLAB调用记录分别检查。

| 检查 | 运行前阈值 | 实际最大值 |
|---|---:|---:|
| 各热源及参考预算积分差 | 1×10⁻⁶ J（原m2_forcing） | 1.455191523×10⁻¹¹ J |
| 积分差相对各源热量，分母至少1 J | 1×10⁻⁶（M2配置） | 1.739742397×10⁻¹⁶ |
| 电机、减速器、盘片分项功率闭合 | 1×10⁻⁷ W（原m2_forcing） | 2.291926648×10⁻¹⁰ W |
| 独立逐区间功率均值差 | 1×10⁻⁷ W | 2.146407496×10⁻¹⁰ W |
| 时间边界/最大步长核对 | 1×10⁻¹⁰ s容差 | PASS，完整覆盖单次制动 |

阈值、输入和新脚本SHA256在实际MATLAB运行前登记，运行后未修改或放宽。12组独立预检全部通过；11项内存副本故障注入全部正确拒绝，覆盖哈希变化、缺字段、输入/输出单位错误、双侧重复能量、以抽点代替积分、校准绕组NaN被填0、错误掩码、逆变器加载绕组、时窗变化和缺节点。真实CSV/JSON未被故障测试修改。1424个既有文件及全部阶段标签保护检查通过。

| 单侧热量 | 原始线性时序积分/J | 区间平均积分/J | 差/J |
|---|---:|---:|---:|
| 盘 | 83644.08003953523 | 83644.08003953524 | 1.4552×10⁻¹¹ |
| 片 | 9293.786671059475 | 9293.786671059475 | 0 |
| 单盘接触摩擦功预算 | 92937.86671059478 | 92937.86671059477 | −1.4552×10⁻¹¹ |
| 电机各分项、逆变器、减速器各分项及其预算 | 0 | 0 | 0 |

最后一行零预算来自P1-A对停用电驱及零传功的既有近似，**不表示实物空载拖曳、逆变器待机或搅油损耗已知为零**。原始190点校准绕组和16区间校准绕组列均为NaN，JSON未知量保持null。EPA联合损耗未被替代为铜耗；原形状权重没有被追加成热源。

## 实际执行命令与成果

下列三条均实际执行且退出码为0。MATLAB实际为25.1.0.2943329 / R2025a；Python 3.13.12、NumPy 2.5.3。没有运行`run_m2`、`m2_simulate`、`m2_flux`、`m2_export`、ANSYS或Fluent。调用记录仅含`m2_load`、`m2_network`及其append、`m2_forcing`及其primitive；MAT文件只有输入`f`和掩码，没有温度结果。

```powershell
& 'C:/Users/90521/AppData/Local/Programs/Python/Python313/python.exe' scripts/m4/check_no_regen_m2_forcing.py --preflight
& 'F:/Program Files/MATLAB/R2025a/bin/matlab.exe' -batch "addpath('scripts/m4'); prepare_no_regen_m2_forcing" -logfile 'tmp/m4_p2a_matlab.log'
& 'C:/Users/90521/AppData/Local/Programs/Python/Python313/python.exe' scripts/m4/check_no_regen_m2_forcing.py
```

- [独立配置](../configs/m4_no_regen_m2_baseline.json)、[MATLAB适配入口](../scripts/m4/prepare_no_regen_m2_forcing.m)、[Python预检](../scripts/m4/check_no_regen_m2_forcing.py)
- [运行前阈值与输入哈希](../results/m4/no_regen_m2_preflight.json)
- [区间平均CSV](../results/m4/no_regen_m2_baseline/single_brake_forcing.csv)、[配套JSON](../results/m4/no_regen_m2_baseline/single_brake_forcing.json)、[原M2输入结构MAT](../results/m4/no_regen_m2_baseline/m2_forcing_input.mat)
- [节点输入功率预览](../results/m4/no_regen_m2_baseline/node_source_input.csv)、[13节点参数快照](../results/m4/no_regen_m2_baseline/compiled_network_input.json)、[源项映射](../results/m4/no_regen_m2_baseline/source_mapping.json)
- [独立预检结果](../results/m4/no_regen_m2_baseline/independent_preflight.json)、[逐项积分审计](../results/m4/no_regen_m2_baseline/source_integral_audit.csv)、[故障拒绝记录](../results/m4/no_regen_m2_baseline/checker_regression_tests.json)
- [MATLAB日志](../results/m4/no_regen_m2_baseline/matlab_preparation.log)、[MATLAB输入/调用记录](../results/m4/no_regen_m2_baseline/matlab_input_checks.json)、[生成文件哈希](../results/m4/no_regen_m2_baseline/generated_files.json)、[审计文件哈希](../results/m4/no_regen_m2_baseline/audit_files.json)

入口拒绝覆盖现有输出及preflight。重新生成应在P1-A父基线`1db75d9...`的独立工作副本中仅复制本轮新增配置/两个脚本，再运行上述命令；不要移动或覆盖本仓库首次证据。文件SHA256标识新增代码，父提交不冒充交付提交。

## 未解决问题与下一步条件

失败项：本轮实际运行无失败项。未执行项：一切温度积分、温升曲线/峰值、驱动预热、冷却、重复制动、ANSYS/Fluent与优化。

输入已符合原M2结构，但下一步温度计算仍须研究者单独审查和授权，并明确初温、有限冷却边界及新单次制动工况的数值验证安排。源项重采样守恒不等于热网络储能/散热守恒或时间步收敛，不能提前宣称这些检查通过。

**归档M2的13节点含有主动参与传热的shield节点和相应辐射路径，不等同于M3/M4 Case0无新增护罩。** 本轮按要求保留原M2参数，未移除该节点；后续应先决定是将其作为原M2拓扑对照，还是另行授权Case0派生拓扑，不能把两者默认为同一结构。真实热阻、接触、视角、冷却、温度标定以及空载损耗仍未知。

本轮只完成P2-A，现停止等待审查；PR #5保持草稿，M4仍PARTIAL，不合并、不创建M4-v1.0、不进入M5。
