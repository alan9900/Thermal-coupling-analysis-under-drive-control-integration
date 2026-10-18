# Git 研究阶段版本管理制度 V1.0

本制度自添加之日起对 Codex 的 **M0–M7 所有后续工作**生效。对应当前研究架构：`configs/baseline_vehicle.yaml` V0.4，后驱双独立电机，单侧电机—减速器—内移制动器热耦合。**Git 阶段版本**（如 `M1-v1.0`）和**车型配置版本**（如 `v0.4`）是不同概念，禁止混淆。

## 1. 基本原则
- `main` 只存放**已经审查并正式验收**的阶段成果；日常开发使用独立分支。
- 每个阶段（M0、M1、…、M7）必须有一条**独立开发分支**、至少一个 commit、阶段报告、测试证据及一份 Pull Request (PR)。
- **经研究者明确批准 PR 合并后**，从已经合并的 `main` 提交创建**不可重用、不可挪动**的阶段 Git Tag。Tag 是已批准成果的稳定快照，不是每天开发中的临时状态。
- 未通过验收、不具备实际软件环境或缺少关键参数，标记 `INCOMPLETE` 或 `BLOCKED`；允许有开发提交及 PR 草稿，**不能创建表示已完成的正式阶段标签**。
- 为保证可回退：**不执行** `git push --force`、重写 `main` 历史、删除/重设旧阶段 Tag、`git reset --hard` 作为团队回退方式，除非研究者另行明确授权。
- 所有研究成果要可追溯：每个阶段报告记录所用配置版本、输入来源、软件版本、commit SHA、PR 链接、测试状态、成果文件路径、结果是否实测/仿真/合成。

## 2. 命名
| 阶段 | 开发分支例子 | 阶段完整验收的Git Tag |
|---|---|---|
| M0 参数审查 | `stage/M0-parameter-audit` | `M0-v1.0` |
| M1 多热源 | `stage/M1-heat-sources` | `M1-v1.0` |
| M2 热网络 | `stage/M2-thermal-network` | `M2-v1.0` |
| M3 结构设计 | `stage/M3-geometry` | `M3-v1.0` |
| M4 ANSYS | `stage/M4-ansys` | `M4-v1.0` |
| M5 Fluent | `stage/M5-fluent` | `M5-v1.0` |
| M6 参数优化 | `stage/M6-optimization` | `M6-v1.0` |
| M7 总结验证 | `stage/M7-validation` | `M7-v1.0` |

纠错后若对阶段结论有实质改动，采用新的修复分支和 `M1-v1.1` 等版本；禁止挪动旧 `M1-v1.0` 标签。一次性紧急修复沿用 `fix/M1-issue-short-description` 分支；正式合并后再建新标签。

## 3. 标准操作流程（有本地Git CLI、GitHub远程写权限时）
1. 先同步并确认基础：`git fetch origin --prune`、`git switch main`、`git pull --ff-only origin main`；记录当前基线 SHA。若与用户或其他 Codex 的未合并工作冲突，**停止询问，不覆盖他人更改**。
2. `git switch -c stage/M1-heat-sources`（举例：只在 M0 完成并已获批准进入 M1 后）。
3. 每完成一个独立可运行子任务就 commit，并附清晰信息，例如 `feat(m1): add rear brake power model`、`test(m1): verify total energy balance`、`docs(m1): summarize assumptions and parameter gaps`。
4. 运行可运行的测试。若 MATLAB/ANSYS/Fluent 未执行，应明确说明 `NOT EXECUTED`，禁止把创建脚本等同于完成计算。
5. 在 `reports/M1_report.md` 提供：结论、输入来源、配置/软件版本、测试通过/失败/跳过明细、误差、开放问题、原始数据/图表地址、commit SHA及变更清单。若结果不完整，报告状态必须为 `BLOCKED` 或 `PARTIAL`。
6. 提交分支：`git push -u origin stage/M1-heat-sources`；创建 PR 指向 `main`，给出检查清单、证据和结果差异。**在用户批准前不自行合并、不开始下一阶段**。
7. 研究者审阅并批准后，合并 PR 到 `main`。取回 `main` 最新 commit SHA；创建附注 Tag `git tag -a M1-v1.0 -m "M1 heat sources approved; baseline V0.4"`；`git push origin M1-v1.0`。如果用户期望直接通过 PR 合并，也可由用户完成合并，Codex再按批准指令生成Tag。
8. 将 `M1-v1.0`、Tag 对应的 commit SHA、PR URL 和阶段报告位置写进 `docs/STAGE_VERSIONS.md`。如果需要更新版本登记，优先在合并/打Tag之前完成该登记记录；如果打Tag后有新的登记提交，注明 **Tag 指向实际验收提交**。避免通过额外 commit 造成“Tag 未包含当时版本登记”的混乱。

