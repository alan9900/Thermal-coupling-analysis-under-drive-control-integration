# M3 几何来源及假设审查

检索工作流：nature-academic-search多来源检索。学术MCP未挂载；本轮使用原始ORNL报告、厂家页面、KHK技术参考和CadQuery官方文档，记录直接HTTP状态与哈希，未穷尽检索。`data/raw/m3/manifest.json`保留实际获取状态；报告原件只读复用M0，不修改M2。

| 数据 | 核实依据 | 本模型使用与边界 |
|---|---|---|
| 电机壳体302×161mm、定子264/161.9×50.8mm、转子160.4/51×50.165mm | [ORNL原报告](https://info.ornl.gov/sites/publications/files/Pub26762.pdf)，表2.7，印刷46/PDF55页，已目视核对本地原件 | S1参考外形/叠片；不缩放。转子叠片孔51mm不是外伸轴直径；轴端30mm、壳壁/法兰/水套/槽形为S3 |
| 盘280×22、总高42、定位孔68mm | [Brembo09.9908.21](https://www.bremboparts.com/europe/en/view-document/catalogue/disc/09-9908-21)，原厂网页 | S1外形参考；摩擦内径、24筋、帽形、112mm孔距、5×11孔与自制毂均S3，不能称OEM复刻或转移目录制动认证 |
| 输出轴承45×85×19mm、参考质量0.404kg | [SKF6209](https://www.emarketplace.in.skf.com/deep-groove-ball-bearing/6209) | 目录边界与质量；拟用两只不等于寿命/配合/温度/载荷选型已通过 |
| 中间轴承35×72×17，输入30×62×16mm | [SKF6207](https://www.emarketplace.in.skf.com/deep-groove-ball-bearing/6207)、[SKF6206](https://www.emarketplace.in.skf.com/deep-groove-ball-bearing/6206)，SKF页面与搜索核对 | 只使用边界；CAD实心环质量不是真实滚动体质量 |
| 标准圆柱齿轮几何 | [KHK尺寸计算](https://khkgears.net/gear-knowledge/gear-technical-reference/calculation-gear-dimensions/) | 标准模数/齿数/中心距方法。两级3×3、m2.5/m3、20/60齿、宽25/32mm是S3新设计，不是Prius行星排；分段渐开线无齿根圆角/齿强度验证 |
| 真实参数化CAD与STEP | [CadQuery导出文档](https://cadquery.readthedocs.io/en/latest/importexport.html) | Python+YAML是参数化源；STEP保存中性几何。原始安装软件并未运行SolidWorks |

M2通用铜/铝热容资料继续作为材料量级参考，具体合金、复材、温变cp/k/发射率未新增标定。质量为B-rep体积×候选密度；凡几何中实体化的空腔/滚动体/叠片均须识别等效边界，不能把名义材料分组升级为真实标定。

实际安装间距、轴肩/挡圈/花键、精确轴端与电机轴承、轴承预紧寿命、内移盘卡钳产品、热接触、局部空气、水套流量及整车包络等保留null。外部空气域只供后续边界准备；实际入口/出口及旋转区域尚未验证。本阶段仅静力候选筛查，不出具安全/制造/法规认证。

尺寸范围按配置独立扫描，2187方案中729被解析约束拒绝；25mm靠近方案还做实际B-rep拒绝。45mm输出轴在S3静力限值下余量小，50mm可作为复核方向，但必须重新匹配轴承、花键、毂和密封，不能只改一根轴径即声称可制造。
