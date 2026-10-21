# Inspect every body; a non-throwing GenerateMesh is NOT proof of success.
import os,json,traceback,time
RUN=r'E:\ansys_runs\m4_case0_20261021'
def dump(name,x):
    with open(os.path.join(RUN,name),'w') as f:json.dump(x,f,indent=2)
def body_counts():
    data=ExtAPI.DataModel.MeshDataByName('Global');rows=[]
    for b in Model.Geometry.GetChildren(DataModelObjectCategory.Body,True):
        if b.Suppressed:continue
        r=data.MeshRegionById(b.GetGeoBody().Id)
        rows.append({'name':b.Name,'id':b.GetGeoBody().Id,'nodes':len(r.NodeIds),'elements':len(r.ElementIds),'state':str(b.ObjectState)})
    return rows
try:
    Model=ExtAPI.DataModel.Project.Model
    dump('mesh_previous_body_counts.json',{'state':str(Model.Mesh.ObjectState),'bodies':body_counts()})
    dump('mechanical_messages_before.json',[str(m) for m in ExtAPI.Application.Messages])
    failed=[r for r in body_counts() if r['elements']==0 or r['state']!='Meshed']
    if failed:
        ids=[r['id'] for r in failed]
        sel=ExtAPI.SelectionManager.CreateSelectionInfo(SelectionTypeEnum.GeometryEntities);sel.Ids=ids
        method=Model.Mesh.AddAutomaticMethod();method.Location=sel
        method.Method=MethodType.AllTriAllTet
        method.Algorithm=MeshMethodAlgorithm.PatchIndependent
        method.MaximumElementSize=Quantity('4 [mm]')
        method.MinimumSizeLimit=Quantity('0.5 [mm]')
    Model.Mesh.ElementSize=Quantity('10 [mm]')
    dump('mesh_repair_started.json',{'time':time.time(),'original_failed':failed})
    Model.Mesh.GenerateMesh()
    rows=body_counts();state=str(Model.Mesh.ObjectState)
    data=ExtAPI.DataModel.MeshDataByName('Global')
    dump('mesh_repair_audit.json',{'state':state,'nodes':data.NodeCount,'elements':data.ElementCount,'body_counts':rows,
        'quality_min':str(Model.Mesh.Minimum),'quality_mean':str(Model.Mesh.Average),
        'all_active_bodies_have_elements':all(r['elements']>0 for r in rows)})
    dump('mechanical_messages_after.json',[str(m) for m in ExtAPI.Application.Messages])
    assert all(r['elements']>0 and r['state']=='Meshed' for r in rows), 'BLOCKED: active body mesh missing or rejected'
    assert 'Error' not in state, 'BLOCKED: mesh state error'
    Model.Mesh.Activate();ExtAPI.Graphics.Camera.SetFit()
    ExtAPI.Graphics.ExportImage(os.path.join(RUN,'case0_mesh_repair.png'))
except:
    dump('mesh_repair_failure.json',{'status':'FAILED','traceback':traceback.format_exc()})
    raise
