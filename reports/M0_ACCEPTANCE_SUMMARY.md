# M0 验收摘要：V0.4 后驱双独立电机

检查日期：2026-10-18。**M0 参数与资料准备交付齐备，可提交研究者验收；尚未正式批准。** 本文不批准M0、不创建正式Tag，也不授权M1。

## 版本与流程状态

| 项目 | 记录 |
|---|---|
| 车型配置版本 | `v0.4`，1800 kg后驱双独立电机，无差速器，单侧后盘详细研究范围 |
| 原M0成果提交 | `2ba858b8a047566f5932a621175d360154f869e8` |
| 本次治理基线main | `fe434fb1f846b96474a6736d77bdc20f66dc2cb7`，不将它认作M0验收提交 |
| 本次独立分支 | `stage/M0-parameter-audit` |
| 复核脚本提交 | `10f16519e332dcb32ac9c8927a5a303cbf8b54a6` |
| 复核证据提交 | 创建证据提交后登记；以STAGE_VERSIONS中的精确SHA为准 |
| PR | 创建后登记；本次PR只申请M0验收 |
| 拟议阶段版本 | `M0-v1.0`，只是候选版本名称，不是已存在的Git Tag |
| 正式流程状态 | `PARTIAL`：技术交付与复核已齐备，历史流程仍待研究者正式验收 |
| Tag及批准日期 | `NOT CREATED`；尚无批准日期 |
| M1–M7 | `NOT_STARTED` |

原M0在新制度发布前直接提交至main，既无原PR，也无阶段Tag。本次按制度第3节的历史M0专项规定补齐送审流程，不重写或回退main、不伪造历史PR、不把历史提交自动认作APPROVED。原成果保留在原SHA，本次新增验收资料经PR等待批准。获准并合并后，再按明确指令为相应main验收提交建立不可移动的附注Tag。

## 原任务完整性检查

| 原任务 | 结果 | 主要证据 |
|---|---|---|
| 1. EPA官方MG2数据包获取 | 已完成；32,352,137字节ZIP，来源及SHA-256齐备 | `data/raw/m0/manifest.json`及原始ZIP |
| 2. 格式、转速转矩与正负象限 | 已完成；12文件，14×39完整数值表，0–13000rpm、−200至200N·m；再生实测完整性不成立 | `results/m0/epa_map_audit.json`、`epa_zip_inventory.json` |
| 3. 60kW／207N·m／13500rpm校核 | 已完成来源校核；60kW不能当连续能力 | ORNL／Toyota原始资料，原报告第4节 |
| 4. EMOT与绕组热源区分 | 已明确；联合电机／逆变器损耗不得全给绕组；137个配对驱动效率点可追溯 | `ornl_paired_drive_efficiency.csv`及原报告第3节 |
| 5. 1800kg整车参数审查 | 已完成；真实参照、假设及null区分；修正后驱加速附着公式符号 | `configs/baseline_vehicle.yaml`、`results/m0/parameter_audit.csv` |
| 6. 不同减速度／再生功率的单盘核算 | 已完成；0.3／0.6／0.8g，整车电池上限0／30／60kW；无路阻和含路阻共18组 | `results/m0/braking_review.csv`、`m0_results.mat` |
| 7. 功率、转速、9:1及160km/h匹配 | 短时参数筛查通过；持续高速未验证 | `results/m0/speed_power_review.csv`、`derived_metrics.json` |
| 8. 减速器、尺寸、物性、冷却、制动器缺口 | 已列清单；当前配置39项保留null | 原报告第8节、`parameter_audit.csv` |
| 9. 参数审查报告与资料提交 | 已完成；代码、配置、CSV/MAT、PNG/SVG、测试记录、Markdown／Word／PDF均已入Git | 原M0提交及本次验收PR |

上述“已完成”限于M0资料获取和参数审查，不表示概念总成已经实测，也不表示M1输入已全部确定。

## 本次实际复核

