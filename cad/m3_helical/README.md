# M3 两级斜齿概念修订

独立于 `cad/m3` 和 `cad/m3_review` 的新版本；旧直齿模型不覆盖。

- `Case0_d50_helical_full.step`：真实无新增隔热罩完整装配。
- `CaseA_d50_helical_full.step`：单层罩。
- `CaseB_d50_helical_full.step`：双层罩/空气间隙。
- `CaseC_d50_helical_full.step`：隔热导流通道。
- 对应 `_thermal.step`：独立热分析候选；等体积平滑大齿轮，一体斜齿小齿轮仍保留。
- `parts/`：改变的输入轴、中间轴、大齿轮及油库存两版STEP。其余部件已包含在每份装配。

单位mm。可编辑参数化源：`scripts/m3_helical/helical_cad.py`、`configs/m3_helical.yaml`，复用未修改的旧CAD基础代码。
实参null、接触/冷却/轴向承载未知，几何候选不等于机械/求解发布。ANSYS/Fluent NOT EXECUTED。
两级20/60、9.0、原轴心、50mm输出轴；固定端面模数2.5/3.0mm，20°螺旋角，非标准法向模数。不得称为标准法向模数产品或制造级齿轮。
几何/STEP核验与完整报告见`results/m3_helical`及`reports/M3_helical_revision.md`。
