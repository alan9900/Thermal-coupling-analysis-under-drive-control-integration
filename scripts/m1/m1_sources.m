function [q,meta]=m1_sources(c,tr,side,mode,overrides)
% Pure single-side M2 input preparation, WITHOUT a thermal network or file I/O.
% Engineering allocations never replace calibrated winding NaNs.
if nargin<5, overrides=struct; end
assert(ismember(string(mode),["strict","engineering"]),'m1:Mode','Mode must be strict or engineering');
if strcmp(mode,'strict')
    error('m1:StrictEvidenceGap','No verified internal loss map, regeneration split or component gearbox map. Engineering export forbidden in strict mode.');
end
assert(ismember(string(side),["left","right"]),'m1:Side','Select exactly one side');
[v,p]=m1_partition_parameters(c,overrides);
col=@(name)tr.([name '_' char(side)]);
t=tr.time_s; n=col('motor_rpm'); T=col('motor_torque_Nm');
L=col('emot_combined_heat_W'); G=col('gear_heat_assumed_W'); D=col('disc_contact_power_W');
assert(height(tr)>=2 && all(isfinite(t)) && all(diff(t)>0),'m1:SourceTime','Strictly increasing finite time required');
assert(all(isfinite([n T L G D]),'all') && all([n L G D]>=0,'all'),'m1:SourceInput','Nonnegative finite source inputs required');
assert(all(isnan(col('winding_heat_W'))),'m1:Evidence','Original calibrated winding losses must stay NaN');
assert(all(tr.trace_feasible),'m1:InfeasibleSource','Do not export an untracked demand as a realizable thermal history');
pm=col('motor_mechanical_power_W');
etaD=c.base.drive.rear_gearbox_per_side.peak_drive_efficiency_screening;
etaB=c.base.drive.rear_gearbox_per_side.peak_backdrive_efficiency_screening;
pw=pm*etaD; back=pm<0; pw(back)=pm(back)/etaB;
ratio=col('inverter_heat_estimated_W')./L;
covered=isfinite(ratio) & T>0 & L>0;
fi=inverter_fraction(v,ratio,covered); motorBudget=L.*(1-fi);
[motorRaw,gearRaw,current]=weights(p,v,n,T,pw);
M=allocate(motorBudget,motorRaw); Z=allocate(G,gearRaw);
% Rigorous component-wise interval enclosure of positive normalized weights.
% These independent extrema cannot be summed as one simultaneous scenario.
lo=v; hi=v; names=fieldnames(v);
for k=1:numel(names)
    key=names{k}; r=p.parameters.(key); lo.(key)=r(1); hi.(key)=r(3);
end
lo.torque_constant_Nm_per_Arms=p.parameters.torque_constant_Nm_per_Arms(3);
hi.torque_constant_Nm_per_Arms=p.parameters.torque_constant_Nm_per_Arms(1);
[ml,gl]=weights(p,lo,n,T,pw); [mh,gh]=weights(p,hi,n,T,pw);
flow=inverter_fraction(endpoint(p,1),ratio,covered); fhigh=inverter_fraction(endpoint(p,3),ratio,covered);
[Mlo,Mhi]=enclose(L.*(1-fhigh),L.*(1-flow),ml,mh);
[Glo,Ghi]=enclose(G,G,gl,gh);
beta=v.disc_heat_fraction;
q=table(t,tr.speed_m_s,n,T,col('disc_omega_rad_s'),L,G,D,col('winding_heat_W'), ...
    'VariableNames',{'time_s','vehicle_speed_m_s','motor_speed_rpm','motor_torque_Nm','disc_speed_rad_s', ...
    'emot_total_reference_W','gear_total_assumed_W','disc_contact_W','calibrated_winding_heat_W'});
sourceNames={'copper','iron','rotor_other','inverter','gear_mesh','gear_bearing','gear_other','disc','pad'};
nom=[M L.*fi Z beta*D (1-beta)*D];
r=p.parameters.disc_heat_fraction;
lower=[Mlo L.*flow Glo r(1)*D (1-r(3))*D];
upper=[Mhi L.*fhigh Ghi r(3)*D (1-r(1))*D];
for k=1:numel(sourceNames)
    name=sourceNames{k}; q.([name '_engineering_W'])=nom(:,k);
    q.([name '_lower_W'])=lower(:,k); q.([name '_upper_W'])=upper(:,k);
