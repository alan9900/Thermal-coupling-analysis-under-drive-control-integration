"""Independent lightweight material-region check, only on completed native RTH."""
import argparse,hashlib,json,os
from native_materials import validate_material_regions
from dpf_regions import solid_regions
from export_native_brake import ROOT,RUN

def main():
    p=argparse.ArgumentParser();p.add_argument('studies',nargs='+');a=p.parse_args()
    configpath=ROOT/'configs/m4_case0.json';config=json.loads(configpath.read_text(encoding='utf-8-sig'))
    os.environ['DPF_DEFAULT_GRPC_MODE']='insecure'
    from ansys.dpf import core as dpf
    server=dpf.start_local_server(ansys_path='E:/Program Files/ANSYS Inc/v241',config=dpf.AvailableServerConfigs.GrpcServer,ip='127.0.0.1')
    rows={}
    try:
        for name in a.studies:
            proof=ROOT/'results/m4/studies'/name/'native_archive_manifest.json';assert proof.exists()
            folder=RUN/'studies'/name;model=dpf.Model(str(folder/'study.rth'),server=server)
            records=validate_material_regions(model.metadata.meshed_region,solid_regions(model),folder/'study.dat',config)
            assert len(records)==28
            rows[name]=dict(status='PASS_NATIVE_REGION_MATERIAL_CONSTANTS',regions=records,
                native_input_sha256=json.loads(proof.read_text(encoding='utf-8-sig'))['study.dat']['sha256'])
            print(name,'28 regions: native DENS/C/KXX match',flush=True)
    finally:server.shutdown()
    out=ROOT/'results/m4/native_material_region_checks.json'
    previous=json.loads(out.read_text(encoding='utf-8-sig')) if out.exists() else {}
    previous.update(rows)
    out.write_text(json.dumps(previous,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
