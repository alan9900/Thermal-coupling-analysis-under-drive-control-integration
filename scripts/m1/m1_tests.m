function result=m1_tests(c,root)
% Physics/interface tests; thresholds fixed before inspecting the run.
names=strings(0,1); o=m1_options(c); o.road_load=false; o.battery_charge_cap_total_kW=0;
q=m1_point(c,100/3.6,-.6*9.81,o);
assert(abs(q.disc_friction_torque_Nm(1)-752.839090958409)<1e-8);
assert(abs(q.disc_contact_power_W(1)-63370.2938517179)<1e-7);
names(end+1)="M0 0.6g torque and initial power regression";
[~,ref]=m1_trace(c,o,100,0,-.6,.04,'test_analytic');
expected=.5*1800*(100/3.6)^2*(.55-.6*.55/2.765)/2/1000;
assert(abs(ref.left_disc_contact_energy_kJ-expected)<1e-8);
assert(abs(ref.front_axle_friction_energy_kJ+2*expected-694.444444444444)<1e-8);
names(end+1)="independent stop-energy analytic solution including front and both rear sides";
assert(max(abs(q.disc_omega_rad_s-q.wheel_omega_rad_s))==0);
assert(max(abs(q.motor_rpm-q.wheel_omega_rad_s*9*60/(2*pi)))<1e-10);
names(end+1)="disc own-wheel 1:1 and each motor 9:1 speed";
on=m1_emot(c,[3000 3000],[0 0],[true true]);
off=m1_emot(c,[3000 3000],[0 0],[false false]);
assert(all(on.combined_heat_W>0) && all(off.combined_heat_W==0));
names(end+1)="explicit active idle versus omitted disconnected drag";
raw=m1_emot(c,[5000 5000],[50 -50],[true true]);
assert(raw.dc_W(1)>raw.mechanical_W(1) && raw.dc_W(2)<0);
assert(max(abs(raw.dc_W-raw.mechanical_W-raw.combined_heat_W))<1e-10);
assert(isfinite(raw.motor_total_heat_estimated_W(1)) && isnan(raw.motor_total_heat_estimated_W(2)));
assert(abs(raw.motor_total_heat_estimated_W(1)+raw.inverter_heat_estimated_W(1)-raw.combined_heat_W(1))<1e-8);
assert(raw.unallocated_emot_heat_W(2)==raw.combined_heat_W(2) && all(isnan(raw.winding_heat_W)));
names(end+1)="signed DC power; split closure; regen and winding losses remain unknown";
out=m1_emot(c,[0 0],[50 50],[true true]);
assert(all(isnan(out.motor_total_heat_estimated_W)) && all(out.unallocated_emot_heat_W==out.combined_heat_W));
names(end+1)="no extrapolation of sparse ORNL component split";
cc=c; cc.base.drive.rear_gearbox_per_side.peak_backdrive_efficiency_screening=.90;
gg=m1_gear(cc,[100000 -100000]);
assert(abs(gg.heat_W(1)-100000*(1/.96-1))<1e-8 && abs(gg.heat_W(2)-10000)<1e-8);
names(end+1)="different drive and backdrive efficiencies use correct power direction";
o.battery_charge_cap_total_kW=30;
sym=m1_point(c,100/3.6,-.6*9.81,o);
assert(-sym.dc_power_total_W<=30000+1e-5 && -sym.dc_power_total_W>29999.9);
assert(max(abs(sym.dc_power_each_W-fliplr(sym.dc_power_each_W)))<1e-8);
names(end+1)="30 kW cap is total vehicle DC charge; L/R symmetry";
o.battery_soc=.95; full=m1_point(c,100/3.6,-.6*9.81,o);
assert(all(full.rear_regen_force_N==0));
o.battery_soc=.5; o.temperature_charge_factor=0; cold=m1_point(c,100/3.6,-.6*9.81,o);
assert(all(cold.rear_regen_force_N==0));
names(end+1)="screening SOC and temperature charge-disable fallbacks";
o.temperature_charge_factor=1;
slow=m1_point(c,4/3.6,-.6*9.81,o); zero=m1_point(c,0,-.6*9.81,o);
assert(all(slow.rear_regen_force_N==0) && all(zero.disc_contact_power_W==0) && zero.dc_power_total_W==0);
names(end+1)="low-speed regen fades and zero-speed power stays finite";
o.regen_available=[false true]; fault=m1_point(c,100/3.6,-.6*9.81,o);
assert(fault.rear_regen_force_N(1)==0 && fault.rear_regen_force_N(2)>sym.rear_regen_force_N(2));
assert(-fault.dc_power_total_W<=30000+1e-5 && fault.trace_feasible);
names(end+1)="single-side regen loss blends friction and reuses shared battery headroom";
o.regen_available=[true true]; o.wheel_speed_ratio=[.9 1.1]; o.rear_force_share=[.4 .6];
asym=m1_point(c,100/3.6,-.6*9.81,o);
assert(asym.motor_rpm(1)~=asym.motor_rpm(2) && abs(asym.lr_kinematic_exchange_W)>1);
assert(abs(asym.power_residual_W)<1e-6);
names(end+1)="independent L/R wheel speeds include explicit non-longitudinal exchange port";
o=m1_options(c); o.road_load=false; o.rear_mu=[.2 .8];
unmet=m1_point(c,100/3.6,-.8*9.81,o);
assert(~unmet.trace_feasible && abs(unmet.unmet_force_N)>1 && abs(unmet.power_residual_W)<1e-6);
names(end+1)="unachievable braking demand is flagged, not silently declared feasible";
o=m1_options(c); o.battery_discharge_cap_total_kW=5;
drive=m1_point(c,10/3.6,.3*9.81,o);
assert(drive.dc_power_total_W<=5000+1e-5 && ~drive.trace_feasible);
names(end+1)="traction battery discharge cap yields explicit unmet demand";
mustfail(@()m1_emot(c,[13500 1000],[20 20]),'m1:MapBounds');
mustfail(@()m1_emot(c,[10000 1000],[100 20]),'m1:TorqueLimit');
mustfail(@()m1_point(c,-1,0,m1_options(c)),'m1:State');
cc=c; cc.stage.inputs.source_voltage_V=400;
mustfail(@()m1_emot(cc,[5000 5000],[20 20]),'m1:Voltage');
names(end+1)="reject speed/torque/voltage extrapolation and unsupported reverse motion";
cc=c; cc.stage.assumptions.allow_estimated_regen_map=false;
mustfail(@()m1_emot(cc,[5000 5000],[-20 -20]),'m1:EstimatedRegenRejected');
mustfail(@()m1_load(root,true),'m1:EvidenceGap');
names(end+1)="strict evidence mode rejects unsupported thermal claims and mirrored regen";
o=m1_options(c); o.grade_rad=atan(.04);
hill=m1_point(c,80/3.6,-.3*9.81,o);
assert(abs(hill.power_residual_W)<1e-6 && hill.grade_power_W>0);
names(end+1)="grade work and load transfer have an explicit energy port";
o=m1_options(c);
[~,coarse]=m1_trace(c,o,100,0,-.6,.02,'refine_coarse');
[~,fine]=m1_trace(c,o,100,0,-.6,.01,'refine_fine');
refinement=abs(coarse.left_disc_contact_energy_kJ-fine.left_disc_contact_energy_kJ)/fine.left_disc_contact_energy_kJ;
assert(refinement<.001);
names(end+1)="time-step refinement changes nominal disc energy by less than 0.1 percent";
result=struct('status','PASS','test_groups',names,'test_group_count',numel(names), ...
    'disc_energy_refinement_relative',refinement,'analytic_stop_energy_kJ',expected, ...
    'strict_mode','expected rejection: missing validated thermal inputs', ...
    'experimental_validation','NOT EXECUTED','matlab',version,'release',version('-release'));
end

function mustfail(fn,id)
try
    fn();
catch e
    assert(strcmp(e.identifier,id),'m1:WrongException','Expected %s, got %s',id,e.identifier); return
end
error('m1:ExpectedFailure','Expected rejection %s',id);
end
