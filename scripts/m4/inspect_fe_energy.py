"""Discover actual FE topology and DPF quadrature capabilities (no PASS claim)."""
import os,json,sys,collections
from pathlib import Path
os.environ['DPF_DEFAULT_GRPC_MODE']='insecure'
from ansys.dpf import core as dpf
s=dpf.start_local_server(ansys_path='E:/Program Files/ANSYS Inc/v241',config=dpf.AvailableServerConfigs.GrpcServer,ip='127.0.0.1')
try:
    model=dpf.Model(sys.argv[1],server=s);mesh=model.metadata.meshed_region
    print('PROPERTIES',mesh.available_property_fields)
    print('FIRST ELEMENT',mesh.elements[0])
    for name in ['apdl_element_type','mat']:
        try:
            f=mesh.property_field(name);print(name,collections.Counter(f.data).most_common(12))
        except Exception as e:print(type(e).__name__,str(e)[:250])
    try:
        op=dpf.Operator('integrate_over_elements',server=s);print(op.specification)
    except Exception as e:print('Quadrature operator unavailable:',str(e)[:250])
finally:s.shutdown()
