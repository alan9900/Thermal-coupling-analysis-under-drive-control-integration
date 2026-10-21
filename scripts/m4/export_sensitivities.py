"""One-factor uncertainty studies; no calibrated parameter substitution.

Keep the same heat-source histories and mesh. Vary the solid mounting-chain
TCC independently of a jointly specified external/jacket cooling scenario.
Oil-film and equivalent motor-gap links retain their stated S3 values.
"""
import argparse,hashlib,json,re,shutil
from pathlib import Path
from export_native_brake import ROOT,RUN

def main():
    ap=argparse.ArgumentParser();ap.add_argument('base');ap.add_argument('--prefix',default='C_sensitivity')
    a=ap.parse_args();base=RUN/'studies'/a.base;text=(base/'study.dat').read_text()
    pairs={}
    for match in re.finditer(r'Create Contact "(S3_[^"]+)"[^\n]*\n[\s\S]*?\*set,tid,(\d+)\s*\n\*set,cid,(\d+)',text):
        pairs[match[1]]=(int(match[2]),int(match[3]))
    assert len(pairs)==32
    # All nominal metal mounting contacts, but not fluid/gap-equivalent links.
    selected={name:ids for name,ids in pairs.items() if not any(s in name for s in ['oil_inventory','motor_winding','motor_stator','motor_rotor_other'])}
    assert selected and 'S3_brake_disc_hat_to_disc_hub' in selected
    insertion=text.index('! Same actual Mechanical FE mesh/contacts;')
    for label,contact_h,external_h,jacket_h in [('contact_low',100,None,None),('contact_high',10000,None,None),
            ('cooling_low',None,5,100),('cooling_high',None,40,800)]:
        folder=RUN/'studies'/(a.prefix+'_'+label);folder.mkdir(exist_ok=False)
        commands=['! S3 uncertainty case, source powers and time schedule unchanged']
        if contact_h:
            for ids in selected.values():
                for rid in ids:commands.append('rmodif,%d,14,%g'%(rid,contact_h))
        else:
            for typ,h in [(99,external_h),(100,jacket_h)]:
                commands.extend(['allsel','esel,s,type,,%d'%typ,'nsle','sf,all,conv,%g,25'%h])
        commands.append('allsel')
        variant=text[:insertion]+'\n'+'\n'.join(commands)+'\n'+text[insertion:]
        (folder/'study.dat').write_text(variant)
        shutil.copy2(base/'source_intervals.csv',folder/'source_intervals.csv')
        meta=json.loads((base/'study_settings.json').read_text());meta.update(
            case=meta['case']+'_'+label,sensitivity_base=a.base,classification='S3_UNCERTAINTY_NOT_CALIBRATED',
            variation=dict(solid_mounting_TCC_W_m2K=contact_h,external_h_W_m2K=external_h,jacket_h_W_m2K=jacket_h),
            varied_contact_pairs=selected if contact_h else {},
            capacity_weights=str(ROOT/'results/m4/studies'/folder.name/'FE_capacity_weights.npz'),status='GENERATED_NOT_EXECUTED',
            input_sha256=hashlib.sha256(variant.encode()).hexdigest())
        (folder/'study_settings.json').write_text(json.dumps(meta,indent=2)+'\n');print(folder)

if __name__=='__main__':main()
