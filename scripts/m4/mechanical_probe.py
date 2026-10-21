# IronPython 2.7 in ANSYS Mechanical 2024 R1; actual import/mesh probe.
import os,json,traceback,time
RUN=r'E:\ansys_runs\m4_case0_20261021'
def dump(name,value):
    with open(os.path.join(RUN,name),'w') as f:json.dump(value,f,indent=2)
try:
    model=ExtAPI.DataModel.Project.Model
    ExtAPI.Application.ActiveUnitSystem=MechanicalUnitSystem.StandardMKS
    dump('mechanical_started.json',{'status':'MECHANICAL_SCRIPT_STARTED','time':time.time()})
    model.AddTransientThermalAnalysis()
    imp=model.GeometryImportGroup.AddGeometryImport()
    pref=Ansys.ACT.Mechanical.Utilities.GeometryImportPreferences()
    pref.ProcessNamedSelections=True
    imp.Import(os.path.join(RUN,'Case0_d50_helical_thermal.step'),GeometryImportPreference.Format.Automatic,pref)
    bodies=model.Geometry.GetChildren(DataModelObjectCategory.Body,True)
    rows=[]
    for b in bodies:
        gb=b.GetGeoBody()
        rows.append({'name':b.Name,'object_id':b.ObjectId,'geo_id':gb.Id,'volume':str(b.Volume),'material':str(b.Material),
                     'faces':len(gb.Faces),'edges':len(gb.Edges)})
    dump('import_audit.json',{'status':'STEP_IMPORTED_ACTUALLY','body_count':len(rows),'bodies':rows})
    # Workbench owns the database; launch_probe.wbjn saves the project.
    dump('probe_complete.json',{'status':'IMPORT_PASS','body_count':len(rows),'mesh':'NOT EXECUTED','solve':'NOT EXECUTED'})
except:
    dump('probe_failure.json',{'status':'FAILED','traceback':traceback.format_exc()})
    raise
