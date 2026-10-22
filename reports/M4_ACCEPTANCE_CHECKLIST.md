# M4 Case0阶段验收检查表

**当前状态：PARTIAL；研究者尚未验收。**

本表依据实际完成回执生成。PASS只对应列明的概念数值检查；真实标定、机械认证和全部工况适用性不包含在内。

| 项目 | 状态 | 证据 |
|---|---|---|
| 配置、未知值、M1接口与来源边界 | PASS | results/m4/input_tests.json |
| 三套原生网格默认形状检查 | PASS_WITH_WARNINGS | results/m4/meshes/native_shape_checks.json |
| 实际原生热容/后向欧拉对流基准 | PASS | results/m4/native_benchmark_checks.json |
| 实际原生辐射K偏置、方向及W单位 | PASS | results/m4/native_radiation_checks.json |
| 原生材料常数与28个RTH材料区核对 | PASS | results/m4/native_material_region_checks.json |
| A真实原生瞬态求解及预期时刻 | PENDING | results/m4/studies/A_normal12_rd95_dt1_retry1/native_archive_manifest.json |
| A总体储热/散热/冷却/辐射收支 | PENDING | results/m4/studies/A_normal12_rd95_dt1_retry1/pilot_FE_energy_checks.json |
| B真实原生瞬态求解及预期时刻 | PENDING | results/m4/studies/B_normal12_rd95h_dt4_retry1/native_archive_manifest.json |
| B总体储热/散热/冷却/辐射收支 | PENDING | results/m4/studies/B_normal12_rd95h_dt4_retry1/pilot_FE_energy_checks.json |
| C真实原生瞬态求解及预期时刻 | PASS | results/m4/studies/C_normal12_rd95_dt1/native_archive_manifest.json |
| C总体储热/散热/冷却/辐射收支 | PASS | results/m4/studies/C_normal12_rd95_dt1/pilot_FE_energy_checks.json |
| D真实原生瞬态求解及预期时刻 | PASS | results/m4/studies/D_normal12_rd95_dt1/native_archive_manifest.json |
| D总体储热/散热/冷却/辐射收支 | PASS | results/m4/studies/D_normal12_rd95_dt1/pilot_FE_energy_checks.json |
| 数值细化 mesh | PASS | results/m4/convergence_checks.json |
| 数值细化 time | PENDING | results/m4/convergence_checks.json |
| 数值细化 radiation_facets_fine | PASS | results/m4/convergence_checks.json |
| 数值细化 radiation_facets_medium | PASS | results/m4/convergence_checks.json |
| 数值细化 radiation_facets_combined | PASS | results/m4/convergence_checks.json |
| 相同输入的安装接触/冷却范围计算 | PENDING | results/m4/sensitivity_checks.json |
| 32对连接覆盖/油液/电驱子控制体 B_normal12_rd95h_dt4_retry1 | PENDING | results/m4/studies/B_normal12_rd95h_dt4_retry1/heat_path_checks.json |
| 32对连接覆盖/油液/电驱子控制体 C_normal12_rd95_dt1 | PASS | results/m4/studies/C_normal12_rd95_dt1/heat_path_checks.json |
| 32对连接覆盖/油液/电驱子控制体 D_normal12_rd95_dt1 | PASS | results/m4/studies/D_normal12_rd95_dt1/heat_path_checks.json |
| 相同网格时序的C-A制动附加响应 | PENDING | results/m4/source_mask_comparison_checks.json |
| M2热容与首次制动比较 | PASS | results/m4/M2_M4_first_brake_comparison.csv |
| 四个生产候选原生输入压缩包与校验和 | PENDING | results/m4/model_input/native_input_packages.json |
| MD/Word/PDF、可编辑公式与逐页视觉检查 | PENDING | results/m4/document_checks.json |
| M0–M3固定研究模型及结果未覆盖 | PASS | git diff M3-v1.0 -- archived source/CAD/results |

## 保留限制

- 所有温度均为S3概念预测；实际温度标定仍BLOCKED，不属于本轮数值通过的内容。
- 真实材料牌号、绕组复合/铁心方向性、温变、热接触、油膜及实际冷却未知。
- 只含部分辐射面与开口环境；未求解制动热空气回流，不能排序真实总成全部传热路径。
- 固定90/10盘片热量分配，无移动摩擦接触/闪温；约400°C摩擦片预测不代表测量或安全认证。
- 首周期/预热窗口不是六周期耐久峰值；高负载预热是给定热负荷。
- 空间细化主要覆盖盘面/片厚，时间细化只覆盖B制动及冷却；内部热源工况的全部空间与D预热阶段时间误差未独立证明。
- 电机内部损耗真实标定PARTIAL；斜齿损耗、空载拖曳、搅油与温度反馈未重新标定。
- 未经研究者批准不合并M4、不创建M4-v1.0、不进入M5。

生成时间：2026-10-22T14:03:06+08:00；证据基于 099e84a57b63c6bca9750206e0b47a5daa8e93b8 及本轮未提交更新。完整检查解释见 results/m4/acceptance_checks.json。
