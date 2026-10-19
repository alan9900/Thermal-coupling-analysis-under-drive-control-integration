# 单侧热源输入接口 m1-source-interface-1.0

入口：`[table, metadata] = m1_sources(c, trace, 'left'或'right', mode, overrides)`。此函数只准备数据、不写文件、不积分温度。`run_m1_sources` 在测试通过后批量保存到 `results/m1/engineering/interface/`，每个CSV必须与同名JSON一起使用。

## 模式与来源

- `strict`：当前缺少已验证内部损耗、再生与减速器分项数据，立即抛出 `m1:StrictEvidenceGap`，不会输出一条伪标定时序。未来获得真实地图后必须另行实现和审查严格路径；不能只修改模式字符串。
- `engineering`：要求完整、有限、有序的所有参数区间；缺失/null、越界、未知参数、无效单侧标识及不可实现轨迹均拒绝。输出均为S3工程分配，明确记录模式/场景、参数值、输入哈希和代码SHA。
- 原来的 `results/m1/traces/` 保留其 `winding_heat_W_left/right=NaN`；原始真实配置不变。工程CSV的 `calibrated_winding_heat_W` 同样保持NaN；实际可加载候选为独立的 `copper_engineering_W`。

## 必需列与量纲

| 列或列组 | 单位/定义 | 未来概念热网络的用途 |
|---|---|---|
| `time_s`、`vehicle_speed_m_s` | s、m/s；时间严格递增 | 时间与工况 |
| `motor_speed_rpm`、`motor_torque_Nm`、`disc_speed_rad_s` | rpm、Nm、rad/s；转矩正驱动、负再生 | 自己一侧的运动输入；盘速=轮速，电机速=9×轮速 |
| `emot_total_reference_W` | W；EPA联合图，驱动参考/再生镜像估计 | **仅用于核算，不能与分项再次一起加载** |
| `gear_total_assumed_W`、`disc_contact_W` | W；S3方向效率总损耗、盘片总接触功 | 核算总预算，同样不能重复加载 |
| `copper_engineering_W` | W；守恒归一化的绕组铜耗候选 | 绕组节点 |
| `iron_engineering_W` | W；定子铁损候选 | 定子铁心节点；不含独立验证 |
| `rotor_other_engineering_W` | W；转子与其他电机损耗合并候选 | 需未来定义合并节点/进一步拆分，不能默认全加磁钢 |
| `inverter_engineering_W` | W；独立逆变器热预算 | 默认外部热边界，不加到电机内部；若未来显式建逆变器节点，只能加载一次 |
| `gear_mesh/gear_bearing/gear_other_engineering_W` | W；齿面/轴承/油液密封等合并候选 | 各自节点或明确的合并节点 |
| `disc/pad_engineering_W` | W；两面合计的单个后盘及其配对摩擦片 | 盘与片热输入；不能再次乘盘数/面数2 |
| 每项对应 `*_lower_W` / `*_upper_W` | W；固定总预算、给定参数盒的逐时分项包络 | 不确定性诊断，不可将所有上界拼成一个物理守恒场景 |
| `current_proxy_Arms`、`*_raw_weight_W` | A RMS代理、W形状权重 | 只供审查，不能当实测电流或另加热源 |
| `motor/gear_budget_normalization` | 无量纲；零预算时NaN | 权重与总预算的偏差诊断，不是模型标定系数 |
| `drive_ratio_covered`、`regen_map_is_estimated` | 0/1 | 驱动分离数据凸包覆盖及再生估计状态 |
| `source_class_code` | 3=S3 | 分项预测的来源等级；真实R不把整体估计升级为S1 |
| `emot/gear/disc_partition_residual_W` | W | 各组分项之和减去其自身总预算 |
| `vehicle_power_residual_W` | W，原整车账本残差 | 包含前轴、左右后轴、路阻及必要外部运动学功率端口的整体复核 |

JSON包含 `schema_version`、`mode`、`side`、`case_id`、`scenario_id`、`classification`、全部实际参数、原始轨迹位置、来源登记位置与输入哈希。没有JSON或模式不明的CSV不能作为可追溯输入使用。字段后缀表示单位，不允许默认为kW。

## 守恒与不确定性

单侧必须满足 `copper+iron+rotor_other+inverter=EMOT`、`gear_mesh+gear_bearing+gear_other=gear_total`、`disc+pad=disc_contact`。电机内部热输入只合计前三项；单侧全部源热输入为上述三组分项之和。两侧相同不等于可把单侧热源再乘2；前轴不属于这个单侧热域，但整车能量账本保留前轴。

名义场景及每一个敏感性样本都严格守恒。上下界使用正权重区间的分式包络；它们是各分项独立极值的保守外包络，不是共同可达时序。未来热网络应使用同一组参数重算完整时序（调用overrides），再比较温度，不能把各上界直接相加后宣称总能守恒。参数采样使用固定种子，并保存每组参数，未赋予概率解释。

当前未覆盖EPA联合总损耗与0.96总效率本身的真实误差；未计入停用电驱拖曳、减速器空载搅油、温度反馈、反转、13000rpm以上、非650V与真实横摆动力学。`rotor_other`及`gear_other`空间分配仍需未来热网络节点明确。实际温度精度和连续能力不能从本接口推出。M2必须经研究者批准后开展。
