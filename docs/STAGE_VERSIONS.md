# 研究阶段版本登记（正式Tag由研究者审批后创建）

规则详见 [Git阶段版本管理制度](GIT_VERSIONING_POLICY.md)。研究基准V0.4是车型配置版本，不是里程碑Tag版本。

| 阶段 | 审核状态 | Git Tag | Commit SHA | PR | 配置版本 | 测试与成果 |
|---|---|---|---|---|---|---|
| M0 参数审查 | PENDING_REVIEW（仓库已有M0相关成果，尚未确认获批） | NOT CREATED | 待核实 | 待核实 | V0.4 | 参见reports/M0_report.md，审阅后确认是否允许补建标签 |
| M1 热源建模 | NOT_STARTED | NOT CREATED | — | — | V0.4 | — |
| M2 热网络 | NOT_STARTED | NOT CREATED | — | — | V0.4 | — |
| M3 几何设计 | NOT_STARTED | NOT CREATED | — | — | V0.4 | — |
| M4 ANSYS | NOT_STARTED | NOT CREATED | — | — | V0.4 | — |
| M5 Fluent | NOT_STARTED | NOT CREATED | — | — | V0.4 | — |
| M6 优化 | NOT_STARTED | NOT CREATED | — | — | V0.4 | — |
| M7 验证 | NOT_STARTED | NOT CREATED | — | — | V0.4 | — |

正式完成时需将Git Tag、PR URL、Git commit SHA、配置版本、批准日期、测试通过/失败/未运行项目写入此表。禁止将本次增加管理制度的Git commit SHA冒充M0正式版本。
