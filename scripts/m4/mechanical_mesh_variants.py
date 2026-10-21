# M4 thermal mesh verification only; accepted CAD and mechanical layout unchanged.
import os,json,traceback
RUN=r'E:\ansys_runs\m4_case0_20261021'
def dump(path,x):
    with open(path,'w') as f:json.dump(x,f,indent=2)
def sel(ids):
    s=ExtAPI.SelectionManager.CreateSelectionInfo(SelectionTypeEnum.GeometryEntities);s.Ids=ids;return s
try:
    model=ExtAPI.DataModel.Project.Model;analysis=model.Analyses[0]
    # Resolve actual friction-face geometry scopes already audited in this model.
    disc=[];pads=[]
    for hf in analysis.GetChildren(DataModelObjectCategory.HeatFlow,True):
        if 'brake_disc_hat' in hf.Name:disc.extend(hf.Location.Ids)
        elif 'pad_' in hf.Name:pads.extend(hf.Location.Ids)
    assert len(set(disc))==2 and len(set(pads))==2
    controls=[];pad_edges=[]
    for b in model.Geometry.GetChildren(DataModelObjectCategory.Body,True):
        if b.Name.split('|')[0] in ['pad_near','pad_far']:
            pad_edges.extend([e.Id for e in b.GetGeoBody().Edges if abs(e.Length-8.5)<1e-4])
    assert len(pad_edges)==8,'Pad axial edges must be explicitly resolved'
    for name,ids in [('M4_disc_flux_surface_refinement',disc),('M4_pad_flux_surface_refinement',pads)]:
        c=model.Mesh.AddSizing();c.Location=sel(list(set(ids)));c.Name=name;controls.append(c)
    axial=model.Mesh.AddSizing();axial.Location=sel(pad_edges)
    axial.Type=SizingType.NumberOfDivisions;axial.Behavior=SizingBehavior.Hard
    axial.Name='M4_pad_explicit_normal_layers'
    # Uniform pad input permits fixed 3mm tangential size; refine the normal.
    for label,hd,layers in [('mesh_normal6',4,6),('mesh_normal12',2,12),('mesh_normal24',1,24)]:
        folder=os.path.join(RUN,'mesh_variants',label)
        if not os.path.isdir(folder):os.makedirs(folder)
        controls[0].ElementSize=Quantity(str(hd)+' [mm]');controls[1].ElementSize=Quantity('3 [mm]');axial.NumberOfDivisions=layers
        model.Mesh.GenerateMesh();data=ExtAPI.DataModel.MeshDataByName('Global');rows=[]
        for b in model.Geometry.GetChildren(DataModelObjectCategory.Body,True):
            if b.Suppressed:continue
            r=data.MeshRegionById(b.GetGeoBody().Id);rows.append({'name':b.Name,'state':str(b.ObjectState),'elements':len(r.ElementIds),'nodes':len(r.NodeIds)})
        audit={'state':str(model.Mesh.ObjectState),'nodes':data.NodeCount,'elements':data.ElementCount,
            'body_counts':rows,'disc_face_mm':hd,'pad_tangential_face_mm':3,'pad_normal_layers':layers,
            'pad_normal_size_mm':8.5/layers,'pad_axial_edge_ids':pad_edges,'quality_min':str(model.Mesh.Minimum),'quality_mean':str(model.Mesh.Average)}
        dump(os.path.join(folder,'mesh_audit.json'),audit)
        assert str(model.Mesh.ObjectState)=='Solved' and all(r['state']=='Meshed' and r['elements']>0 for r in rows)
        analysis.WriteInputFile(os.path.join(folder,'mechanical_ds.dat'))
        model.Mesh.Activate();ExtAPI.Graphics.Camera.SetFit();ExtAPI.Graphics.ExportImage(os.path.join(folder,'actual_mesh.png'))
        dump(os.path.join(folder,'input_export_complete.json'),{'status':'ACTUAL_MESH_AND_INPUT_EXPORTED','solve':'NOT EXECUTED'})
except:
    dump(os.path.join(RUN,'mesh_variants_failure.json'),{'traceback':traceback.format_exc(),'messages':[m.DisplayString for m in ExtAPI.Application.Messages]})
    raise
