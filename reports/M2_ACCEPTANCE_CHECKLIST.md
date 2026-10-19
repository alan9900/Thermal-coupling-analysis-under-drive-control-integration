# M2 概念瞬态热网络验收检查表

状态：**数值交付齐备，研究者验收PENDING**。模型为S3概念预测，未取得样机温度标定；M1真实损耗标定仍PARTIAL。不得据此认定实际总成热安全或法规符合性。

基线V0.4；分支 `stage/M2-thermal-network`；[PR #3](https://github.com/alan9900/Thermal-coupling-analysis-under-drive-control-integration/pull/3)。数值运行源提交 `ff818ccb35daf8d70d0cbafbf28fc6690ab457a8`；完整成果提交在阶段登记后续记录，避免自引用。

| 项目 | 检查结果与证据 |
|---|---|
| M1先归档再启动M2 | PASS：PR #2已合并，附注M1-v1.0远端剥离至9d545ab39a3efcce857573af74f7e325b74a2b15；M0固定版本未改 |
| V0.4、单侧详细模型 | PASS：后驱双独立电机，无差速器；详细热域单侧；前轴/双侧动力学沿用M1 |
| 热网络节点与边界 | PASS：13动态节点，22内部边；空气有限热容；环境/冷却液固定热库，拓扑PNG/SVG与配置齐备 |
| 传热方程 | PASS：绝对K辐射、双向温差、被动内部传热成对抵消；外界/液冷净热量带符号 |
| 三条热侵入路径 | PASS：唯一跨电驱子域边界，瞬时有符号/正向累计/净量分别导出，不重复统计连续边 |
| 输入与数据等级 | PASS：只读M1、严格缺参拒绝；原始null/NaN保留，S3配置独立；不加载逆变器、不把转子其他等同磁体、不叠加总损耗 |
| 资料与适用范围 | PASS：docs/M2_SOURCE_REVIEW.md，原始下载成功/失败记录和哈希、NIST参考值；资料未验证总成热阻/视角 |
| A/B/C/D场景 | PASS：4基础场景；A/B受控热源消融；D约41.18kW/侧60s预热，不证明连续功率 |
| 热网络能量闭合 | PASS：MATLAB全网络最大相对残差5.28e-14；电驱子域最大绝对残差1.50e-8J，含储热、环境与冷却 |
| 无源与热流方向 | PASS：24,000s无源最大残余0.000657K；热冷却液允许反向加热；初次12,000s未达判据的日志保留 |
| 独立解与时间步长 | PASS：单热容解析解；C名义/细0.001203K，D0.001562K；SciPy自适应RK45与C最大温差0.002916K |
| 敏感性 | PASS：8参数双端点16次+2组守恒M1联合分配；另3路径移除；不是概率区间或可加贡献率 |
| 误差与未建模项 | PASS披露：总损耗尺度扰动不重算电池控制；空载拖曳/零功率搅油/温度反馈未建模，乘法范围不能补出零基线遗漏 |
| 软件实跑 | PASS：MATLAB25.1.0.2943329/R2025a，11组测试通过；Python独立复核7场景；真实日志保留 |
| 结果与可复算性 | PASS：CSV/MAT、输入/输出哈希、参数、PNG/SVG、测试JSON、日志、复现README齐备 |
| 报告三格式及视觉检查 | 见reports/M2_report.md/.docx/.pdf及results/m2/document_checks.json；最终检查随证据归档 |
| 真实温度验证 | NOT EXECUTED；需实际几何、质量、热接触、冷却/气流、损耗与温度测量 |
| 研究者验收 | PENDING；本表为技术送审检查，不代替批准 |
| M2合并/正式Tag | NOT DONE / NOT CREATED；须另获批准 |
| M3/CAD/ANSYS/Fluent | NOT STARTED / NOT EXECUTED |

主报告：[Markdown](M2_report.md) / [Word](M2_report.docx) / [PDF](M2_report.pdf)。数值证据：[验证](../results/m2/validation.json)、[测试](../results/m2/tests.json)、[独立复核](../results/m2/independent_checks.json)、[实际日志](../results/m2/matlab_run.txt)。
