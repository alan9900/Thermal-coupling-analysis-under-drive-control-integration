function run_m1
% M1 heat-source/power ledger only. No temperature model or optimization.
root=fileparts(fileparts(fileparts(mfilename('fullpath'))));
out=fullfile(root,'results','m1'); tracesDir=fullfile(out,'traces');
if ~exist(tracesDir,'dir'), mkdir(tracesDir); end
c=m1_load(root); tests=m1_tests(c,root);
writejson(fullfile(out,'tests.json'),tests);
rows={}; traces={}; options={}; dt=c.stage.numerics.sample_interval_s;
for road=[false true]
    for z=c.stage.cases.deceleration_g(:)'
        for cap=c.stage.cases.battery_charge_cap_total_kW(:)'
            o=m1_options(c); o.road_load=road; o.battery_charge_cap_total_kW=cap;
            id=sprintf('stop_z%02d_bat%02d_road%d',round(z*10),cap,road);
            [tr,q]=m1_trace(c,o,100,0,-z,dt,id);
            rows{end+1}=q; traces{end+1}=tr; options{end+1}=o; %#ok<AGROW>
            writetable(tr,fullfile(tracesDir,[id '.csv']));
        end
    end
end
% Separate robustness/interface cases, all with explicitly specified states.
special={};
o=m1_options(c); o.regen_available=[false true]; special{end+1}={o,100,0,-.6,'left_regen_unavailable'};
o=m1_options(c); o.battery_soc=.95; special{end+1}={o,100,0,-.6,'high_soc_no_regen'};
o=m1_options(c); o.temperature_charge_factor=0; special{end+1}={o,100,0,-.6,'temperature_charge_disabled'};
o=m1_options(c); o.wheel_speed_ratio=[.9 1.1]; o.rear_force_share=[.4 .6]; special{end+1}={o,100,0,-.6,'unequal_wheel_speed_port_test'};
o=m1_options(c); special{end+1}={o,0,80,.15,'short_drive_0_to_80'};
for k=1:numel(special)
    args=special{k}; [tr,q]=m1_trace(c,args{1},args{2},args{3},args{4},dt,args{5});
    rows{end+1}=q; traces{end+1}=tr; options{end+1}=args{1}; %#ok<AGROW>
    writetable(tr,fullfile(tracesDir,[args{5} '.csv']));
end
summary=struct2table([rows{:}]);
assert(all(summary.trace_feasible),'m1:InfeasibleCase','A planned trace cannot be tracked');
assert(all(summary.energy_residual_relative<c.stage.numerics.energy_relative_tolerance));
assert(all(summary.max_power_residual_W<c.stage.numerics.point_power_tolerance_W));
assert(all(summary.peak_total_battery_charge_kW(1:18)<=summary.battery_charge_cap_total_kW(1:18)+1e-7));
writetable(summary,fullfile(out,'case_summary.csv'));
% Source interface readiness is separate from numerical test success.
ready=struct('numerical_implementation','PASS','stage_status','PARTIAL', ...
    'reason','validated internal motor losses, regen split, directional gearbox maps, heat partition and BMS limits absent', ...
    'combined_emot','EPA fitted 650 V table; regeneration mirrored with empirical 1.05 factor', ...
    'drive_motor_inverter_split','ESTIMATED: ORNL sparse drive loss ratio applied to EPA combined loss; no extrapolation', ...
    'regen_motor_inverter_split','UNKNOWN: combined heat exported as unallocated EMOT', ...
    'winding_heat','UNKNOWN: NaN in all runtime traces; never use EMOT heat as copper heat', ...
    'gear_heat','ASSUMED: constant directional efficiencies, not a validated loss map', ...
    'disc_heat','ASSUMED: 0.90 contact-to-disc share, 0.85..0.95 illustrative bounds', ...
    'asymmetric_trace','imposed independent L/R speed/force power ports, includes signed exchange; not yaw dynamics', ...
    'thermal_temperature_prediction','NOT EXECUTED; M2 not authorized', ...
    'ANSYS','NOT EXECUTED','Fluent','NOT EXECUTED','optimization','NOT EXECUTED');
writejson(fullfile(out,'source_readiness.json'),ready);
validation=struct('status','PASS','stage_status','PARTIAL','case_count',height(summary), ...
    'maximum_energy_residual_relative',max(summary.energy_residual_relative), ...
    'maximum_point_power_residual_W',max(summary.max_power_residual_W), ...
    'test_groups',tests.test_group_count,'matlab',version,'release',version('-release'), ...
    'M0_baseline_commit',c.provenance.baseline_commit,'winding_sources_available',false,'M2_started',false);
