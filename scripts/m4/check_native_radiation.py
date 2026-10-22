"""Actual native radiosity benchmark: Kelvin offset, signs and heat-rate units."""
import csv,hashlib,json,re,shutil
from export_native_brake import ROOT,RUN

def main():
    folder=RUN/'radiation_benchmark_retry1'
    log=(folder/'check.out').read_text(encoding='utf-8-sig',errors='replace')
    assert 'RUN COMPLETED' in log
    errors=int(re.search(r'NUMBER OF ERROR\s+MESSAGES ENCOUNTERED=\s+(\d+)',log)[1]);assert errors==0
    rows=[]
    for row in csv.reader((folder/'radiation_check.csv').open()):
        prescribed,surface,reaction,net=map(float,row)
        analytic=.8*5.669e-8*.01*((surface+273.15)**4-(25+273.15)**4)
        assert abs(net-analytic)<1e-5 and abs(net-reaction)<1e-5
        assert net>0 if prescribed==100 else net<0 if prescribed==0 else abs(net)<1e-5
        rows.append(dict(prescribed_node_C=prescribed,native_surface_C=surface,
            reaction_input_W=reaction,native_radiation_out_W=net,analytic_radiation_out_W=analytic,
            absolute_difference_W=abs(net-analytic)))
    assert len(rows)==3
    out=ROOT/'results/m4/radiation_benchmark';out.mkdir(exist_ok=True)
    files={}
    for name in ['check.dat','check.out','check.rth','radiation_check.csv']:
        path=folder/name;shutil.copy2(path,out/name)
        files[name]=dict(bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    receipt=dict(status='PASS_NATIVE_RADIOSITY_UNITS_AND_DIRECTION',solver='MAPDL 2024 R1',
        cases=rows,absolute_tolerance_W=1e-5,errors=errors,
        warnings=int(re.search(r'NUMBER OF WARNING\s+MESSAGES ENCOUNTERED=\s+(\d+)',log)[1]),
        files=files,limitations='Single exposed surface to 25C space node, no geometric obstruction. Does not validate Case0 view factors, complete shielding or actual emissivities. Failed high-conductivity/over-tight-reference attempt preserved separately.')
    (ROOT/'results/m4/native_radiation_checks.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(receipt['status'], 'max analytic error W',max(r['absolute_difference_W'] for r in rows))

if __name__=='__main__':main()
