# M4 原生工程清理与核心结果保留（2026-10-23）

研究者明确要求先保存现有核心结果，再删除占用空间的ANSYS仿真模型。已完成归档、逐文件回读校验和实际删除；本次仅为存储维护，没有新求解、热源修改或零再生计算。M4仍为PARTIAL，草稿PR #5不合并、不打正式Tag、不进入M5。

## 核心资料入口

| 资料 | 保留位置与内容 |
|---|---|
| 云图逐图讲解 | [Word](../reports/M4_contour_explained.docx)、[PDF](../reports/M4_contour_explained.pdf)、[Markdown](../reports/M4_contour_explained.md)：30页，29幅真实ANSYS导出图及解释 |
| 云图原图 | [contour_captures](../results/m4/contour_captures/)：整体1幅、部件28幅，保留各自时刻、色标和SHA256 |
| 阶段结果与限制 | [M4报告Word](../reports/M4_report.docx)、[PDF](../reports/M4_report.pdf)、[验收表](../reports/M4_ACCEPTANCE_CHECKLIST.md) |
| 数值数据 | [studies](../results/m4/studies/)：各部件最高/最低/热容均温时序、热源、能量收支、热流路径和部分FE场数据 |
| 本次提取的峰值索引 | [core_peak_temperatures.csv](../results/m4/storage_cleanup_20261023/core_peak_temperatures.csv)：从已有CSV提取，未重算模型；含场景、28个区域、峰值及峰值时刻 |
| 可复算输入 | [model_input](../results/m4/model_input/)：4个精确执行输入压缩包；保留[复算准备脚本](../scripts/m4/prepare_reproduction.py)和现有模型源代码 |
| 删除及核验凭证 | [归档核验](../results/m4/storage_cleanup_20261023/archive_verification.json)、[删除清单](../results/m4/storage_cleanup_20261023/native_deletion_inventory.json)、[删除回执](../results/m4/storage_cleanup_20261023/deletion_receipt.json)、[最终检查](../results/m4/storage_cleanup_20261023/post_cleanup_checks.json) |

独立本地归档：`E:\ansys_runs_archives\M4_core_results_20261023.zip`。

- ZIP大小391,664,998字节，约373.52 MiB；1934个成员的SHA256及大小回读核对通过。
- ZIP SHA256：`444e0f781eb2b5f8fd13935e6b254f4923e65ec905b233390d8eb43acffbf067`。
- 内含清理前Git工作区文件快照，以及532份本地日志、截图、宏、参考文档等补充证据。不是Git历史备份；Git历史和标签仍留在原仓库及GitHub。
- ZIP内的`ARCHIVE_MEMBERS_SHA256.json`提供逐成员核验；同目录`.sha256`及`.cleanup_receipt.json`提供整体校验和清理回执。归档为清理前快照，最终清理记录另保存在仓库。
- ZIP保存在本地，未声称上传GitHub。原有受控小结果、报告、代码和精确输入包仍在Git；清理记录随当前M4分支提交。

## 实际删除范围及空间

仅删除以下五个项目目录，执行前逐个核对绝对路径、文件清单和归档哈希，确认没有活动ANSYS求解/模型进程及目录链接：

- `E:\ansys_runs\m4_case0_20261021`
- `E:\ansys_runs\m4_viewer_20261022`
- `E:\ansys_runs\M4_Case0_reproduction_prepared_20261021`
- `E:\ansys_runs\M4_D_reproduction_prepared_20261021`
- `E:\ansys_runs\m4_native_benchmark`

共删除1028个文件，文件逻辑大小167,796,230,090字节，约156.27 GiB。E盘空闲从29,462,589,440字节增加至143,358,042,112字节，实测增加113,895,452,672字节，约106.07 GiB。原文件存在压缩、链接及其他磁盘活动，逻辑大小与空闲增量不能直接等同。本次释放的是磁盘存储；检查时没有运行中的ANSYS求解应用，未声称释放同等容量的运行内存。

已删除大型Workbench项目及配套Mechanical数据库、RTH完整瞬态结果、视角系数缓存、求解矩阵和临时工程；保留软件安装、许可证服务、Python/CAD环境、无关旧项目及仓库内全部既有受控文件。仓库内小型辐射单元测试结果继续作为测试证据保留。M0—M3标签及原始CAD未修改。

## 结果解释与恢复限制

现有结果仍是原30 kW整车再生上限条件下的历史S3概念预测，不能视为零再生结果或样机温度标定。截图中的整体同步场与各零件自身峰值时刻不同，使用各自色标；不能直接将图册不同页当成同一时刻。

C/D完整时窗整体热能收支最大相对残差约0.001957%/0.000507%，仍保留原数值验证的适用范围；三档时间步闭合、完整接触/冷却敏感性和内部热源全面空间误差验证未完成，不因本次归档变成PASS。

**原生完整三维场和Workbench数据库已删除且未包含在ZIP内，无法再直接打开任意时刻的完整云图或恢复原Workbench界面。** 已有29张图、部件时序和选定场子集可直接查阅；如需完整交互后处理，须使用保留输入重新建库/求解。精确输入包不等于完整Workbench工程；去除外部视角缓存依赖的准备脚本仍需ANSYS许可证、资源和重新核验，不能保证已有未完成验证自动通过。

后续仿真继续暂停，零再生研究计划见[NO_REGEN_WORK_PLAN.md](NO_REGEN_WORK_PLAN.md)。本次清理授权不构成恢复研究或求解授权。
