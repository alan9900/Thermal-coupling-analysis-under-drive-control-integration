# M3 独立几何复核交付

原始概念在`cad/m3/`，未覆盖。本目录为新修订的机械/热分析候选；所有新增结构均S3工程假设，非OEM CAD或制造发布。

- `Case{0,A,B,C}_d50_full.step`：四方案完整装配。
- `Case{0,A,B,C}_d50_thermal.step`：独立热分析版本，保留热路和材料区。
- `Case0_d45_full/thermal.step`：45mm失败方向对照，不作为冻结设计。
- `*_full_air.step`：五份单连通局部外部空气域，不是已经验证的Fluent旋转/远场域。
- `revised_parts/`：50mm Case0所有独立命名STEP零件；四方案基础相同，罩及支点在各装配内。

单位mm。Python/YAML是可编辑参数化源，STEP不含建模历史。数量以`results/m3_review/step_manifest.json`为准；总量有限约160MB，每文件<100MB。保存完整/热装配和公共零件一份，不提交CAD内核、venv或网格缓存。所有STEP设为Git binary以保原始字节。

模型具有轴承装入候选路径，未完成工具可达性、配合、预紧、疲劳及实际装车验证。可拆套需验证压力/摩擦/热松脱；运行片隙不是粘结面；端绕组绝缘仍BLOCKED。压盖、夹紧环、销/键、密封均为等效候选，不能按目录件认证。

OCCT回读/干涉已实际执行；ANSYS、Fluent、SolidWorks均NOT EXECUTED。允许作后续导入/分区准备，不表示可直接得到可信温度。当前仍M3，未经批准不进入M4。
