"""Evidence-driven M4 checklist. Missing or failed runs never become passes."""
import csv, hashlib, json, subprocess
from datetime import datetime
from pathlib import Path
from summarize_studies import ROOT, OUT, STUDIES, load

CASES={'A':'A_normal12_rd95_dt1','B':'B_normal12_rd95h_dt4',
       'C':'C_normal12_rd95_dt1','D':'D_normal12_rd95_dt1'}
PATH_CASES=[CASES[k] for k in ['B','C','D']]

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else None

def main():
    items=[]
    def add(key,title,status,evidence,detail=''):
        items.append(dict(id=key,item=title,status=status,evidence=evidence,detail=detail))
    inp=read(OUT/'input_tests.json')
    add('inputs','配置、未知值、M1接口与来源边界','PASS' if inp and inp['status'].startswith('PASS') else 'PENDING',
        'results/m4/input_tests.json','12组前处理检查；不代替有限元数值验证')
    shape=read(OUT/'meshes/native_shape_checks.json')
    shape_pass=shape and len(shape)==3 and all(r['error_elements']==0 for r in shape.values())
    add('mesh_shape','三套原生网格默认形状检查','PASS_WITH_WARNINGS' if shape_pass else 'PENDING',
        'results/m4/meshes/native_shape_checks.json','0错误；警告单元仍保留，不能称全部优质网格')
    bench=read(OUT/'native_benchmark_checks.json')
    add('units','实际原生热容/后向欧拉对流基准','PASS' if bench and bench['status'].startswith('PASS') else 'PENDING',
        'results/m4/native_benchmark_checks.json','单单元等温基准；不验证空间网格或辐射')
    for case,name in CASES.items():
        p=STUDIES/name;manifest=read(p/'native_archive_manifest.json')
        data=load(name)
        ready=manifest is not None and data is not None
        add('solve_'+case,case+'真实原生瞬态求解及预期时刻','PASS' if ready else 'PENDING',
            'results/m4/studies/'+name+'/native_archive_manifest.json')
        energy=read(p/'pilot_FE_energy_checks.json')
        add('energy_'+case,case+'总体储热/散热/冷却/辐射收支',
            'PASS' if ready and energy and energy['status'].startswith('PASS') else 'BLOCKED' if energy and not energy['status'].startswith('PASS') else 'PENDING',
            'results/m4/studies/'+name+'/pilot_FE_energy_checks.json',
            ('最大相对残差 %.8g；阈值 0.005'%energy['max_relative_residual']) if energy else '')
    conv=read(OUT/'convergence_checks.json') or {}
    for name in ['mesh','time','radiation_facets_fine','radiation_facets_medium','radiation_facets_combined']:
        r=conv.get(name,{})
        status='PASS' if r.get('status','').startswith('PASS') else 'BLOCKED' if r.get('status','').startswith('BLOCKED') else 'PENDING'
        add(name,'数值细化 '+name,status,'results/m4/convergence_checks.json','预先登记的工程阈值；不是GCI或实验精度')
    sensitivity=read(OUT/'sensitivity_checks.json') or {}
    add('sensitivity','相同输入的安装接触/冷却范围计算',
        'PASS' if sensitivity.get('status')=='ACTUAL_SERIES_COMPLETE' else 'PENDING',
        'results/m4/sensitivity_checks.json','只扫安装链TCC与对流h；内部绕组接触、油膜、冷却体温及材料方向性未全面覆盖')
    for name in PATH_CASES:
        p=STUDIES/name;contact=read(p/'contact_output_audit.json');paths=read(p/'heat_path_checks.json')
        status='PASS' if contact and paths and contact['status'].startswith('PASS') and paths['status'].startswith('PASS') else 'BLOCKED' if paths and paths['status'].startswith('BLOCKED') else 'PENDING'
        add('paths_'+name,'32对连接覆盖/油液/电驱子控制体 '+name,status,
            'results/m4/studies/'+name+'/heat_path_checks.json',
            '有符号功率、净积分与正向积分分开；不把串联轴承截面重复加总')
    matched=read(OUT/'source_mask_comparison_checks.json') or {}
    add('matched_sources','相同网格时序的C-A制动附加响应',
        'PASS' if matched.get('status')=='PASS_MATCHED_SOURCE_MASK_INPUTS' else 'PENDING',
        'results/m4/source_mask_comparison_checks.json','区域最大值之差不等于逐点温差最大值')
    add('M2_compare','M2热容与首次制动比较','PASS' if (OUT/'M2_M4_capacity_comparison.csv').exists() and (OUT/'M2_M4_first_brake_comparison.csv').exists() else 'PENDING',
        'results/m4/M2_M4_first_brake_comparison.csv','边界、热容和拓扑不同；不是样机验证或降温效果认证')
    packages=read(OUT/'model_input/native_input_packages.json') or {}
    required=[CASES[k] for k in ['A','B','C','D']]
    add('inputs_archive','四个生产候选原生输入压缩包与校验和',
        'PASS' if all(n in packages for n in required) else 'PENDING',
        'results/m4/model_input/native_input_packages.json',
        '大容量RTH/WBPJ/VF仅本地留存及哈希，不声称已作远程大文件归档')
    doc=read(OUT/'document_checks.json') or {}
    hashes=doc.get('sha256',{})
    current=bool(hashes) and all((ROOT/'reports'/('M4_report.'+ext)).exists() and hashlib.sha256((ROOT/'reports'/('M4_report.'+ext)).read_bytes()).hexdigest()==digest for ext,digest in hashes.items())
    add('reports','MD/Word/PDF、可编辑公式与逐页视觉检查',
        'PASS' if current and doc.get('visual_inspection')=='PASS' else 'PENDING',
        'results/m4/document_checks.json','正文更新后旧文档哈希自动失效，不能沿用旧视觉通过记录')
    frozen=['cad/m3_helical','scripts/m3_helical','results/m3_helical','scripts/m0','scripts/m1','scripts/m2','results/m0','results/m1','results/m2']
    changed=subprocess.check_output(['git','diff','M3-v1.0','--name-only','--',*frozen],cwd=ROOT,text=True).strip()
    add('frozen','M0–M3固定研究模型及结果未覆盖','PASS' if not changed else 'BLOCKED',
        'git diff M3-v1.0 -- archived source/CAD/results',changed)
    blockers=[r['id'] for r in items if r['status']=='BLOCKED']
    pending=[r['id'] for r in items if r['status']=='PENDING']
    status='BLOCKED_NUMERICAL_ITEMS' if blockers else 'PARTIAL' if pending else 'READY_FOR_LIMITED_CONCEPT_REVIEW'
    limitations=[
        '所有温度均为S3概念预测；实际温度标定仍BLOCKED，不属于本轮数值通过的内容。',
        '真实材料牌号、绕组复合/铁心方向性、温变、热接触、油膜及实际冷却未知。',
        '只含部分辐射面与开口环境；未求解制动热空气回流，不能排序真实总成全部传热路径。',
        '固定90/10盘片热量分配，无移动摩擦接触/闪温；约400°C摩擦片预测不代表测量或安全认证。',
        '首周期/预热窗口不是六周期耐久峰值；高负载预热是给定热负荷。',
        '电机内部损耗真实标定PARTIAL；斜齿损耗、空载拖曳、搅油与温度反馈未重新标定。',
        '未经研究者批准不合并M4、不创建M4-v1.0、不进入M5。']
    result=dict(status=status,generated_at=datetime.now().astimezone().isoformat(timespec='seconds'),
        evidence_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        blockers=blockers,pending=pending,items=items,limitations=limitations,
        acceptance='RESEARCHER_REVIEW_PENDING')
    (OUT/'acceptance_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# M4 Case0阶段验收检查表','', '**当前状态：'+status+'；研究者尚未验收。**','',
        '本表依据实际完成回执生成。PASS只对应列明的概念数值检查；真实标定、机械认证和全部工况适用性不包含在内。','',
        '| 项目 | 状态 | 证据 |','|---|---|---|']
    for r in items:lines.append('| '+r['item']+' | '+r['status']+' | '+r['evidence']+' |')
    lines+=['','## 保留限制','']+['- '+x for x in limitations]
    lines+=['','生成时间：'+result['generated_at']+'；证据基于 '+result['evidence_head']+' 及本轮未提交更新。完整检查解释见 results/m4/acceptance_checks.json。','']
    (ROOT/'reports/M4_ACCEPTANCE_CHECKLIST.md').write_text('\n'.join(lines),encoding='utf-8')
    print(status,'BLOCKED',blockers,'PENDING',pending)

if __name__=='__main__':main()