**注意 M0 可能已经存在主分支工作**：首先检查 main 历史和 `reports/M0_report.md`、实际测试证据、既有 PR/Tag。**不得自动把既有 M0 提交认定为验收通过，不得无审核补打 `M0-v1.0`**；由用户明确批准后可以为已验收的历史提交打标签。其他阶段严格从流程开始。

## 4. 合并审批要求
PR 标题：`[M1] Rear axle heat-source model — review requested`。正文至少包含：
- [ ] 范围符合当前后驱 V0.4 架构，未使用废弃前驱配置
- [ ] 配置、来源、单位、数据许可及假设有记录
- [ ] 关键物理校验和软件测试可复现，失败项已列明
- [ ] 各结果/图表明确标注数值或合成演示性质
- [ ] 原始数据、报告及图表可以从 Git 中找到，超大文件另附校验和与稳定存储位置
- [ ] 研究者已审核；获批后才合并并打正式 Tag

不可仅因“代码能运行”就通过：制动和能量守恒测试、上下游接口兼容、前后轴分配和单侧功率标定均应按阶段验收标准检查。

## 5. 文件与大小
- 可版本化：`.m`、`.py`、配置 YAML、有限大小的 CSV、源图（`.svg`/绘图脚本）、图片、模型输入、自动化日志和报告。
- 大量瞬态场、ANSYS工程/结果、Fluent `.cas/.dat`、大容量`.mat`或版权受限数据包不得无计划直接塞进Git历史。优先提交可复算的脚本/设置、关键小结果、元数据/来源/校验和。经研究者同意后使用 Git LFS、外部受控归档或 GitHub Release assets，明确其**独立于常规Git回退**的存储和保留方式。
- 切勿提交软件许可证、密钥、个人凭据；大文件和中间缓存使用 `.gitignore`。

## 6. 安全回退、查看与修正
- 查看所有快照：`git tag --list 'M*-v*'`。
- **只读查看旧版**：`git switch --detach M1-v1.0`；看完用 `git switch main` 返回。
- 从旧版创建调查分支：`git switch -c inspect/from-M1-v1.0 M1-v1.0`。此操作不改变主分支。
- 修复错误：从当前 `main` 建 `fix/M1-bug-name`，针对问题做补丁、测试、PR，合并后生成 `M1-v1.1`。**不要直接对公开共享 main 执行回退硬重置**；若确有需要恢复原状态，使用 `git revert` 形成新的可审计提交并通过 PR。
- 当前阶段尚未通过时，以未通过 PR/分支继续修正，不提前宣告 `M1-v1.0` 已完成。

## 7. 版本登记规范
`docs/STAGE_VERSIONS.md`（可先只列暂无正式版本，待验收时逐条更新）。列字段：阶段、状态（NOT_STARTED/IN_PROGRESS/PARTIAL/BLOCKED/APPROVED）、Tag、commit SHA、PR、研究基准配置版本、主要产物、测试状态、批准日期。任何 TAG 创建失败需要明确报告 **TAG NOT CREATED**，不可声称已归档完成。

## 8. 无 git push / tag 权限的备选
若 Codex 的环境只有 GitHub API 或无法创建 Git Tag：依然提交功能分支和 PR/commit，向用户报告无法推送 Tag，提供准确的 commit SHA 和 GitHub PR 链接；**不能仅写“已生成tag”**。请用户用 GitHub 网页 Releases/Tags 或本地git根据已批准 SHA 创建Tag，完成之后再更新登记。
