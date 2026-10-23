"""Check native APDL constants and actual RTH region material IDs."""
import re
import numpy as np

def validate_material_regions(mesh,regions,native_input,config):
    constants={}
    with native_input.open(encoding='utf-8-sig') as f:
        for line in f:
            match=re.match(r'MP,(DENS|C|KXX),(\d+),([^,\s]+)',line,re.I)
            if match:
                prop,mid,value=match.groups()
                constants.setdefault(int(mid),{})[prop.upper()]=float(value.replace('D','E').replace('d','e'))
    field=mesh.property_field('mat')
    mids=dict(zip(map(int,field.scoping.ids),map(int,field.data)))
    records={}
    for name,ids in regions.items():
        expected=config['materials'][config['body_materials'][name[3:].lower()]]
        unique=sorted({mids[int(e)] for e in ids})
        for mid in unique:
            for prop,key in [('DENS','rho_kg_m3'),('C','cp_J_kgK'),('KXX','k_W_mK')]:
                if not np.isclose(constants[mid][prop],expected[key],rtol=1e-11,atol=1e-10):
                    raise ValueError('Native material/config mismatch: '+name+' '+prop)
        records[name]=dict(material_ids=unique,constants={str(mid):constants[mid] for mid in unique})
    return records
