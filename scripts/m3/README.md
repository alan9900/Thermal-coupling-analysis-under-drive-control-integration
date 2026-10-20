# M3 参数化概念几何（CAD已实际执行）

基线 `M2-v1.0`：`1d51c22d94577ff8f52be785300b5f6b4aadee37`。分支 `stage/M3-geometry`，[PR #4](https://github.com/alan9900/Thermal-coupling-analysis-under-drive-control-integration/pull/4)。所有M2固定文件只读。

模型可编辑源为 **`configs/m3_geometry.yaml` + `cad_model.py`**，使用CadQuery2.8.0/OpenCascade7.9.3.1实际建模。STEP是中性几何，不携带完整参数历史；重建/改参请编辑上述源。没有运行SolidWorks、ANSYS或Fluent。

在仓库根目录PowerShell：

```powershell
py -m venv tmp/m3_cad
& tmp/m3_cad/Scripts/python.exe -m pip install -r scripts/m3/requirements.txt
& tmp/m3_cad/Scripts/python.exe scripts/m3/run_geometry.py
& tmp/m3_cad/Scripts/python.exe scripts/m3/analyze_geometry.py
& tmp/m3_cad/Scripts/python.exe scripts/m3/geometry_tests.py
& tmp/m3_cad/Scripts/python.exe scripts/m3/render_geometry.py
```

资料重新核对可单独运行`py scripts/m3/collect_sources.py`，离线复现不依赖重新下载。Python依赖的完整版本另存在results/m3/environment.txt，安装曾遇TLS重试但最终成功，无需关闭证书验证。

`cad/m3/base_parts/`保存共同零件一次，各Case子目录仅保存新增罩体/支柱；四个`*_assembly.step`是包含命名部件的完整装配，四个`*_air_domain.step`为连通外部局部空气域。全部有限STEP约78MB，最大装配约14MB；不提交CAD内核/环境/缓存，不无计划重复存放拓展DOE模型。后续更大场数据须另行评估LFS或受控归档。

`results/m3/`保存质量/C、热阻候选、辐射直接视角、参数/间隙/静力检查、单元/回归测试、STEP哈希、日志及图片。体积来自B-rep，密度/cp/k为材料等效候选；轴承CAD是实心环包络，不能用其体积×钢密度冒充实物轴承质量。本轮M2输出轴承候选取两只6209目录参考质量0.404kg/只，仍不代表完成选型。

温度不求解：M3只输出新的候选接口；M2的罩节点不是本阶段Case0。几何CaseA/B/C也不是M2热源加载A/B/C/D。逆变器外置、转子其他非磁体、分项总损耗不重复加载等规则不变。

几何验证范围：名义装配四Case、AABB剔除后的全对布尔交集、STEP回读、18个齿轮相位、范围解析筛查与25mm紧凑布局实际干涉拒绝。不是GD&T、疲劳/齿强度、轴承寿命、装车安装或法规认证。

M4准备要求：先核对装配单位mm并转换SI，分离/标识固体与油/水/空气域，绕组50体需等效共享拓扑或绑定接触；不得把油/水域当成金属；重新定义接触、辐射面、冷却和材料。外部空气域是选定局部边界，不含旋转网格/入口速度/湍流/外部车辆空间；两处各约689mm³的密闭螺栓间隙空气不并入外部连通域。环形水套无实测端口/流量图，不能当作完整泵循环。M3批准前不进入这些求解工作。

初次干涉、STEP和空气连通检查失败日志保留；修复采用轴端收回、错位安装孔、避免通风筋精确相切退化、区分封闭气穴及保留护罩连续桥带，未缩放参考电机。

报告Word从Markdown经本地pandoc-report-word技能脚本生成，实际Word导出PDF并检查。未经研究者批准不合并PR、不创建M3-v1.0、不进入M4。
