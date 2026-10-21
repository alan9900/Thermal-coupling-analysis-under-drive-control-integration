# 单侧V0.4概念CAD交付

可编辑参数历史在仓库`configs/m3_geometry.yaml`与`scripts/m3/cad_model.py`；运行与适用范围见`scripts/m3/README.md`。这两个文件是源模型，不以STEP冒充参数历史。

- Case0_assembly.step：真正没有新增隔热罩和导流结构的基准。
- CaseA_assembly.step：单层带支柱隔热罩。
- CaseB_assembly.step：双层罩及10mm候选空气间隙。
- CaseC_assembly.step：罩与20°候选斜向开口通道一体化。
- base_parts：四方案共用部件；CaseA/B/C子目录保存新增结构的单件。
- *_air_domain.step：最大连通局部外部空气域；盲孔密闭间隙气穴单列于几何检查，不加入外部流场。

单位mm；实际执行CadQuery2.8.0/OpenCascade7.9.3.1，STEP已回读。它是S3概念模型，不是Toyota/Brembo原厂CAD，也不是可制造发布。轴承为包络、绕组为分段等效体、齿根无圆角、壳体未完成分型/紧固/公差/密封，水套未完成端口。目录符合性不能转移到本改制安装。

名义无正体积干涉不代表真实温度、结构强度、装车或加工可行性已验证；M4需先复核拓扑、接触、材料和边界，当前未运行ANSYS/Fluent。
