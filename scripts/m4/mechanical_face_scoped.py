# Explicit finite face scopes; accepted geometry and mesh unchanged.
import os,json,traceback,time
RUN=r'E:\ansys_runs\m4_case0_20261021'
def dump(n,x):
    with open(os.path.join(RUN,n),'w') as f:json.dump(x,f,indent=2)
def sel(ids):
    s=ExtAPI.SelectionManager.CreateSelectionInfo(SelectionTypeEnum.GeometryEntities);s.Ids=ids;return s
try:
    model=ExtAPI.DataModel.Project.Model;analysis=model.Analyses[0]
    with open(os.path.join(RUN,'contact_scope_resolved.json')) as f:scopes=json.load(f)
    assert scopes['status']=='PASS_GEOMETRIC_SCOPES_ONLY'
    for c in list(model.Connections.GetChildren(DataModelObjectCategory.ContactRegion,True)):c.Delete()
    for r in scopes['contacts']:
        c=model.Connections.AddContactRegion()
        c.SourceLocation=sel(r['source_face_ids']);c.TargetLocation=sel(r['target_face_ids'])
        c.ContactType=ContactType.Bonded
        c.AutomaticThermalConductance=False;c.ThermalConductanceValue=Quantity(str(r['h_W_m2K'])+' [W m^-2 K^-1]')
        c.PinballRegion=ContactPinballType.Radius;c.PinballRadius=Quantity('20 [mm]' if r['source']=='oil_inventory' else '2 [mm]')
        c.Name='S3_'+r['source']+'_to_'+r['target']
    # Do not cool mounting-contact faces to ambient at the same time.
    contact_faces=set(i for r in scopes['contacts'] for k in ['source_face_ids','target_face_ids'] for i in r[k])
    for cv in analysis.GetChildren(DataModelObjectCategory.Convection,True):
        if cv.Name=='S3_finite_ambient':
            ids=[i for i in cv.Location.Ids if i not in contact_faces]
            assert ids;cv.Location=sel(ids)
    # Export native FE face nodes for independent physical surface integration.
    data=ExtAPI.DataModel.MeshDataByName('Global');regions={}
    for bc in analysis.Children:
        try:ids=list(bc.Location.Ids)
        except:continue
        if not ids:continue
        regions[bc.Name]=[{'face_id':i,'node_ids':list(data.MeshRegionById(i).NodeIds)} for i in ids]
    dump('face_scoped_FE_boundary_nodes.json',regions)
    analysis.Name='M4_Case0_B_face_scoped_CONCEPT_NOT_CALIBRATED'
    configs=list(ExtAPI.Application.SolveConfigurations);conf=configs[0]
    conf.SolveProcessSettings.MaxNumberOfCores=2;conf.SolveProcessSettings.DistributeSolution=False
    analysis.WriteInputFile(os.path.join(RUN,'face_scoped_ds.dat'))
    dump('face_scoped_started.json',{'time':time.time(),'contact_pairs':len(scopes['contacts']),
        'classification':'S3_ENGINEERING','energy_balance':'PENDING','mesh_independence':'PENDING'})
    analysis.Solution.Solve(True,conf)
    dump('face_scoped_state.json',{'state':str(analysis.Solution.ObjectState),'result_file':analysis.ResultFileName,'working_dir':analysis.WorkingDir})
    assert str(analysis.Solution.ObjectState)=='Solved'
    t=analysis.Solution.AddTemperature();t.Name='M4_temperature_field_S3_not_calibrated'
    analysis.Solution.EvaluateAllResults();t.Activate()
    ExtAPI.Graphics.Camera.SetFit();ExtAPI.Graphics.ExportImage(os.path.join(RUN,'FACE_SCOPED_temperature_NOT_VALIDATED.png'))
    dump('face_scoped_temperature.json',{'minimum':str(t.Minimum),'maximum':str(t.Maximum),'average':str(t.Average),'validation':'PENDING'})
except:
    dump('face_scoped_failure.json',{'traceback':traceback.format_exc(),'messages':[m.DisplayString for m in ExtAPI.Application.Messages]})
    raise