完整机器可读记录：[acceptance_checks.json](../results/m0_acceptance/acceptance_checks.json)。本次不刷新下载、不更改原报告、不替换原M0输出；在`tmp/m0_acceptance/project`隔离运行原MATLAB脚本。新复核证据保存于`results/m0_acceptance/`。

| 检查 | 本次结果 |
|---|---|
| 原始资料完整性 | 7份已下载官方文件字节数与SHA-256均通过；原下载失败记录另保留 |
| EPA ZIP、数值解析与插值 | 重新检查CRC、12文件清单及数值转存；546个有限值、137个配对驱动点，审计结果与历史一致 |
| Python配置测试 | 3个测试通过，覆盖10种无效输入拒绝；见`python_tests.txt` |
| MATLAB R2025a | 实际执行；12组检查通过，18组制动积分通过；见`matlab_run.txt`与新`validation.json` |
| 与历史输出比较 | 5个CSV的18／4／27／3／18行数值逐项相同，最大绝对差0 |
| 整车能量残差 | 最大相对值`7.91042111814022e-16`，检查阈值`1e-9` |
| 积分细化 | 相对变化`7.385392216087986e-6`，低于`5e-4`阈值 |
| Word／PDF | 本次重新检查到21个OMML对象和8页PDF；保留此前逐页目视QA记录，未重新排版或声称重新人工逐页检查 |
| 原文件保护 | 59个受监测输入／产物／脚本哈希未变；清单见`original_artifact_hashes.json` |
| 未运行／不适用 | 原ALPHA／REVS对象、M1热源、热网络、CAD、ANSYS、Fluent、优化及实体实验均未在本次执行 |

本次复核命令：

```powershell
py scripts/m0/review_acceptance.py prepare
& 'F:\Program Files\MATLAB\R2025a\bin\matlab.exe' -batch "addpath('tmp/m0_acceptance/project/scripts/m0'); run_m0_review" -logfile tmp/m0_acceptance/matlab_run.log
py scripts/m0/review_acceptance.py collect
```

`prepare`遇到已有临时项目会停止，避免删除既有复核记录。原报告及复算方法见[scripts/m0/README.md](../scripts/m0/README.md)。

## 验收需要保留的限制

1. **再生不是实测MAP。** EPA负转矩区由驱动损耗乘1.05镜像估计；数据表到13000rpm，13500rpm只是最高转速声明；仅650V，不覆盖任意母线电压。
2. **热源尚不具备直接应用条件。** 连续功率、独立绕组／铁芯／转子损耗、温限、实际再生及电池SOC／温度／充电边界仍未知。EMOT总损耗不等于绕组发热。
3. **工程假设不能升级为事实。** 再生效率0.90、130N·m再生限扭、5km/h退出、传动效率0.96等仅用于筛查；同附着轴间分配不是量产EBD。160km/h只通过转速和短时动力筛查。
4. **机械及热参数未补齐。** 39项null及更详细的减速器几何、内移盘支承、热物性、冷却和制动器能力仍需补充；目录盘不能证明安装或法规符合性。
5. **来源与归档限制。** 原获取记录中VW 2020技术页为404，Cd=0.27保持未验证；本次没有重试该网页。既有原包含第三方附件且无统一许可证，未宣称其全部无版权；后续新增大型／受限资料必须先确定合规归档方式，本次未新增这类资料或重写历史。

## 审阅结论

建议研究者按“参数与资料准备”范围审阅M0：文件交付齐备，复算一致，局限已明确；正式验收尚待批准。审批前保留`PARTIAL`，Tag为`NOT CREATED`。本次PR不申请合并授权以外的任何阶段工作，也不申请启动M1。M0批准、合并与正式Tag建立后，是否开展M1仍等待明确阶段指令。

原始报告：[Markdown](M0_report.md) / [Word](M0_report.docx) / [PDF](M0_report.pdf)。版本与PR登记：[STAGE_VERSIONS.md](../docs/STAGE_VERSIONS.md)。
