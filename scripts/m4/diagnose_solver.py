import os,json,traceback
RUN=r'E:\ansys_runs\m4_case0_20261021'
def describe(o):
    d={'name':o.Name,'type':str(o.DataModelObjectCategory),'state':str(o.ObjectState)}
    for key in ['Suppressed','Material','AnalysisType','State']:
        try:d[key]=str(getattr(o,key))
        except:pass
    return d
model=ExtAPI.DataModel.Project.Model
data={'analyses':[],'bodies':[],'contacts':[],'messages':[],'mesh':describe(model.Mesh)}
for a in model.Analyses:
    d=describe(a);d['children']=[describe(x) for x in a.Children];data['analyses'].append(d)
for b in model.Geometry.GetChildren(DataModelObjectCategory.Body,True):
    if not b.Suppressed:data['bodies'].append(describe(b))
for c in model.Connections.GetChildren(DataModelObjectCategory.ContactRegion,True):data['contacts'].append(describe(c))
for m in ExtAPI.Application.Messages:data['messages'].append({'text':m.DisplayString,'severity':str(m.Severity)})
with open(os.path.join(RUN,'solver_diagnosis.json'),'w') as f:json.dump(data,f,indent=2)
