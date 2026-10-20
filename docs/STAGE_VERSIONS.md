# 研究阶段版本登记（正式Tag由研究者审批后创建）

规则详见 [Git阶段版本管理制度](GIT_VERSIONING_POLICY.md)。研究基准V0.4是车型配置版本，不是里程碑Tag版本。

| 阶段 | 审核状态 | Git Tag | Commit SHA | PR | 配置版本 | 测试与成果 |
|---|---|---|---|---|---|---|
| M0 参数审查 | APPROVED（参数与资料准备范围） | [M0-v1.0](https://github.com/alan9900/Thermal-coupling-analysis-under-drive-control-integration/releases/tag/M0-v1.0)，附注Tag已推送验证 | 验收main `b13f265b1ff0add1f9e8b166d2c1bfa4ac8a8d16`；Tag对象 `d50d3896b71480bc3793a82d274f862afac1f8ec` | [PR #1](https://github.com/alan9900/Thermal-coupling-analysis-under-drive-control-integration/pull/1)，MERGED | V0.4 | [关卡记录](../reports/M0_GATE_ACCEPTANCE_2026-10-19.md)；Python 3项／MATLAB既有12组检查及18组制动积分通过；批准日期2026-10-19，用户授权简验后进入M1 |
| M1 热源建模 | APPROVED（概念数值模型）；真实标定PARTIAL | [M1-v1.0](https://github.com/alan9900/Thermal-coupling-analysis-under-drive-control-integration/releases/tag/M1-v1.0)，附注Tag已推送核验 | 验收main `9d545ab39a3efcce857573af74f7e325b74a2b15`；Tag对象 `9b3c7f97c63b56b50eb7c0477a72ad03060cae39` | [PR #2](https://github.com/alan9900/Thermal-coupling-analysis-under-drive-control-integration/pull/2)，MERGED | V0.4 | [报告](../reports/M1_report.md) / [Word](../reports/M1_report.docx) / [PDF](../reports/M1_report.pdf) / [验收表](../reports/M1_ACCEPTANCE_CHECKLIST.md)；R2025a原18+新11测试组、23整车轨迹、46单侧接口及322敏感性运行通过；Python独立复核通过；严格模式拒绝、工程模式S3；M2 NOT EXECUTED |
| M2 热网络 | APPROVED（概念瞬态网络限定范围）；实物标定未完成 | M2-v1.0，附注Tag已推送核验 | 验收main `1d51c22d94577ff8f52be785300b5f6b4aadee37`；Tag对象 `4ad89c4a220174de741b4ba48706279d3b7cb2d1` | [PR #3](https://github.com/alan9900/Thermal-coupling-analysis-under-drive-control-integration/pull/3)，MERGED | V0.4 | [报告](../reports/M2_report.md) / [Word](../reports/M2_report.docx) / [PDF](../reports/M2_report.pdf) / [验收表](../reports/M2_ACCEPTANCE_CHECKLIST.md)；11组测试、4+3+18场景及Python/SciPy复核PASS；2026-10-20批准，真实几何/热阻/换热/温度未标定 |
| M3 几何设计 | IN_PROGRESS（概念几何交付，验收PENDING） | NOT CREATED | CAD生成源 `3ea9c6bd2af2cde56d17c1ce5f56ba446813477b`；基线M2-v1.0 `1d51c22d94577ff8f52be785300b5f6b4aadee37` | [PR #4](https://github.com/alan9900/Thermal-coupling-analysis-under-drive-control-integration/pull/4)，DRAFT | V0.4 | [报告](../reports/M3_report.md) / [Word](../reports/M3_report.docx) / [PDF](../reports/M3_report.pdf) / [验收表](../reports/M3_ACCEPTANCE_CHECKLIST.md)；实际CAD、56 STEP回读、283对干涉/18相位/8测试组；2187解析筛查中729拒绝；制造、寿命、实装未验证；不合并/Tag/进入M4 |
| M4 ANSYS | NOT_STARTED | NOT CREATED | — | — | V0.4 | — |
| M5 Fluent | NOT_STARTED | NOT CREATED | — | — | V0.4 | — |
| M6 优化 | NOT_STARTED | NOT CREATED | — | — | V0.4 | — |
| M7 验证 | NOT_STARTED | NOT CREATED | — | — | V0.4 | — |

正式完成时需将Git Tag、PR URL、Git commit SHA、配置版本、批准日期、测试通过/失败/未运行项目写入此表。禁止将本次增加管理制度的Git commit SHA冒充M0正式版本。

M0本次使用`stage/M0-parameter-audit`分支补齐历史成果送审。`PARTIAL`表示正式审批流程尚未完成，不表示已重新验收失败；技术完整性与未验证数据见验收摘要。原M0结果、配置及报告不被此次复核覆盖。候选版本名不代表Git Tag已经存在，尚未尝试创建正式Tag。

治理基线为`fe434fb1f846b96474a6736d77bdc20f66dc2cb7`；这不是已批准的M0阶段版本。M1–M7保持`NOT_STARTED`。后续批准后只从相应验收后的main创建下一阶段分支；修复另建版本，禁止移动或删除旧Tag。

复核脚本提交为`10f16519e332dcb32ac9c8927a5a303cbf8b54a6`。上述复核证据SHA固定指向保存日志、MAT、CSV与图的提交；本次PR链接登记在后续提交中，避免文档自引用自身提交SHA。批准后需登记实际验收main提交及不可变Tag，不将证据SHA或登记SHA自动当作正式版本。

2026-10-19送审说明补充：[工作安排图片](../reports/planning/research_work_plan_v04_2026-10-19_v1.png)及[生成提示词](../reports/planning/research_work_plan_v04_2026-10-19_v1.prompt.md)随现有M0分支提交PR #1。`v1`仅指图稿修订，不是正式阶段版本；未改变M0待验收及M1–M7未开始的状态。

## 2026-10-19当前关卡更新

用户已授权简单验收M0通过后进入M1，复核已通过。上方旧送审说明、验收摘要及工作安排图均为其生成时状态，保留追溯；当前状态以上表与[M0关卡记录](../reports/M0_GATE_ACCEPTANCE_2026-10-19.md)为准。合并后将验证Tag是否成功创建并在后续提交登记实际SHA；不把拟议Tag冒充现有Tag。

M0已于本轮合并且附注Tag实际创建成功，远端剥离Tag后的目标SHA已核对为`b13f265b1ff0add1f9e8b166d2c1bfa4ac8a8d16`。本登记属于之后的M1开发提交，**M0-v1.0固定指向实际验收合并提交**，不移动Tag以包含后来的登记文字。M1仅被授权开发，M2–M7仍未授权。

## M1 数值交付（2026-10-19）

分支 `stage/M1-heat-sources` 直接从已验收的M0 main提交创建。全部23组轨迹保存在 `results/m1/traces/`，配置快照、文本SHA-256、实际MATLAB日志、MAT结果、曲线和独立复核见 `results/m1/`；复现命令见 `scripts/m1/README.md`。数值代码SHA与输入哈希固定在 `inputs.json` 和 `independent_checks.json`。报告包含27个可编辑公式，Word经实际导出PDF并逐页检查。真实标定缺口使本阶段保持PARTIAL；M1未合并、TAG NOT CREATED，M2–M7未开展。

证据归档提交：`2514a6d337eb5300b4f807419a3e1f7b66a72cd7`，含报告Markdown/Word/PDF、23条CSV轨迹、MAT、图表、运行日志、独立复核与文档检查；本行在后续登记提交加入，避免提交SHA自引用。送审为上述PR #2，不将草稿PR视为已验收版本。

## M1 参数化与不确定性补充（2026-10-19）

用户已授权继续同一分支/PR，允许明确标识的工程替代模型，不批准合并/Tag/M2。代码提交 `d3dbf6c5839b9d228db8665e76da0c5d7549c0dd` 引入参数化分项；`2b336e62485e0183f79428dd6009ec7aa32a1ab3` 补充时序输入溯源保护及图表标识，最终实际运行采用后者。旧证据提交保留，可从历史恢复；本轮更新M1报告及结果，不改M0固定版本。

独立工程配置 `configs/m1_source_partition.yaml`，资料审查 `docs/M1_SOURCE_REVIEW.md`，未来输入合同 `docs/M1_HEAT_SOURCE_INTERFACE.md`。46对CSV/JSON、161×2参数运行、MAT/图表/日志及检查位于 `results/m1/engineering/`。范围为固定联合/传动总损耗下的守恒分配及条件区间，非实测置信区间；真实绕组数据仍NaN/null。概念数值验收条件已具备，研究者验收PENDING；M1未合并，TAG NOT CREATED，M2–M7未开展。

本轮完整证据归档SHA：`ec134044c346e10cac3f7d31e0bfc99dc641ec13`。含12页Markdown/Word/PDF报告、52个可编辑数学对象、5幅报告图、验收表、46对单侧接口、322次敏感性结果及参数矩阵、独立检查与运行日志。文档逐页视觉检查PASS；本行在后续登记提交加入，避免自引用。后续登记不改数值代码或证据内容，不表示已经批准M1。

## M1 最终验收授权

2026-10-19研究者按“具有明确来源、参数化假设和不确定性分析的概念数值热源模型”验收M1，批准合并PR #2及附注Tag归档；真实损耗标定仍PARTIAL。见reports/M1_GATE_ACCEPTANCE_2026-10-19.md。下阶段授权须以M1远端归档核验成功为前提。旧段落及计算JSON中的待审状态是历史快照，当前以本关卡为准。合并及Tag核验后的准确SHA在后续登记，Tag固定指向实际合并main提交。

## M1远端归档核验与M2启动

PR #2已合并，M1-v1.0附注Tag对象 `9b3c7f97c63b56b50eb7c0477a72ad03060cae39`，远端剥离目标已核对为实际验收main合并提交 `9d545ab39a3efcce857573af74f7e325b74a2b15`。M0-v1.0仍为 `b13f265b1ff0add1f9e8b166d2c1bfa4ac8a8d16`。本段在之后的M2分支登记，Tag固定在真实验收提交，不移动Tag以包含后续登记文字。M2分支从该最新main创建，M2合并/正式Tag/M3仍须另行批准。

## M2数值送审（2026-10-19）

运行源提交`ff818ccb35daf8d70d0cbafbf28fc6690ab457a8`；后续仅完善资料说明、图稿颜色/布局及报告。13节点、4基础场景、3路径移除、18敏感性均已实际运行MATLAB25.1/R2025a。11组测试PASS；C名义/细步峰值差0.001203K，D0.001562K；全网络最大相对能量残差5.28e-14；Python独立复核7场景及自适应RK45比较PASS，最大温差0.002916K。初次12,000s无源测试未达0.1K要求，日志保留；延长至24,000s后通过，未放宽阈值。

成果位置`results/m2/`，代码`scripts/m2/`，配置`configs/m2_thermal_network.yaml`，来源审查`docs/M2_SOURCE_REVIEW.md`。限S3概念预测；M1真实损耗仍PARTIAL，实际热阻/冷却/几何未知，空载拖曳、零功率搅油及温度反馈尚未建模。完整证据SHA在后续登记提交追加，避免自引用。本次没有M2验收授权，PR保持草稿、正式Tag NOT CREATED；M3/CAD/ANSYS/Fluent未开展。

### 2026-10-20中断恢复及完整证据登记

完整证据提交为`d19bae2f3691ee2501c1659beb8135a2e004ee9d`，包含7场景CSV/JSON、18敏感性MAT结果、原始源项、PNG/SVG、实际日志、独立检查及9页Word/PDF（18个可编辑数学对象、6幅报告图、逐页视觉检查PASS）。报告/资料/图稿布局准备提交为`229939cb588a8cb52c6c43b62b28ae9255799cc9`；数值方程/配置实际运行源仍为`ff818ccb35daf8d70d0cbafbf28fc6690ab457a8`，未因恢复归档而改写模型或重称新数值运行。

恢复后实际重跑Python独立复核PASS；7场景最大能量相对残差1.4539e-13，与SciPy温度差0.002916K；归档完整性检查PASS，记录于`results/m2/delivery_checks.json`。56个新增证据文件按有限结果归档方案保存，最大MAT约13MB；源码、原始未知量及M0/M1固定文件未改。当前PR #3仍待研究者批准；M2未合并、无正式Tag，M3未开始。本行在证据提交后的登记提交加入，不将证据SHA误称已验收main版本。

## M2正式验收授权（2026-10-20）

研究者已按“具有明确工程假设、通过能量守恒及数值验证的概念瞬态热网络模型”批准M2、PR #3合并和M2-v1.0附注Tag。真实几何、热阻、换热及温度标定仍未完成，见reports/M2_GATE_ACCEPTANCE_2026-10-20.md。本轮独立复核再次PASS；报告仅更新批准口径，数值方程和候选参数未改。只有远端Tag实际核验成功后才开展M3，实际合并SHA/Tag对象在后续登记，不覆盖M0/M1。本段之前PENDING描述与运行JSON是历史快照。

## M2远端归档核验及M3启动

实际合并提交`1d51c22d94577ff8f52be785300b5f6b4aadee37`，远端M2-v1.0附注Tag对象`4ad89c4a220174de741b4ba48706279d3b7cb2d1`，剥离目标与合并提交一致。M0/M1原Tag对象及目标不变。M3分支stage/M3-geometry从该最新main创建；本登记属于后续M3提交，不移动M2 Tag以包含后续登记。M3只做几何与热参数候选，禁止提前运行M4 ANSYS/Fluent或声称降温效果。

## M3概念几何送审（2026-10-20）

实际CadQuery2.8.0/OpenCascade7.9.3.1生成源`3ea9c6bd2af2cde56d17c1ce5f56ba446813477b`；4装配32/36/40/36命名部件与连通空气域、共同零件及新增结构共56 STEP，有限总量约78MB。有效Brep及回读体积误差约1e-13；283对无>0.001mm³交叠；8组回归/18齿轮相位PASS；2187解析组合中729拒绝，25mm紧凑包络实际触发干涉。原始失败/修复日志保留。

报告9页、21个可编辑数学对象、5幅图，Word导出PDF并逐页检查PASS；M2固定文件无差异。热阻/热容/视角仅新候选，未重算M2温度、不声称降温。45mm轴余量小，40mm拒绝；轴向定位、花键、壳体分型、轴承寿命/密封、预紧/防滑、车辆包络和真实冷却仍缺。M3等待研究者验收，不合并、不创建正式Tag、不开展M4。完整证据SHA后续登记，避免自引用。

M3完整证据提交：`0dc265e7329870c92e849abe89fb9c2d12378c77`，已推送；包括56 STEP、144行质量/C、283对干涉、2187解析范围、CSV/JSON/图和三格式报告。独立交付检查PASS，另逐一读取该提交的110个源/成果Git blob核对保存的SHA-256，全部一致，STEP原始字节未被Git换行转换。后续登记不改CAD几何，不把该证据SHA冒充main或正式M3版本。最终批准状态PENDING；PR #4保持草稿。

## M3几何正确性复核与有限元前精化（2026-10-20）

继续`stage/M3-geometry`及[PR #4](https://github.com/alan9900/Thermal-coupling-analysis-under-drive-control-integration/pull/4)。状态**PARTIAL_WITH_BLOCKED_ITEMS**，不是M3正式验收；Tag **NOT CREATED**，M4/ANSYS/Fluent **NOT EXECUTED**。原`cad/m3`、`scripts/m3`、`results/m3`和原M3报告均保留，M2-v1.0固定文件不变。

最终几何生成由提交`700edf045c03ea63ed27e197e2020048ceb98995`启动；后续断言/参数元数据和审查文档更新未改变几何，当前源对所有Case0部件体积回归通过。旧生成器在写结果时取HEAD的问题已用独立launch/result-write字段纠正，未伪称重新运行CAD。提交`c4aace5`补充罩支点差动热膨胀BLOCKED及未来导入清单；本轮完整证据SHA在之后登记，避免自引用。

交付`cad/m3_review`：10份完整/热装配（4方案50mm及Case0的45mm对照）、5份局部连通空气域及共同零件，共144 STEP约152.5MB；全对筛选后3686对精确布尔无>0.001mm³交叠，最大回读误差2.28e-13；16组审查、18啮合相位、24盘/钳旋转配对通过。测试通过表示审查正确，不把失败工况当通过。50mm驱动Kt2约162.34MPa，45mm约222.74MPa（180MPa阈值为S3）；0.6g/0.8g零再生单盘752.839/911.057N·m。

补充报告`reports/M3_geometry_review.md/.docx/.pdf`：9页、8个可编辑OMML公式、7幅真实CAD/工程图，Pandoc转换与Word导出后逐页视觉检查PASS。配置/接口`configs/m3_geometry_review.yaml`、`configs/M3_to_M4_mapping.json`；结果和测试`results/m3_review`；补充验收表`reports/M3_GEOMETRY_REVIEW_CHECKLIST.md`；未来几何准备清单`docs/M4_GEOMETRY_IMPORT_PREPARATION.md`。

轴承装入问题改为可拆套候选，但传扭/热松脱、预紧防滑、局部凸台/疲劳/位移、端部绝缘、滚动接触与油膜、冷却端口和装车包络仍BLOCKED。罩300K/箱100K差动膨胀约0.406mm超过0.2mm孔隙，需滑移/柔性支点复审。允许作为ANSYS导入候选，不等于可直接做可信样机温度或优化结论。原始未知值保持null，未修改旧Tag、合并M3或进入M4。

本轮完整精化证据提交：`40c95c1a1eb9de5584e899df70ec887cce9488a6`，已推送并核对远端分支。其交付清单222个文件逐一读取实际Git blob核对SHA256全部通过，含144 STEP与三格式报告，见`results/m3_review/git_blob_checks.json`。后续只追加核验记录、登记及针对CR行尾的Git检查属性，不重写证据提交。远端main仍为M2合并`1d51c22d94577ff8f52be785300b5f6b4aadee37`；M0/M1/M2原附注Tag对象及剥离目标不变，M3-v1.0不存在。PR #4待复核，BLOCKED条件继续有效。

### 用户提出输出大齿轮疑似干涉后的复核

2026-10-20实际在本机SolidWorks2023打开Case0_d50_full并完成装配干涉检测，129叶零件、未忽略隐藏体，结果0。OCCT原齿轮对前/后壳体交集均0，最短距离18.646322/10mm；半径93mm完整360°扫掠包络亦无干涉，齿顶至内底壁径向留11mm；26个旋转/箱体配对通过。只调整观察显示，未修改CAD尺寸或零件位置。

见`reports/M3_OUTPUT_GEAR_CLEARANCE_RECHECK.md`及`results/m3_review/output_gear_clearance/`，带尺寸真实截面和独立运行脚本已归档。旧报告中SolidWorks未执行属历史交付快照；此次后续确已执行，不改写历史报告。其余机械/热边界BLOCKED继续有效，M3未合并/无正式Tag，M4未开展。

专项复核完整证据提交`4e02ef6b544d6c336ca12e6623d5a46b98b93b05`已推送至同一开发分支/PR #4，含原STEP哈希、旋转/扫掠布尔与距离、实际SolidWorks导入位置/检测记录和显示截图。此处后续追加准确证据SHA，不移动旧Tag或修改归档模型。
