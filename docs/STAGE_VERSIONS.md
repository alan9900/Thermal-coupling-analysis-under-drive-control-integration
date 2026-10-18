# 研究阶段版本登记（正式Tag由研究者审批后创建）

规则详见 [Git阶段版本管理制度](GIT_VERSIONING_POLICY.md)。研究基准V0.4是车型配置版本，不是里程碑Tag版本。

| 阶段 | 审核状态 | Git Tag | Commit SHA | PR | 配置版本 | 测试与成果 |
|---|---|---|---|---|---|---|
| M0 参数审查 | PARTIAL（技术交付及复核齐备，正式验收待批准） | NOT CREATED；候选名M0-v1.0 | 原成果 `2ba858b8a047566f5932a621175d360154f869e8`；复核代码 `10f16519e332dcb32ac9c8927a5a303cbf8b54a6` | 验收PR创建后登记 | V0.4 | [验收摘要](../reports/M0_ACCEPTANCE_SUMMARY.md)；[原报告](../reports/M0_report.md)；[复核结果](../results/m0_acceptance/acceptance_checks.json)：Python 3项／MATLAB 12组通过，18组制动积分；批准日期：尚未批准 |
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
