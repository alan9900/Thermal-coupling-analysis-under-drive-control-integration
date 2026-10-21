"""Resolve Mechanical body named selections without assuming nodal scoping."""
import numpy as np

def body_element_ids(model, name):
    from ansys.dpf import core as dpf
    scope = model.metadata.named_selection(name)
    if str(scope.location) == 'Elemental':
        return np.asarray(scope.ids, dtype=int)
    if str(scope.location) == 'Nodal':
        scope = dpf.operators.scoping.transpose(
            mesh_scoping=scope, meshed_region=model.metadata.meshed_region,
            inclusive=0, server=model._server).outputs.mesh_scoping()
        return np.asarray(scope.ids, dtype=int)
    raise ValueError('Unsupported body selection location: '+str(scope.location))

def solid_regions(model):
    mesh=model.metadata.meshed_region
    prop=mesh.property_field('apdl_element_type')
    solid=set(int(i) for i,t in zip(prop.scoping.ids,prop.data) if int(t)==278)
    regions={}
    for name in model.metadata.available_named_selections:
        if name.startswith('M4_'):
            ids=sorted(solid.intersection(body_element_ids(model,name)))
            if not ids:raise ValueError('Empty solid body region '+name)
            regions[name]=np.asarray(ids,dtype=int)
    assigned=[int(i) for ids in regions.values() for i in ids]
    if len(assigned)!=len(set(assigned)) or set(assigned)!=solid:
        raise ValueError('Solid body regions overlap or omit elements')
    return regions
