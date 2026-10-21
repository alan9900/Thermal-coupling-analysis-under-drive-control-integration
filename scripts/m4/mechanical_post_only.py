import os,json,traceback
RUN=r'E:\ansys_runs\m4_case0_20261021'
def dump(n,x):
    with open(os.path.join(RUN,n),'w') as f:json.dump(x,f,indent=2)
try:
    model=ExtAPI.DataModel.Project.Model;a=model.Analyses[0]
    assert str(a.Solution.ObjectState)=='Solved'
    t=a.Solution.AddTemperature();t.Name='M4_temperature_field_S3_not_calibrated'
    a.Solution.EvaluateAllResults();t.Activate();ExtAPI.Graphics.Camera.SetFit()
    ExtAPI.Graphics.ExportImage(os.path.join(RUN,'FACE_SCOPED_temperature_NOT_VALIDATED.png'))
    dump('face_scoped_temperature.json',{'minimum':str(t.Minimum),'maximum':str(t.Maximum),'average':str(t.Average),
        'solver_state':str(a.Solution.ObjectState),'validation':'Energy, mesh and time verification are separate; S3 not calibrated',
        'result_category':str(t.DataModelObjectCategory)})
except:
    dump('post_only_failure.json',{'traceback':traceback.format_exc(),'messages':[m.DisplayString for m in ExtAPI.Application.Messages]})
    raise
