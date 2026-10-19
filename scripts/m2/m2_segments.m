function s=m2_segments(root,p,sourceOverrides)
% Read accepted M1 code/data; all newly generated histories stay in M2 only.
if nargin<3,sourceOverrides=struct;end
c=m1_load(root); o=m1_options(c);o.battery_charge_cap_total_kW=p.cases.charge_cap_total_kW;
rawDrive=readtable(fullfile(root,'results','m1','traces','short_drive_0_to_80.csv'));
[rawBrake,~]=m1_trace(c,o,p.cases.cycle_speed_kmh,0,-p.cases.brake_deceleration_g,.02,'m2_brake80');
oh=o;oh.grade_rad=p.cases.preheat_grade_rad;
rawHold=constantTrace(c,oh,p.cases.cycle_speed_kmh/3.6,p.cases.preheat_s);
orr=o;orr.road_load=false;rawRest=constantTrace(c,orr,0,1);
[s.drive,s.drive_meta]=m1_sources(c,rawDrive,p.cases.side,'engineering',sourceOverrides);
[s.brake,s.brake_meta]=m1_sources(c,rawBrake,p.cases.side,'engineering',sourceOverrides);
[s.hold,s.hold_meta]=m1_sources(c,rawHold,p.cases.side,'engineering',sourceOverrides);
[s.rest,s.rest_meta]=m1_sources(c,rawRest,p.cases.side,'engineering',sourceOverrides);
if isempty(fieldnames(sourceOverrides))
    accepted=readtable(fullfile(root,'results','m1','engineering','interface','short_drive_0_to_80_left.csv'));
    for key={'copper','iron','rotor_other','inverter','gear_mesh','gear_bearing','gear_other','disc','pad'}
        name=[key{1} '_engineering_W'];assert(max(abs(s.drive.(name)-accepted.(name)))<1e-7,'m2:M1Interface','M1 source contract changed');
    end
end
s.hold_motor_mechanical_W=rawHold.motor_mechanical_power_W_left(1);
s.hold_feasible=all(rawHold.trace_feasible);
assert(s.hold_feasible,'m2:PreheatDemand','Prescribed preheat exceeds instantaneous M1 envelope');
s.sourceOverrides=sourceOverrides;
end

function tr=constantTrace(c,o,v,duration)
q=m1_point(c,v,0,o);fields=fieldnames(q);tr=table([0;duration],'VariableNames',{'time_s'});
for j=1:numel(fields)
    key=fields{j};val=q.(key);
    if numel(val)==2,tr.([key '_left'])=repmat(val(1),2,1);tr.([key '_right'])=repmat(val(2),2,1);
    else,tr.(key)=repmat(val,2,1);end
end
end
