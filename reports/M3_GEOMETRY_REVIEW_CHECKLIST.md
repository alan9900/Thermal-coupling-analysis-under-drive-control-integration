# M3 几何复核补充验收表

状态：PARTIAL / 待研究者复核。PR #4沿用，M3-v1.0未创建，M4未开展。

| 验收项目 | 状态 | 证据/限制 |
|---|---|---|
| V0.4单侧拓扑、完整传动与制动反力路径 | PASS_CONCEPT | M3_geometry_review第3节；无差速器 |
| 45/50mm轴及关联孔、轴承、毂/密封 | PASS_REVIEW | 两套CAD和shaft_screening.csv；45mm保留BLOCKED方向 |
| 轴肩、双键、挡圈、夹紧环、支承/密封位置 | PASS_GEOMETRY / PARTIAL_MECHANICS | 等效零件已建；标准槽/力/配合/寿命未验证 |
| 后轴承装入路径 | PASS_ENVELOPE | 可拆外端套修复一体座阻挡；无完整工具/公差试装 |
| 连接套传扭、热态松脱 | BLOCKED | removable_sleeve_scan.csv，不冻结过盈或h |
| 280mm盘/帽/毂/5螺栓/片/钳 | PASS_GEOMETRY | 新80mm盘帽定位孔为S3，非原Brembo产品 |
| 0.6g/0.8g零再生载荷 | PASS_SCREEN_ONLY | rear动态载荷；约752.84/911.06N·m |
| 卡钳M12杆部初筛 | PASS_SCREEN_ONLY | 0.8g约71.70MPa，阈值是假设 |
| 预紧防滑/接缝张开/局部凸台/疲劳 | BLOCKED | 低μ/低预紧组合滑移；实际结构求解未执行 |
| 盘膨胀/浮动量预算 | CONDITIONAL / BLOCKED_FAILURES | 温升与跳动扫描，非实际热变形验证 |
| 片隙与液压/支架位移 | BLOCKED | 0.5mm名义隙；实际闭合/锥变形未知 |
| 完整与独立热版STEP，四方案同基础 | PASS_GEOMETRY | geometry_checks.json，全体积/回读/干涉 |
| 空气域及CaseC入口-出口连通 | PASS_LOCAL_GEOMETRY | 同一流体体+8探针；远场/流动未知 |
| 安装支柱与压盖冲突修复 | PASS_GEOMETRY | 30→60°支点，匹配孔/杆，原失败日志保留 |
| 质量/C/体R/接触面积与M2比较 | PASS_CANDIDATES | CSV及映射，不覆盖M2；轴承有效C仍null |
| 端绕组绝缘/轴承/套/分型面接触R | BLOCKED | 不自动粘结；范围与真实值严格分开 |
| 冷却端口/流量/油膜/温变 | BLOCKED | 闭合几何库存不能当真实冷却系统 |
| 热区/边界选择与M3-to-M4合同 | PASS_PREPARATION | source_regions/boundary_selection_plan；非已执行ANSYS分区 |
| 新辐射遮挡计算 | PASS_SELECTED_FACE_ONLY | 修订STEP射线；非全壳体总交换/降温 |
| 源码、日志、图、三格式报告 | PASS_DELIVERY_CHECK_REQUIRED | 见delivery_checks和document_checks最终记录 |
| 实际ANSYS导入/网格/温度、Fluent | NOT EXECUTED | 本轮不进入M4 |
| 实际车型安装包络/OEM轴端/材料证书 | BLOCKED | 不强缩放，不声称能量产装车 |
| 研究者批准、合并、M3正式Tag | PENDING | 本轮未执行 |

几何检查PASS不覆盖力学和热参数BLOCKED；若准备用于定量优化，必须先解决或显式扫描上述敏感边界，并取得下一阶段授权。
