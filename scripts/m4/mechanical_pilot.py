# Actual first transient attempt. Results remain diagnostic until validated.
import os,json,traceback,time
RUN=r'E:\ansys_runs\m4_case0_20261021'
def dump(name,x):
    with open(os.path.join(RUN,name),'w') as f:json.dump(x,f,indent=2)
def sel(ids):
    s=ExtAPI.SelectionManager.CreateSelectionInfo(SelectionTypeEnum.GeometryEntities);s.Ids=ids;return s
try:
    model=ExtAPI.DataModel.Project.Model;ExtAPI.Application.ActiveUnitSystem=MechanicalUnitSystem.StandardMKS
    with open(os.path.join(RUN,'pilot_source.json')) as f:p=json.load(f)
    bodies=model.Geometry.GetChildren(DataModelObjectCategory.Body,True);by={}
    for b in bodies:
        if not b.Suppressed:by.setdefault(b.Name.split('|')[0],[]).append(b)
    # Remove default contact assumptions; every replacement has finite h.
    for c in list(model.Connections.GetChildren(DataModelObjectCategory.ContactRegion,True)):c.Delete()
    contacts=[]
    pairs=[('brake_disc_hat','disc_hub',1000),('disc_hub','hub_removable_sleeve',1000),('hub_removable_sleeve','output_shaft',1000),
        ('gear_case_front','gear_case_rear',1000),('gear_case_front','motor_gear_adapter',1000),('motor_gear_adapter','motor_case',1000),
        ('motor_case','motor_stator',500),('motor_stator','motor_winding',100),('motor_rotor_other','motor_stator',20),
        ('motor_rotor_shaft','motor_rotor_other',1000),('motor_rotor_shaft','motor_input_coupling',1000),('motor_input_coupling','input_shaft',1000),
        ('intermediate_shaft','stage1_gear',1000),('output_shaft','stage2_gear',1000),
        ('gear_case_rear','caliper_reaction_bracket',1000),('caliper_reaction_bracket','caliper',1000),
        ('caliper','pad_near',100),('caliper','pad_far',100),('oil_inventory','gear_case_rear',65),('oil_inventory','stage2_gear',65)]
    for ax in ['input','intermediate','output']:
        for j,case in [(1,'gear_case_front'),(2,'gear_case_rear')]:
            pairs.extend([(ax+'_shaft',ax+'_bearing_'+str(j),1000),(ax+'_bearing_'+str(j),case,1000)])
    for a,b,h in pairs:
        c=model.Connections.AddContactRegion();c.Name='S3_'+a+'_to_'+b
        c.SourceLocation=sel([x.GetGeoBody().Id for x in by[a]]);c.TargetLocation=sel([x.GetGeoBody().Id for x in by[b]])
        c.ContactType=ContactType.Bonded;c.AutomaticThermalConductance=False;c.ThermalConductanceValue=Quantity(str(h)+' [W m^-2 K^-1]')
        c.PinballRegion=ContactPinballType.Radius;c.PinballRadius=Quantity('2 [mm]' if a!='oil_inventory' else '20 [mm]')
        contacts.append({'from':a,'to':b,'h_W_m2K':h,'law':'finite imperfect thermal contact; not ideal bonded conductance'})
    dump('pilot_contacts.json',contacts)
    analysis=model.Analyses[0];analysis.Name='M4_Case0_brake_only_DIAGNOSTIC'
    analysis.Children[0].InitialTemperatureValue=Quantity('25 [C]')
    settings=analysis.AnalysisSettings;settings.NumberOfSteps=1;settings.StepEndTime=Quantity(str(p['duration_s'])+' [s]')
    settings.AutomaticTimeStepping=AutomaticTimeStepping.Off;settings.TimeStep=Quantity('0.5 [s]')
    def tab(field,values,unit):
        field.Inputs[0].DiscreteValues=[Quantity(str(x)+' [s]') for x in p['time_s']]
        field.Output.DiscreteValues=[Quantity(str(x)+' ['+unit+']') for x in values]
    # IGeoFace centroid/area are mm/mm2. Face annulus centroid is on axis;
    # do not select an annulus by centroid radius.
    face_rows=[]
    for name,bb in by.items():
        for b in bb:
            for f in b.GetGeoBody().Faces:face_rows.append((name,f.Id,list(f.Centroid),f.Area*1e-6,str(f.SurfaceType)))
    def face(name,x,amin=0):
        ids=[i for n,i,c,a,t in face_rows if n==name and abs(c[0]-x)<.001 and a>amin and t=='GeoSurfacePlane']
        assert len(ids)==1,(name,x,ids);return ids
    heat=[]
    for name,x,amin,key in [('brake_disc_hat',205,.02,'disc_W'),('brake_disc_hat',227,.02,'disc_W'),('pad_near',204.5,.001,'pad_W'),('pad_far',227.5,.001,'pad_W')]:
        ids=face(name,x,amin);hf=analysis.AddHeatFlow();hf.Name='M1_'+name+'_'+str(x);hf.Location=sel(ids)
        tab(hf.Magnitude,[q*.5 for q in p[key]],'W');heat.append({'body':name,'face_ids':ids,'source':key,'fraction':.5})
    dump('pilot_source_faces.json',heat)
    # Finite convection; exclude internal faces and the jacket inventory.
    external=[];jacket=[]
    for name,i,c,a,t in face_rows:
        x,y,z=c
        if name=='brake_disc_hat':external.append(i)
        elif name in ['gear_case_front','gear_case_rear'] and (abs(x)<.001 or abs(x-160)<.001 or abs(y+110)<.001 or abs(y-285)<.001 or abs(z+110)<.001 or abs(z-265)<.001):external.append(i)
        elif name=='motor_case' and t=='GeoSurfaceCylinder':
            # Cylinder centroid is on its axis: distinguish by axial extent/area.
            if a>.13:external.append(i)
            elif -193.01<x<-87.99 and .08<a<.10:jacket.append(i)
    assert external and jacket,(len(external),len(jacket))
    for label,ids,h in [('ambient',external,15),('jacket',jacket,300)]:
        conv=analysis.AddConvection();conv.Name='S3_finite_'+label;conv.Location=sel(ids)
        conv.FilmCoefficient.Output.DiscreteValues=[Quantity(str(h)+' [W m^-2 K^-1]')]
        conv.AmbientTemperature.Output.DiscreteValues=[Quantity('25 [C]')]
    for name,ids,epsilon in [('disc',face('brake_disc_hat',205,.02),.8),('case',face('gear_case_rear',160,.1),.7)]:
        rad=analysis.AddRadiation();rad.Name='Open_pair_'+name;rad.Location=sel(ids)
        rad.Correlation=RadiationType.SurfaceToSurface;rad.Enclosure=1;rad.EnclosureType=EnclosureType.Open
        rad.Emissivity.Output.DiscreteValues=[Quantity(str(epsilon))];rad.AmbientTemperature.Output.DiscreteValues=[Quantity('25 [C]')]
    temp=analysis.Solution.AddTemperature();temp.Name='Diagnostic_temperature_not_validated'
    dump('pilot_setup.json',{'status':'SETUP_EXECUTED','contact_pairs':len(contacts),'source_faces':heat,'time_step_s':.5,
        'ambient_faces':external,'jacket_faces':jacket,'solve_validation':'PENDING','hot_air_feedback':'NOT IMPLEMENTED'})
    analysis.WriteInputFile(os.path.join(RUN,'pilot_ds.dat'))
    dump('pilot_solve_started.json',{'time':time.time()})
    analysis.Solution.Solve(True)
    dump('pilot_solve_state.json',{'state':str(analysis.Solution.ObjectState),'working_dir':analysis.WorkingDir,'result_file':analysis.ResultFileName})
    assert str(analysis.Solution.ObjectState)=='Solved','BLOCKED: solver did not report Solved'
    analysis.Solution.EvaluateAllResults();temp.Activate();ExtAPI.Graphics.Camera.SetFit()
    ExtAPI.Graphics.ExportImage(os.path.join(RUN,'DIAGNOSTIC_temperature_NOT_VALIDATED.png'))
    dump('pilot_temperature.json',{'minimum':str(temp.Minimum),'maximum':str(temp.Maximum),'average':str(temp.Average),'status':'DIAGNOSTIC_NO_ENERGY_OR_CONVERGENCE_ACCEPTANCE'})
except:
    dump('pilot_failure.json',{'status':'FAILED','traceback':traceback.format_exc()})
    raise
