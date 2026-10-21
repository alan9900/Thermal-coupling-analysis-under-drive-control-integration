# Actual Workbench-hosted Mechanical continuation: audit and mesh, no solve.
import os,json,traceback,time
RUN=r'E:\ansys_runs\m4_case0_20261021'
def dump(name,value):
    with open(os.path.join(RUN,name),'w') as f:json.dump(value,f,indent=2)
try:
    model=ExtAPI.DataModel.Project.Model
    ExtAPI.Application.ActiveUnitSystem=MechanicalUnitSystem.StandardMKS
    model.Materials.Import(os.path.join(RUN,'M4_materials.xml'))
    with open(os.path.join(RUN,'m4_case0.json')) as f:config=json.load(f)
    keep=['motor_case','motor_stator','motor_winding','motor_rotor_other','motor_rotor_shaft','motor_input_coupling','motor_gear_adapter',
          'input_shaft','intermediate_shaft','output_shaft','stage1_gear','stage2_gear','gear_case_front','gear_case_rear',
          'oil_inventory','brake_disc_hat','disc_hub','hub_removable_sleeve','pad_near','pad_far','caliper','caliper_reaction_bracket']
    for ax in ['input','intermediate','output']:
        for k in [1,2]:keep.append(ax+'_bearing_'+str(k))
    bodies=model.Geometry.GetChildren(DataModelObjectCategory.Body,True)
    audit=[];faces=[]
    for b in bodies:
        name=b.Name.split('|')[0];gb=b.GetGeoBody();b.Suppressed=name not in keep
        if name in keep:b.Material='M4_S3_'+config['body_materials'][name]
        row={'name':name,'geo_id':gb.Id,'suppressed':b.Suppressed,'volume':str(b.Volume)}
        for key in ['Volume','Centroid','BoundingBox']:
            try:row['geo_'+key]=str(getattr(gb,key))
            except:pass
        audit.append(row)
        if not b.Suppressed:
            for f in gb.Faces:
                faces.append({'body':name,'id':f.Id,'area_m2':f.Area,'centroid':list(f.Centroid),'surface_type':str(f.SurfaceType)})
    dump('body_mesh_audit.json',audit);dump('face_audit.json',faces)
    mesh=model.Mesh
    mesh.ElementOrder=ElementOrder.Linear
    mesh.ElementSize=Quantity('15 [mm]')
    dump('mesh_started.json',{'time':time.time(),'active_bodies':sum(not r['suppressed'] for r in audit)})
    mesh.GenerateMesh()
    data=ExtAPI.DataModel.MeshDataByName('Global')
    metrics={'status':'MESH_EXECUTED','nodes':data.NodeCount,'elements':data.ElementCount,'element_size_mm':15,'order':'linear'}
    try:
        mesh.MeshMetric=MeshMetricType.ElementQuality
        metrics['quality_min']=str(mesh.Minimum);metrics['quality_mean']=str(mesh.Average)
    except:metrics['quality_api_note']=traceback.format_exc()
    dump('mesh_audit.json',metrics)
    ExtAPI.Graphics.Camera.SetFit()
    ExtAPI.Graphics.ExportImage(os.path.join(RUN,'case0_mesh.png'))
    dump('mesh_complete.json',{'status':'MESH_COMPLETE','solve':'NOT EXECUTED'})
except:
    dump('mesh_failure.json',{'status':'FAILED','traceback':traceback.format_exc()})
    raise
