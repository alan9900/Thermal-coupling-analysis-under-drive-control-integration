# V0.4 M0：资料与参数复核

范围仅限M0。程序没有温度求解、ANSYS接口、热源时间序列或优化。

## 复算

在仓库根目录执行（Windows PowerShell，Python 3.13和MATLAB R2025a已验证）：

```powershell
py -m pip install -r scripts/m0/requirements.txt
# 原始ZIP及官方资料已经提交；只有刷新来源时才需要执行下一条。
py scripts/m0/fetch_sources.py
py scripts/m0/test_m0_audit.py
py scripts/m0/prepare_audit.py
& 'F:\Program Files\MATLAB\R2025a\bin\matlab.exe' -batch "addpath('scripts/m0'); run_m0_review"
```

MATLAB路径按机器调整。Python不以`-O`运行，因为本M0审查使用assert进行前置条件检查。YAML经Python转成JSON，MATLAB无需额外YAML库；null在MATLAB中表现为空数组并保持未知，不填零。

`prepare_audit.py`始终先核验ZIP CRC及内部路径，再提取原文件；不执行EPA下载的代码。数值 `.m` 已含完整电功率表，可独立解析。ALPHA/REVS外部类及HTML中的`Extracted_Data_emach`不随包提供，本次未运行完整ALPHA对象。运行前确保官方包、配置与manifest相匹配；刷新会更新获取时间和哈希，来源改变后需重新审查。

`fetch_sources.py`会逐项记录失败；VW 2020技术页当前404被保留为失败，不影响已下载的EPA主包。MY21的轴距由PDF第19页图示目视核实。原始PDF只在ZIP内保留一份解包附件，Git忽略重复提取的EPA PDF。官网ORNL及VW PDF另外保留以追溯下载来源。

## 输出

- `results/m0/parameter_audit.csv`：配置全部叶子字段的值、单位、来源层级、未知项与后续影响。
- `epa_map_audit.json`、`epa_zip_inventory.json`：完整性、象限及文件证据。
- `epa_emot_grid.csv`、`epa_map_numeric.json/.mat`：546点原始数值转存，限扭包络另列；不是新损耗模型。
- `ornl_paired_drive_efficiency.csv`：137个电机／逆变器配对驱动效率点。
- `braking_review.csv`：无路阻和含路阻各9组参数积分；单盘摩擦量、前轴及两后侧总再生能量分开。
- `screening_assumptions.json`：空气密度、再生效率、转矩及低速退出假设；不写入真实硬件参数。
- `speed_power_review.csv`、`derived_metrics.json`：功率／转速／速比筛查。
- `regen_assumption_sensitivity.csv`、`geometry_assumption_sensitivity.csv`：假设扫描，非优化。
- `validation.json`、`m0_results.mat`：MATLAB检查与原始工作结果；PNG/SVG为M0审查图。

所有再生数字是650V参考包络与假设效率、假设再生限扭的筛查；电池上限0/30/60kW为**整车总值**。负转矩不是实测再生证据。连续功率、绕组损耗及实际再生控制参数保持null。

## 报告重建与排版检查

作者源文件为 `reports/M0_report.md`，Word由本地`pandoc-report-word`技能脚本生成。

```powershell
py scripts/m0/report_qa.py reference
& 'C:\Users\90521\.codex\skills\pandoc-report-word\scripts\Convert-PandocReport.ps1' -InputPath reports/M0_report.md -OutputPath reports/M0_report.docx -ReferenceDoc reports/M0_reference.docx
py scripts/m0/report_qa.py render
```

可改用复制在本目录的`Convert-PandocReport.ps1`，它与本次使用的技能转换脚本相同。`report_qa.py`对Pandoc结果仅作格式整理（表头底纹、不拆分表格行、表内行距和中文语言元数据），不改文字、数据或公式；然后使用安装的Microsoft Word独立隐藏实例导出PDF，再用PyMuPDF生成页图，不会附着或关闭用户现有Word实例。脚本检查OMML数学对象、表格及图像。人工逐页检查后才将结果记录到`results/m0/delivery_checks.json`。

报告表格与文字是审查源，参数更改后需同步重审；不应只重跑脚本而假定报告数值自动更新。

原始资料保留来源及版权，不为其附加本仓库自有许可证。用户确认前不要开始M1。
