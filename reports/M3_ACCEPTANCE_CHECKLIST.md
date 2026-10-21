# M3 概念几何验收检查表

当前：**技术交付齐备，研究者验收PENDING**。可申请验收范围为可追溯参数化概念几何、四方案、限定安装/静力筛查及几何热参数候选，不含生产发布或降温验证。

[PR #4](https://github.com/alan9900/Thermal-coupling-analysis-under-drive-control-integration/pull/4)，分支stage/M3-geometry；基线M2-v1.0 `1d51c22d94577ff8f52be785300b5f6b4aadee37`。生成源提交`3ea9c6bd2af2cde56d17c1ce5f56ba446813477b`。

| 项目 | 结果与适用范围 |
|---|---|
| M2先归档 | PASS：PR #3合并；M2-v1.0附注Tag远端核验；M0/M1不变 |
| V0.4拓扑 | PASS：后驱双独立电机、每侧9:1、输出端内移盘，无差速器，详细单侧 |
| 参考尺寸 | PASS：ORNL电机/叠片、Brembo盘外形、SKF轴承边界，原始来源/哈希明确；自设计S3 |
| 实际CAD执行 | PASS：CadQuery2.8/OpenCascade7.9，非仅脚本；SolidWorks NOT EXECUTED |
| 参数化源及STEP | PASS：YAML+Python可编辑源，56 STEP；mm、有效Brep与回读体积检查 |
| 真正Case0 | PASS：不存在新增罩/支柱/通道，明确不同于含罩的M2原网络 |
| CaseA/B/C | PASS：单/双层及通道，公共32体一致，开口保留连续桥带，间隙/厚/角度/面积参数化 |
| 名义干涉 | PASS：283候选对精确布尔后无>0.001mm³交叠；18个齿轮相位通过 |
| 失败/拒绝记录 | PASS：轴端/安装孔冲突、STEP退化、封闭空气气穴的初次失败与修复记录保留 |
| 热膨胀/范围 | PASS限定筛查：400K假设、容差/跳动分开；2187解析组合中729拒绝，25mm紧凑布局实际拒绝 |
| 输出轴/反力 | PASS有限静力计算：40mm拒绝，45mm余量很小；载荷从钳片/支架传至壳体/车架耳。实际材料、预紧/疲劳和车辆支承未验证 |
| 热阻推导 | PASS：L/A/k与径向对数公式、SI单位；接触R保留null，轴承连续体仅下界，不冒充M2等效真值 |
| 辐射遮挡 | PASS限定直接几何F：指定端面、射线细化/解析圆盘对照；支柱/连接耳/多次辐射/壳侧面等限制明确，不称温降 |
| M2接口 | PASS：新CSV/JSON质量/C、热阻、面积和几何；不覆盖M2，不重载总损耗，不把逆变器入绕组或转子其他当磁体 |
| 空气/水/油域 | PASS概念边界：4连通外气域，封闭气穴单列；水套无实测端口/流量，油库存非全空腔填油 |
| 报告/曲线/测试记录 | 见M3_report.md/.docx/.pdf、results/m3/document_checks.json、tests.json、geometry_checks.json及日志 |
| 生产、整车安装、寿命和实测热标定 | NOT EXECUTED；壳体分型、轴向定位、花键、密封、轴承寿命、支架预紧及整车包络仍缺 |
| 研究者M3验收 | PENDING；本表不代替批准 |
| M3合并/正式Tag/M4 | NOT DONE / NOT CREATED / NOT STARTED |

完整成果位置：[CAD](../cad/m3/README.md)、[配置](../configs/m3_geometry.yaml)、[复现](../scripts/m3/README.md)、[报告](M3_report.md)、[来源审查](../docs/M3_SOURCE_REVIEW.md)。
