"""Record the user-requested pause; never launch a solver or infer completion."""
import hashlib,json
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
RUN=Path('E:/ansys_runs/m4_case0_20261021/studies')
OUT=ROOT/'results/m4/attempts'
OUT.mkdir(exist_ok=True)
names=['B_normal12_rd95h_dt4_retry1','C_normal12_rd95_contact_high']
records=[]
for name in names:
    folder=RUN/name
    log=folder/'study.out'
    data=log.read_bytes() if log.exists() else b''
    tail=OUT/(name+'_user_pause_tail.txt')
    tail.write_bytes(data[-24000:])
    records.append(dict(study=name,status='STOPPED_AT_USER_REQUEST_NOT_COMPLETED',
        native_folder=str(folder),log_sha256=hashlib.sha256(data).hexdigest(),
        log_bytes=len(data),tail=str(tail.relative_to(ROOT)),
        partial_results='Retained locally; not accepted as completed production results.'))
planned=['mechanical_heated_mesh.py','run_heated_mesh.wbjn','export_zero_probe.py',
         'refine_same_source_time.py','finish_heated_verification.py']
receipt=dict(status='PARTIAL_PAUSED_AT_USER_REQUEST',
    recorded_at=datetime.now().astimezone().isoformat(timespec='seconds'),
    request='Summarize promptly; temporarily stop further research to conserve token budget.',
    stopped=records,not_executed=['C_normal12_rd95_cooling_low','C_normal12_rd95_cooling_high'],
    proposed_scripts_not_executed=['scripts/m4/'+n for n in planned],
    restrictions='No additional solves, no M4 merge/tag, no M5. Existing completed results preserved.')
(OUT/'user_requested_pause_20261022.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
report=ROOT/'reports/M4_report.md'
text=report.read_text(encoding='utf-8')
text=text.replace('**阶段状态：PARTIAL，计算与数值验证进行中。**',
    '**阶段状态：PARTIAL；按研究者2026-10-22要求暂停进一步研究，仅整理已有成果。**')
marker='## 7.1 本次暂停交接'
if marker not in text:
    note='''## 7.1 本次暂停交接

研究者要求尽快总结、暂不继续研究。已停止队列和两个尚未完成的原生求解：B 最细时间步重试、C 高接触导度。部分结果与日志保留，明确不作为完成或收敛证据；回执见 `results/m4/attempts/user_requested_pause_20261022.json`。A 中网格重试已完成并纳入本报告。B 已完成时间步1/2结果可作阶段参考，但三档时间步独立性仍未闭合。

冷却低/高两种范围计算没有执行；安装接触敏感性未形成完整低/中/高系列。内部发热工况的进一步整体网格细化、预热阶段时间步验证也未执行。新增的五个后续验证草稿脚本仅保留为 NOT EXECUTED，不属于已经验证的交付流程，详见暂停回执。

本次交付是已有结果的可追溯总结，不是M4正式完成验收。后续需研究者另行要求才恢复计算；此时不合并PR、不创建M4正式标签、不进入M5。

'''
    text=text.replace('# 8. 资料依据',note+'# 8. 资料依据')
report.write_text(text,encoding='utf-8')
print(receipt['status'])