writejson(fullfile(out,'validation.json'),validation);
save(fullfile(out,'m1_results.mat'),'summary','rows','traces','options','tests','ready','validation');
plots(c,summary,traces,out);
disp(summary(:,{'case_id','initial_left_disc_torque_Nm','left_disc_contact_energy_kJ','battery_net_energy_kJ','energy_residual_relative'}));
disp(validation);
end

function plots(c,summary,traces,out)
f=figure('Visible','off','Color','w','Position',[100 100 1150 720]); tiledlayout(2,2);
colors=lines(3);
nexttile; hold on;
for k=1:3
    cap=[0 30 60]; idx=find(strcmp(summary.case_id,sprintf('stop_z06_bat%02d_road1',cap(k))));
    tr=traces{idx}; plot(tr.time_s,tr.disc_contact_power_W_left/1000,'Color',colors(k,:),'LineWidth',1.5);
end
xlabel('Time (s)'); ylabel('One rear disc contact power (kW)'); legend('0 kW','30 kW','60 kW');
title('0.6g stop; total DC charge cap (SCREENING)'); grid on;
nexttile; idx=find(strcmp(summary.case_id,'stop_z06_bat30_road1')); tr=traces{idx};
plot(tr.time_s,[-tr.dc_power_total_W tr.emot_combined_heat_W_left+tr.emot_combined_heat_W_right ...
    tr.gear_heat_assumed_W_left+tr.gear_heat_assumed_W_right]/1000,'LineWidth',1.5);
xlabel('Time (s)'); ylabel('Whole-vehicle power (kW)'); legend('Battery recovery','EMOT combined heat','Gear heat (assumed)'); grid on;
nexttile; idx=find(strcmp(summary.case_id,'short_drive_0_to_80')); tr=traces{idx};
plot(tr.time_s,[tr.emot_combined_heat_W_left tr.motor_total_heat_estimated_W_left tr.inverter_heat_estimated_W_left]/1000,'LineWidth',1.5);
xlabel('Time (s)'); ylabel('One-side drive heat estimate (kW)'); legend('EMOT combined','Motor total (estimated)','Inverter (estimated)');
title('ORNL ratio split only inside sparse-data hull'); grid on;
nexttile; base=summary(1:18,:); E=base.left_disc_contact_energy_kJ;
E=reshape(E,3,3,2); bar([.3 .6 .8],E(:,:,2)');
xlabel('Deceleration (g)'); ylabel('One rear disc friction work (kJ)'); legend('0 kW','30 kW','60 kW');
title('Road load included; mirrored regen map'); grid on;
exportgraphics(f,fullfile(out,'source_power_curves.png'),'Resolution',180);
exportgraphics(f,fullfile(out,'source_power_curves.svg'),'ContentType','vector'); close(f);
f=figure('Visible','off','Color','w','Position',[100 100 1100 420]); tiledlayout(1,2);
nexttile; x=[.3 .6 .8]; nominal=summary([11 14 17],:);
E=[nominal.front_axle_friction_energy_kJ 2*nominal.left_disc_contact_energy_kJ ...
    nominal.road_energy_kJ nominal.gear_heat_energy_total_kJ nominal.emot_heat_energy_total_kJ -nominal.battery_net_energy_kJ];
bar(x,E,'stacked'); ylabel('Whole-vehicle energy (kJ)'); xlabel('Deceleration (g)');
legend('Front friction','Both rear discs','Road','Gear','EMOT','Recovered DC','Location','eastoutside');
title('Energy ledger; 30 kW total DC charge cap'); grid on;
nexttile; idx=find(strcmp(summary.case_id,'unequal_wheel_speed_port_test')); tr=traces{idx};
plot(tr.time_s,[tr.motor_rpm_left tr.motor_rpm_right],'LineWidth',1.5); xlabel('Time (s)'); ylabel('Motor speed (rpm)');
legend('Left port','Right port'); title('Imposed L/R speed test; exchange power accounted'); grid on;
exportgraphics(f,fullfile(out,'energy_and_independent_sides.png'),'Resolution',180);
exportgraphics(f,fullfile(out,'energy_and_independent_sides.svg'),'ContentType','vector'); close(f);
end

function writejson(path,value)
fid=fopen(path,'w','n','UTF-8'); assert(fid>=0); cl=onCleanup(@()fclose(fid));
fprintf(fid,'%s\n',jsonencode(value,'PrettyPrint',true));
end