end
q.current_proxy_Arms=current;
q.copper_raw_weight_W=motorRaw(:,1); q.iron_raw_weight_W=motorRaw(:,2); q.rotor_other_raw_weight_W=motorRaw(:,3);
q.motor_budget_normalization=normalization(motorBudget,motorRaw);
q.gear_budget_normalization=normalization(G,gearRaw);
q.drive_ratio_covered=covered; q.regen_map_is_estimated=col('regen_is_estimated');
q.emot_partition_residual_W=sum(nom(:,1:4),2)-L;
q.gear_partition_residual_W=sum(nom(:,5:7),2)-G;
q.disc_partition_residual_W=sum(nom(:,8:9),2)-D;
q.vehicle_power_residual_W=tr.power_residual_W;
q.source_class_code=3*ones(height(q),1); % all allocated internals are S3, including ORNL-assisted ones
assert(max(abs([q.emot_partition_residual_W q.gear_partition_residual_W q.disc_partition_residual_W]),[],'all')<1e-7, ...
    'm1:PartitionConservation','Component sums must equal their own total budget');
assert(all(nom>=-1e-10,'all') && all(nom>=lower-1e-7 & nom<=upper+1e-7,'all'),'m1:Interval','Allocation outside enclosure');
meta=struct('schema_version',p.metadata.schema_version,'mode','engineering','side',side, ...
    'scenario_id',p.metadata.scenario_id,'classification','S3_ENGINEERING_NOT_MEASURED', ...
    'parameter_values',v,'original_calibrated_data_modified',false, ...
    'inverter_thermal_destination','external_boundary_not_motor_internal', ...
    'rotor_other_destination','lumped_rotor_plus_other_motor_loss_requires_M2_node_choice', ...
    'gear_other_destination','oil_seal_and_drag_lump_not_motor_winding', ...
    'bounds_definition','conditional component-wise enclosure over configured independent box; not simultaneous extrema or confidence intervals', ...
    'total_loss_uncertainty_included',false,'no_load_gear_drag_included',false, ...
    'temperature_feedback_executed',false,'M2_executed',false, ...
    'source_registry','docs/M1_SOURCE_REVIEW.md','input_provenance',c.provenance);
end

function v=endpoint(p,k)
v=struct; names=fieldnames(p.parameters);
for j=1:numel(names), r=p.parameters.(names{j}); v.(names{j})=r(k); end
end

function f=inverter_fraction(v,ratio,covered)
f=v.fallback_inverter_fraction*ones(size(ratio));
f(covered)=min(.99,max(.01,ratio(covered)*v.drive_inverter_ratio_multiplier));
end

function [motor,gear,I]=weights(p,v,n,T,pw)
ref=p.reference; x=n/ref.reference_speed_rpm; y=abs(T)/ref.reference_torque_Nm;
fw=max(n/p.controls.field_weakening_start_rpm-1,0);
I=abs(T)/v.torque_constant_Nm_per_Arms.*sqrt(1+v.field_weakening_current_factor*fw.^2);
% alpha is referenced to 20 C, while measured R is at 21 C.
R=ref.phase_resistance_ohm*(1+ref.copper_alpha_20_per_K*(v.winding_temperature_C-20)) ...
    /(1+ref.copper_alpha_20_per_K*(ref.resistance_temperature_C-20));
cu=3*R*I.^2.*(1+v.ac_copper_speed_factor*x.^2);
iron=v.iron_hysteresis_ref_W*x+v.iron_eddy_ref_W*x.^2;
rotor=v.rotor_speed_squared_ref_W*x.^2+v.motor_stray_load_ref_W*y.^2;
motor=[cu iron rotor];
omega=n*2*pi/60; P=abs(pw);
mesh=v.gear_mesh_power_coefficient*P;
bearing=v.gear_bearing_torque_Nm*omega+v.gear_bearing_load_coefficient*P;
other=v.gear_churning_ref_W*x.^3+v.gear_seal_torque_Nm*omega;
gear=[mesh bearing other];
end

function q=allocate(total,w)
den=sum(w,2);
assert(all(den>0 | total==0),'m1:ZeroWeights','Positive loss budget needs positive weights');
q=total.*w./max(den,realmin);
end

function k=normalization(total,w)
den=sum(w,2); k=nan(size(total)); use=total>0 & den>0; k(use)=total(use)./den(use);
end

function [lower,upper]=enclose(totalLo,totalHi,lo,hi)
lower=zeros(size(lo)); upper=lower;
for k=1:size(lo,2)
    other=setdiff(1:size(lo,2),k);
    lower(:,k)=totalLo.*lo(:,k)./max(lo(:,k)+sum(hi(:,other),2),realmin);
    upper(:,k)=totalHi.*hi(:,k)./max(hi(:,k)+sum(lo(:,other),2),realmin);
end
end
