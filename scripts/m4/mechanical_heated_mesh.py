# Workbench-hosted mesh changes only; accepted M3 CAD/thermal scopes unchanged.
import os,json,traceback
RUN=r'E:\ansys_runs\m4_case0_20261021'
def dump(path,value):
    with open(path,'w') as f:json.dump(value,f,indent=2)
try:
    model=ExtAPI.DataModel.Project.Model;analysis=model.Analyses[0]
    controls=dict((c.Name,c) for c in model.Mesh.GetChildren(DataModelObjectCategory.Sizing,True))
    controls['M4_disc_flux_surface_refinement'].ElementSize=Quantity('2 [mm]')
    controls['M4_pad_flux_surface_refinement'].ElementSize=Quantity('3 [mm]')
    controls['M4_pad_explicit_normal_layers'].NumberOfDivisions=12
    methods=model.Mesh.GetChildren(DataModelObjectCategory.AutomaticMethod,True)
    for h in [14,7]:
        folder=os.path.join(RUN,'mesh_variants','mesh_global'+str(h))
        assert not os.path.exists(folder),'Never overwrite a mesh attempt'
        os.makedirs(folder)
        model.Mesh.ElementSize=Quantity(str(h)+' [mm]')
        changed=[]
        # The adapter previously needed patch-independent tetrahedra. Scale
        # that method's maximum size too; preserve its 1.5mm feature floor.
        for method in methods:
            if 'PatchIndependent' in str(method.Algorithm):
                method.MaximumElementSize=Quantity(str(.8*h)+' [mm]')
                changed.append(method.Name)
        model.Mesh.GenerateMesh();data=ExtAPI.DataModel.MeshDataByName('Global');rows=[]
        for b in model.Geometry.GetChildren(DataModelObjectCategory.Body,True):
            if b.Suppressed:continue
            region=data.MeshRegionById(b.GetGeoBody().Id)
            rows.append(dict(name=b.Name,elements=len(region.ElementIds),nodes=len(region.NodeIds),state=str(b.ObjectState)))
        record=dict(state=str(model.Mesh.ObjectState),nodes=data.NodeCount,elements=data.ElementCount,body_counts=rows,
            global_size_mm=h,adapter_max_mm=.8*h,adapter_methods=changed,minimum_feature_size_mm=1.5,
            disc_face_mm=2,pad_tangential_mm=3,pad_normal_layers=12,
            quality_min=str(model.Mesh.Minimum),quality_mean=str(model.Mesh.Average))
        dump(os.path.join(folder,'mesh_audit.json'),record)
        assert str(model.Mesh.ObjectState)=='Solved' and all(r['elements']>0 and r['state']=='Meshed' for r in rows)
        analysis.WriteInputFile(os.path.join(folder,'mechanical_ds.dat'))
        model.Mesh.Activate();ExtAPI.Graphics.Camera.SetFit()
        ExtAPI.Graphics.ExportImage(os.path.join(folder,'actual_mesh.png'))
        dump(os.path.join(folder,'input_export_complete.json'),dict(status='ACTUAL_MESH_AND_INPUT_EXPORTED',solve='NOT EXECUTED'))
except:
    dump(os.path.join(RUN,'heated_mesh_failure.json'),dict(traceback=traceback.format_exc()))
    raise
