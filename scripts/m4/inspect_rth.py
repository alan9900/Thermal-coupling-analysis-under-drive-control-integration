"""Read-only inspection of a converged subset in a still-running RTH.
This intentionally does not mark the entire transient or its validation PASS.
"""
import os,json,sys
from pathlib import Path
os.environ['DPF_DEFAULT_GRPC_MODE']='insecure'
from ansys.dpf import core as dpf
path=Path(sys.argv[1]);root=Path(__file__).resolve().parents[2]
s=dpf.start_local_server(ansys_path='E:/Program Files/ANSYS Inc/v241',config=dpf.AvailableServerConfigs.GrpcServer,ip='127.0.0.1')
try:
    m=dpf.Model(str(path),server=s)
    ts=m.metadata.time_freq_support.time_frequencies.data
    f=m.results.temperature(time_scoping=[1]).eval()[0]
    mesh=m.metadata.meshed_region
    r=dict(status='PARTIAL_CONVERGED_SUBSTEPS_ONLY_NOT_VALIDATED',times_s=list(ts),first_step_temperature_unit=f.unit,
        first_step_min=float(f.data.min()),first_step_max=float(f.data.max()),available_results=str(m.metadata.result_info),
        named_selections=m.metadata.available_named_selections,mesh_info=str(mesh),element_types=str(mesh.property_field('eltype').data[:15]))
    (root/'results/m4/live_rth_inspection.json').write_text(json.dumps(r,indent=2)+'\n');print(r)
finally:s.shutdown()
