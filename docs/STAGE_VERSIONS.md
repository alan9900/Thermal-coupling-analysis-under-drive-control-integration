# 研究阶段版本登记（正式Tag由研究者审批后创建）

规则详见 [Git阶段版本管理制度](GIT_VERSIONING_POLICY.md)。研究基准V0.4是车型配置版本，不是里程碑Tag版本。

| 阶段 | 审核状态 | Git Tag | Commit SHA | PR | 配置版本 | 测试与成果 |
|---|---|---|---|---|---|---|
| M0 参数审查 | APPROVED（参数与资料准备范围） | NOT CREATED；批准后拟创建M0-v1.0 | 原成果 `2ba858b8a047566f5932a621175d360154f869e8`；复核证据 `a08c46cdf5a36d649cd03e1d895c7da0e438a382` | [PR #1](https://github.com/alan9900/Thermal-coupling-analysis-under-drive-control-integration/pull/1)，授权复核后合并，待执行 | V0.4 | [关卡记录](../reports/M0_GATE_ACCEPTANCE_2026-10-19.md)；Python 3项／MATLAB既有12组检查及18组制动积分通过；批准依据：2026-10-19用户本轮条件授权，简验通过 |
| M1 热源建模 | NOT_STARTED | NOT CREATED | — | — | V0.4 | — |
| M2 热网络 | NOT_STARTED | NOT CREATED | — | — | V0.4 | — |
| M3 几何设计 | NOT_STARTED | NOT CREATED | — | — | V0.4 | — |
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
