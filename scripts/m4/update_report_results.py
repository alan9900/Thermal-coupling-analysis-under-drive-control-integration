"""Actual result tables in Markdown; pending never becomes PASS."""
import csv,json,subprocess
from datetime import datetime
from summarize_studies import ROOT,OUT,STUDIES,load

def pick(*names):return next((n for n in names if load(n)),None)
def peak(name,part):return max(float(r['maximum']) for r in load(name) if r['part']=='M4_'+part)
def main():
    report=ROOT/'reports/M4_report.md';text=report.read_text(encoding='utf-8')
    choices={'A':pick('A_normal12_rd95_dt1_retry1','A_internal_only_dt1'),
      'B':pick('B_normal12_rd95h_dt4_retry1','B_normal12_rd95h_dt2','B_normal12_rd95h_dt1','B_normal24_rd95h_dt1','B_normal12_dt1_retry1'),
      'C':pick('C_normal12_rd95_dt1','C_normal12_dt1','C_combined_dt1_retry1'),
      'D':pick('D_normal12_rd95_dt1','D_preheat_braking_dt1')}
    source=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    lines=['# 5. 实际结果与模型比较','',
      '数据整理时间：'+datetime.now().astimezone().isoformat(timespec='seconds')+'。文档基于提交 '+source+' 及本轮更新；求解输入以原生清单的实际文件 SHA256 为准，不把该提交冒充所有任务的启动源码。','',
      '下表为各热源场景当前已完成计算的局部最高温度，单位 °C。不同场景热历史及窗口不同，不能把峰值差直接当作纯制动热贡献。显示位数用于复核，不代表实际温度精度。','',
      '| 热源场景 | 制动盘 | 输出端轴承 | 减速器后壳 | 油液等效体 | 绕组 |','|---|---:|---:|---:|---:|---:|']
    for case,name in choices.items():
        if name:lines.append('| '+case+' | '+' | '.join('%.3f'%peak(name,p) for p in ['BRAKE_DISC_HAT','OUTPUT_BEARING_2','GEAR_CASE_REAR','OIL_INVENTORY','MOTOR_WINDING'])+' |')
    lines+=['','各行数据来源：','']
    for case,name in choices.items():
        if name:
            meta=json.loads((STUDIES/name/'study_settings.json').read_text(encoding='utf-8-sig'))
            lines.append('- '+case+'：'+name+'，终点 %.4f s，%d 个结果时刻。'%(meta['duration_s'],meta['expected_sets']))
    lines+=['','D 的高负载保持是给定的工程热负荷，不代表普通平路恒速行驶。本轮不是 M2 六周期耐久制动，不能用单次制动峰值替代连续制动最高温度。','',
      '| 场景 | 总输入 J | 最大总体热能相对残差 | 实际状态 |','|---|---:|---:|---|']
    for case,name in choices.items():
        if not name:continue
        p=STUDIES/name/'pilot_FE_energy_checks.json'
        if p.exists():
            r=json.loads(p.read_text(encoding='utf-8-sig'))
            lines.append('| %s | %.3f | %.5g%% | %s |'%(case,r['final']['input_J'],r['max_relative_residual']*100,'PASS 离散储热与边界收支' if r['status'].startswith('PASS') else r['status']))
    checks=json.loads((OUT/'convergence_checks.json').read_text(encoding='utf-8-sig'))
    lines+=['','| 数值验证项目 | 实际状态 |','|---|---|']
    for key,r in checks.items():lines.append('| '+key+' | '+r['status']+' |')
    lines+=['','实体网格比较采用 6/12/24 层摩擦片和 4/2/1 mm 制动面。时间比较采用中网格生产候选，减半制动时间步，并细化 30 s 冷却段。阈值是预先登记的工程筛查，不是正式 GCI 或实验误差。细网格盘面采用 RDEC，须另通过辐射面误差检查。','',
      '![实际网格加密结果；一层摩擦片已拒绝。](../results/m4/mesh_refinement_actual.png){width=15cm}','',
      '原一层摩擦片约 150°C 峰值已拒绝。多层结果为约 400°C 量级，仍依赖候选热量分配、固定面热流和常热物性；不是实测温度或安全限值。','']
    if (OUT/'time_refinement_actual.png').exists():lines+=['![实际三档时间步比较，包含制动及30 s冷却。](../results/m4/time_refinement_actual.png){width=15cm}','']
    if (OUT/'refined_source_scenarios.png').exists():
        lines+=['![相同12层网格与辐射离散的A/B/C/D热源场景。](../results/m4/refined_source_scenarios.png){width=15cm}','']
    else:lines+=['![相同原始诊断网格的热源对比；不比较已拒绝的摩擦片峰值。](../results/m4/source_scenario_comparison.png){width=15cm}','']
    if (OUT/'added_brake_response.png').exists():
        lines+=['![相同内部热源及边界的C减A响应；微小温差不代表实测精度。](../results/m4/added_brake_response.png){width=15cm}','',
          'C−A 比较使用同一几何、网格、时间轴及内部损耗，只有制动盘/片摩擦热不同。热容均温之差表示区域储热变化；区域最大值之差并非逐点温差场最大值。非线性辐射保留，差值不能直接作为独立线性传递系数。低于网格筛查绝对温差门槛的信号仅用于诊断，不证明其物理精度。','']
    field=next((n for n in ['D_normal12_rd95_dt1','C_normal12_rd95_dt1','C_normal12_dt1'] if (STUDIES/n/'component_peak_fields.png').exists()),None)
    if field:lines+=['![实际有限元表面温度；各部件在自身峰值时刻，独立色标，S3 预测。](../results/m4/studies/'+field+'/component_peak_fields.png){width=15cm}','']
    lines+=['![M2 与 M4 首次制动；不同热容与边界，不是实验验证。](../results/m4/M2_M4_first_brake_comparison.png){width=15cm}','',
      'M2 是集总温度；M4 同时保存节点最大值和热容加权平均。CAD 修订使输出轴热容由 552 变为约 2061 J/K、齿轮由 1150 变为约 3914 J/K、减速器壳体由 3600 变为约 8644 J/K。完整分组见 M2_M4_capacity_comparison.csv。转接件、转子与轴的分组也不同。','',
      'M2 含护罩与局部热空气节点；M4 Case0 没有新增护罩，也未求解热空气回流。不能把温差全部归因于散热改善，或据短周期宣布长期轴系热侵入不重要。','']
    start=text.index('# 5. ');end=text.index('# 6. ',start)
    text=text[:start]+'\n'.join(lines)+'\n'+text[end:]
    marker='<!-- ACTUAL_PATH_RESULTS -->';stop='<!-- END_ACTUAL_PATH_RESULTS -->'
    paths=['## 6.1 实际路径输出','',
      '下表是各自窗口终点有符号净积分，单位 J。固体跨界仅计连接套→输出轴和支架→壳体；轴承串联截面不重复相加。壳体净辐射包括开口环境，未分离成纯盘→壳体交换。','',
      '| 工况 | 固体净流入 | 壳体净辐射流入 | 环境对流流出 | 冷却带走 | 子控制体 |','|---|---:|---:|---:|---:|---|']
    selected=[]
    for name in ['B_normal24_rd95h_dt1','B_normal12_rd95h_dt4_retry1','C_normal12_rd95_dt1','D_normal12_rd95_dt1']:
        p=STUDIES/name/'heat_path_checks.json'
        if p.exists():
            r=json.loads(p.read_text(encoding='utf-8-sig'));f=r['final'];selected.append(name)
            values=[f[k+'_net_J'] for k in ['solid_cut_into_drive','radiation_net_into_case','ambient_drive_out','coolant_out']]
            paths.append('| '+name+' | '+' | '.join('%.5g'%v for v in values)+' | '+('PASS' if r['status'].startswith('PASS') else 'BLOCKED')+' |')
    if not selected:paths.append('| 待完成 | — | — | — | — | PENDING |')
    paths+=['','瞬时有符号功率、累计正向流入与净积分独立保存在 signed_heat_paths.csv。负数表示反向传热，不能把绝对值强计为热侵入。外部对流是环境散热；**热空气回流为 NOT MODELLED，不是物理零值**。旧粗网格 B 子控制体残差约 0.72% 超过 0.5% 阈值，历史 BLOCKED 保留。','']
    if selected:
        name=selected[-1]
        if (STUDIES/name/'signed_heat_paths.png').exists():paths+=['![实际路径；符号、正向与净积分分开，辐射含开口环境。](../results/m4/studies/'+name+'/signed_heat_paths.png){width=15cm}','']
    if (OUT/'contact_cooling_sensitivity.png').exists():paths+=['![实际接触与冷却敏感性；工程场景范围，非实测置信区间。](../results/m4/contact_cooling_sensitivity.png){width=15cm}','']
    sensitivity=OUT/'sensitivity_temperature_summary.csv'
    if sensitivity.exists():
        data=list(csv.DictReader(sensitivity.open()))
        paths+=['| 部件 | 五个已算场景峰值范围 °C |','|---|---:|']
        for part in ['BRAKE_DISC_HAT','OUTPUT_BEARING_2','GEAR_CASE_REAR','OIL_INVENTORY','MOTOR_WINDING','PAD_NEAR']:
            values=[float(r['peak_C']) for r in data if r['part']=='M4_'+part]
            paths.append('| '+part+' | %.3f–%.3f |'%(min(values),max(values)))
        paths+=['','范围只覆盖基准及四个已算边界场景，不包括冷却液体温、材料方向性、全部内部接触和损耗分配不确定性。','']
    incremental=OUT/'added_brake_heat_path_checks.json'
    if incremental.exists():
        r=json.loads(incremental.read_text(encoding='utf-8-sig'));f=r['final']
        paths+=['## 6.2 相同内部热源的增量收支','',
          '比较 C−A 后，终点电驱总成储热增加 %.5g J；固体跨界净输入增加 %.5g J，壳体净辐射输入增加 %.5g J，环境对流流出增加 %.5g J，冷却带走增加 %.5g J。增量收支状态 %s，最大相对残差 %.5g%%。'%(f['delta_drive_stored_J'],f['delta_solid_cut_into_drive_net_J'],f['delta_radiation_net_into_case_net_J'],f['delta_ambient_drive_out_net_J'],f['delta_coolant_out_net_J'],r['status'],100*r['relative_residual']),'',
          '壳体净辐射差仍包含壳体温度改变后与环境交换的变化；它不是完全分离的盘—壳体两体交换。未模拟热空气回流，不能据当前短窗口给真实系统三条路径作完整排序。','',
          '![相同时间轴C减A的路径功率与净能量差，非累计绝对热流。](../results/m4/added_brake_heat_paths.png){width=15cm}','']
    block=marker+'\n'+'\n'.join(paths)+'\n'+stop
    if marker in text:text=text[:text.index(marker)]+block+text[text.index(stop)+len(stop):]
    else:text=text.replace('# 7. ',block+'\n\n# 7. ',1)
    report.write_text(text,encoding='utf-8');print('Report updated from actual receipts; pending retained.')
if __name__=='__main__':main()
