function f=m2_forcing(p,s,preheated,dt)
% Exact energy-preserving resampling of each M1 piecewise-linear segment.
keys={'copper','iron','rotor_other','inverter','gear_mesh','gear_bearing','gear_other','disc','pad'};
blocks={};labels={};
for cycle=1:p.cases.cycles
    blocks{end+1}=s.drive;labels{end+1}=sprintf('drive_%d',cycle); %#ok<AGROW>
    if preheated && cycle==1,blocks{end+1}=s.hold;labels{end+1}='high_load_preheat';end %#ok<AGROW>
    blocks{end+1}=s.brake;labels{end+1}=sprintf('brake_%d',cycle); %#ok<AGROW>
    z=s.rest;z.time_s=z.time_s*p.cases.rest_per_cycle_s;
    blocks{end+1}=z;labels{end+1}=sprintf('rest_%d',cycle); %#ok<AGROW>
end
z=s.rest;z.time_s=z.time_s*p.cases.final_cool_s;blocks{end+1}=z;labels{end+1}='final_cool';
edges=0;values=[];which=[];rawIntegral=zeros(1,15);boundaries=[];
for j=1:numel(blocks)
    tr=blocks{j};t=tr.time_s; duration=t(end);assert(duration>0 && dt>0,'m2:Time','Positive segment durations and step required');
    matrix=zeros(height(tr),15);
    for k=1:9,matrix(:,k)=tr.([keys{k} '_engineering_W']);end
    matrix(:,10:15)=[tr.vehicle_speed_m_s tr.motor_speed_rpm tr.motor_torque_Nm tr.emot_total_reference_W tr.gear_total_assumed_W tr.disc_contact_W];
    assert(all(isnan(tr.calibrated_winding_heat_W)) && all(matrix(:,1:9)>=0,'all'),'m2:M1Interface','M1 raw unknowns or source sign changed');
    target=linspace(0,duration,ceil(duration/dt)+1)';
    integral=primitive(t,matrix,target);averages=diff(integral)./diff(target);
    rawIntegral=rawIntegral+trapz(t,matrix);
    start=edges(end);edges=[edges;start+target(2:end)];values=[values;averages];which=[which;j*ones(size(averages,1),1)]; %#ok<AGROW>
    boundaries(j,:)=[start edges(end)]; %#ok<AGROW>
end
assert(all(diff(edges)>0) && max(diff(edges))<=dt+1e-10,'m2:Time','Bad forcing bins');
residual=sum(values.*diff(edges),1)-rawIntegral;
assert(max(abs(residual(1:9)))<1e-6,'m2:ResampleEnergy','Source resampling changed integrated heat');
assert(max(abs(sum(values(:,1:4),2)-values(:,13)))<1e-7 && ...
    max(abs(sum(values(:,5:7),2)-values(:,14)))<1e-7 && max(abs(sum(values(:,8:9),2)-values(:,15)))<1e-7, ...
    'm2:M1Interface','Source partitions no longer match their own reference budgets');
f=struct('edges_s',edges,'parts_W',values(:,1:9),'speed_m_s',values(:,10),'motor_rpm',values(:,11), ...
    'motor_torque_Nm',values(:,12),'reference_budgets_W',values(:,13:15),'segment_id',which, ...
    'segment_labels',{labels},'segment_boundaries_s',boundaries,'raw_integral_J',rawIntegral(1:9), ...
    'resampling_energy_residual_J',max(abs(residual(1:9))),'mode','engineering', ...
    'classification','S3_CONCEPT_PREDICTION_NOT_CALIBRATED','preheated',preheated,'maximum_step_s',dt);
end

function E=primitive(t,P,query)
% Analytic primitive of linear power within every original M1 sample interval.
cum=cumtrapz(t,P);idx=interp1(t,(1:numel(t))',query,'previous');idx=min(idx,numel(t)-1);
d=query-t(idx);slope=(P(idx+1,:)-P(idx,:))./(t(idx+1)-t(idx));
E=cum(idx,:)+P(idx,:).*d+.5*slope.*d.^2;
end
