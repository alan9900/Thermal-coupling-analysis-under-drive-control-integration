import os,json,traceback,time
RUN=r'E:\ansys_runs\m4_case0_20261021'
def dump(n,x):
    with open(os.path.join(RUN,n),'w') as f:json.dump(x,f,indent=2)
try:
    model=ExtAPI.DataModel.Project.Model
    if str(model.Mesh.ObjectState)!='Solved':execfile(os.path.join(RUN,'mechanical_mesh_repair.py'))
    analysis=model.Analyses[0]
    for ns in list(model.NamedSelections.Children):
        if ns.Name.startswith('m4_'):ns.Delete()
    by={}
    for b in model.Geometry.GetChildren(DataModelObjectCategory.Body,True):
        if not b.Suppressed:by.setdefault(b.Name.split('|')[0],[]).append(b.GetGeoBody().Id)
    for name,ids in by.items():
        ns=model.AddNamedSelection();ns.Name='m4_'+name
        s=ExtAPI.SelectionManager.CreateSelectionInfo(SelectionTypeEnum.GeometryEntities);s.Ids=ids
        ns.Location=s;ns.SendToSolver=True
    with open(os.path.join(RUN,'pilot_source.json')) as f:p=json.load(f)
    for hf in analysis.GetChildren(DataModelObjectCategory.HeatFlow,True):
        key='disc_W' if 'brake_disc_hat' in hf.Name else 'pad_W'
        hf.Magnitude.Inputs[0].DiscreteValues=[Quantity(str(x)+' [s]') for x in p['time_s']]
        hf.Magnitude.Output.DiscreteValues=[Quantity(str(x*.5)+' [W]') for x in p[key]]
    settings=analysis.AnalysisSettings;ends=p['brake_bin_end_s']+[p['duration_s']]
    settings.NumberOfSteps=len(ends);prev=0
    for j,end in enumerate(ends):
        settings.CurrentStepNumber=j+1;settings.StepEndTime=Quantity(str(end)+' [s]')
        settings.AutomaticTimeStepping=AutomaticTimeStepping.Off
        settings.TimeStep=Quantity(str(end-prev if j<len(ends)-1 else 1)+' [s]');prev=end
    # Actual cylindrical water-jacket faces only; exclude the stator fit face.
    jacket=[]
    for b in model.Geometry.GetChildren(DataModelObjectCategory.Body,True):
        if b.Name.split('|')[0]!='motor_case':continue
        for f in b.GetGeoBody().Faces:
            if str(f.SurfaceType)=='GeoSurfaceCylinder' and .08<f.Area*1e-6<.10:jacket.append(f.Id)
    assert len(jacket)==2
    for cv in analysis.GetChildren(DataModelObjectCategory.Convection,True):
        if cv.Name=='S3_finite_jacket':
            s=ExtAPI.SelectionManager.CreateSelectionInfo(SelectionTypeEnum.GeometryEntities);s.Ids=jacket;cv.Location=s
    configurations=list(ExtAPI.Application.SolveConfigurations)
    dump('available_solve_configurations.json',[c.Name for c in configurations])
    assert configurations,'No local solve configuration'
    conf=configurations[0]
    conf.SolveProcessSettings.MaxNumberOfCores=2;conf.SolveProcessSettings.DistributeSolution=False
    dump('pilot_corrected_setup.json',{'load_step_end_s':ends,'jacket_face_ids':jacket,'cores':2,'distributed':False,'source_energy_J':p['source_energy_J']})
    analysis.WriteInputFile(os.path.join(RUN,'pilot_ds.dat'))
    assert os.path.isfile(os.path.join(RUN,'pilot_ds.dat')),'BLOCKED: input generation failed'
    analysis.Solution.Solve(True,conf)
    dump('pilot_solve_state.json',{'state':str(analysis.Solution.ObjectState),'working_dir':analysis.WorkingDir,'result_file':analysis.ResultFileName})
    assert str(analysis.Solution.ObjectState)=='Solved','BLOCKED: solver did not report Solved'
    analysis.Solution.EvaluateAllResults()
    temp=analysis.Solution.GetChildren(DataModelObjectCategory.Temperature,True)[0];temp.Activate()
    ExtAPI.Graphics.Camera.SetFit();ExtAPI.Graphics.ExportImage(os.path.join(RUN,'DIAGNOSTIC_temperature_NOT_VALIDATED.png'))
    dump('pilot_temperature.json',{'minimum':str(temp.Minimum),'maximum':str(temp.Maximum),'average':str(temp.Average),'status':'DIAGNOSTIC_NO_ENERGY_OR_CONVERGENCE_ACCEPTANCE'})
except:
    dump('resume_failure.json',{'traceback':traceback.format_exc(),'messages':[{'text':m.DisplayString,'severity':str(m.Severity)} for m in ExtAPI.Application.Messages]})
    raise
