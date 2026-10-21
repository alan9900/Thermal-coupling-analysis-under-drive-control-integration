import os,json,traceback,time
RUN=r'E:\ansys_runs\m4_case0_20261021'
def dump(n,x):
    with open(os.path.join(RUN,n),'w') as f:json.dump(x,f,indent=2)
try:
    model=ExtAPI.DataModel.Project.Model
    execfile(os.path.join(RUN,'mechanical_mesh_repair.py'))
    analysis=model.Analyses[0]
    for b in model.Geometry.GetChildren(DataModelObjectCategory.Body,True):
        if b.Suppressed:continue
        ns=model.AddNamedSelection();ns.Name='m4_'+b.Name.split('|')[0]
        s=ExtAPI.SelectionManager.CreateSelectionInfo(SelectionTypeEnum.GeometryEntities);s.Ids=[b.GetGeoBody().Id]
        ns.Location=s;ns.SendToSolver=True
    analysis.WriteInputFile(os.path.join(RUN,'pilot_ds.dat'))
    assert os.path.isfile(os.path.join(RUN,'pilot_ds.dat')),'BLOCKED: input generation failed'
    analysis.Solution.Solve(True)
    dump('pilot_solve_state.json',{'state':str(analysis.Solution.ObjectState),'working_dir':analysis.WorkingDir,'result_file':analysis.ResultFileName})
    assert str(analysis.Solution.ObjectState)=='Solved','BLOCKED: solver did not report Solved'
    analysis.Solution.EvaluateAllResults()
    temp=analysis.Solution.GetChildren(DataModelObjectCategory.Temperature,True)[0];temp.Activate()
    ExtAPI.Graphics.Camera.SetFit();ExtAPI.Graphics.ExportImage(os.path.join(RUN,'DIAGNOSTIC_temperature_NOT_VALIDATED.png'))
    dump('pilot_temperature.json',{'minimum':str(temp.Minimum),'maximum':str(temp.Maximum),'average':str(temp.Average),'status':'DIAGNOSTIC_NO_ENERGY_OR_CONVERGENCE_ACCEPTANCE'})
except:
    dump('resume_failure.json',{'traceback':traceback.format_exc(),'messages':[{'text':m.DisplayString,'severity':str(m.Severity)} for m in ExtAPI.Application.Messages]})
    raise
