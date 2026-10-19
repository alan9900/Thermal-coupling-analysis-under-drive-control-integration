# M0 简要验收与M1启动授权记录

日期：2026-10-19（Asia/Shanghai）。配置：V0.4。原成果SHA：`2ba858b8a047566f5932a621175d360154f869e8`。

用户本轮授权：“你对m0的工作内容再做简单的验收后就可以开始m1的工作了。” 此记录表示用户授权在复核通过后关闭M0关卡并开展M1，不伪造GitHub中的人工Review记录。

## 复核结论

M0作为“参数与资料准备”阶段通过简要验收。7份官方文件哈希、配置哈希及交付检查通过；Python 3个配置测试通过。复阅已提交的隔离MATLAB复核证据：12组检查及18组制动积分通过，5个CSV与原结果数值一致。原M0报告为8页，包含21个可编辑数学对象。原始报告、代码、配置及结果不修改。

本轮实际再次运行：`py scripts/m0/test_m0_audit.py`、`py scripts/m0/check_delivery.py`。没有无理由重跑此前已经通过且未更改的MATLAB计算。复核详情：`results/m0_acceptance/acceptance_checks.json`；原验收摘要保持为历史送审快照。

验收保留以下边界：EPA再生图是镜像估计，EMOT含逆变器，未获得绕组损耗分布；连续能力、实际电池边界及39项null尚未全部补齐。验收不代表实测热场或安装安全验证。

## 版本操作与阶段边界

本记录随[PR #1](https://github.com/alan9900/Thermal-coupling-analysis-under-drive-control-integration/pull/1)合并后，为相应main验收提交创建附注Tag `M0-v1.0`，不覆盖旧版本。Tag创建成功与精确目标SHA必须通过远端查询确认，并在后续版本登记中写明；本文件写入时Tag尚未创建。

从该main基线创建 `stage/M1-heat-sources`。M1允许开发和运行多热源及能量核算程序；未经后续批准不合并M1、不创建M1正式Tag、不进入M2、ANSYS、CFD或优化阶段。
