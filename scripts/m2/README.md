# M2 单侧多热源LPTN（概念预测，未标定）

基线：M1-v1.0，main合并 `9d545ab39a3efcce857573af74f7e325b74a2b15`。M1限定概念范围验收，真实损耗标定仍PARTIAL。M0/M1固定版本和成果只读。

## 完整复现

依赖沿用 `scripts/m0/requirements.txt`。在仓库根目录：

```powershell
py scripts/m2/prepare_inputs.py
& 'F:\Program Files\MATLAB\R2025a\bin\matlab.exe' -batch "addpath('scripts/m2'); run_m2" -logfile results/m2/matlab_run.log
py scripts/m2/check_outputs.py
py scripts/m2/topology_figure.py
py scripts/m2/sensitivity_figure.py
```

可选 `collect_sources.py` 会更新检索记录，必须在prepare_inputs之前运行。已有登记支持离线计算；M2不依赖在线资料下载成功。Word报告另用本地pandoc-report-word技能脚本从Markdown生成，再运行 `report_qa.py` 以Word导出PDF，人工检查后填写document_checks。

## 接口与求解

- `m2_load` / `m2_network`：独立工程配置、13节点、唯一跨域边界。严格模式缺真实热参数时拒绝；不回填unknown_actual或旧baseline。
- `m2_segments`：只读M1函数/数据，复核已归档短驱动分项；新生成80→0制动和坡道预热均保存M2。逆变器不加载入热域，转子其他/油其他采用明确等效节点。
- `m2_forcing`：同一运动时间轴的六组0→80驱动、80→0制动、20s停歇和600s冷却。D在第一次驱动后额外加入60s、0.18rad上坡、约41.18kW/侧预热；仅验证瞬时包络，不证明连续能力。
- 每个原M1分段按线性功率的解析积分重采样为区间平均，保留精确热量；不跨不同工况的源项跳变插值。
- `m2_flux` / `m2_simulate`：K制非线性辐射、双向传热、显式RK4与同阶累计能量积分；固定热容，无温变反馈。总网络和电驱子域分别检查储热/环境/冷却收支。
- 路径热量按唯一跨域边界累计：辐射2边、局部空气对流1边、固体3边（轴到轴承、轴到齿轮、钳支架旁路）。盘→轴及轴承→壳体逐边导出，但不再加进边界总量重复计数。

A/B是同运动序列的受控热源消融，分别只加载内部损耗/摩擦热；不是两种新的整车能量闭合工况。C加载全部热源，D额外先驱动预热。路径移除对比不是可相加的温度贡献率，可能同时去掉原先的散热路径。

## 成果与大小

`results/m2/cases/` 保存4主场景+3路径移除的完整CSV、源项区间CSV与JSON；每个内部边瞬时有符号热流、净累计量和正向累计量都保留。`compiled_network.json` 可独立重构热流；`inputs.json` 与独立检查记录源/输出SHA-256。

`m2_results.mat` 保存所有主场景与18敏感性场景的温度和路径累计结果、参数、汇总及细步D。为控制归档大小，MAT不重复三份CSV已保存的逐边矩阵；全部逐边结果仍在CSV。单文件MAT约13MB、每个CSV约5–6MB，是有限可重算结果，未生成ANSYS/Fluent大场文件。后续扩展需重新评估LFS/外部归档，不能无限堆积。

独立检查包含7场景输入/储热/边界/跨域账本及自适应SciPy RK45比较。瞬时CSV热流为右侧状态诊断值，累计量来自RK4积分；不要用粗时间梯形重积分替代原能量账本而误判残差。

只刷新曲线布局可运行 `render_saved_plots`，不重算温度、不覆盖测试。补充PNG/SVG均标记S3概念预测。初次12,000s无源测试观察窗不足及随后诊断日志保留，最终24,000s测试使用同一0.1K判据。

M2未经研究者验收不合并，不创建M2-v1.0，不开始M3/CAD/ANSYS/Fluent。参数与来源限制见 `docs/M2_SOURCE_REVIEW.md`。
