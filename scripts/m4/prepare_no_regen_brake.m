function prepare_no_regen_brake
% P1-A only: one M1-derived no-regen braking source, no thermal-state solve.
root=fileparts(fileparts(fileparts(mfilename('fullpath'))));
addpath(fullfile(root,'scripts','m1'));
configRel='configs/m4_no_regen_brake_baseline.json';
cfg=jsondecode(fileread(fullfile(root,configRel)));
[status,branch]=system('git branch --show-current');
assert(status==0 && strcmp(strtrim(branch),cfg.required_branch),'m4:Branch','Wrong development branch');
out=fullfile(root,cfg.output_directory);
assert(~exist(out,'dir'),'m4:NoOverwrite','Output already exists; preserve existing results');
preflightPath=fullfile(root,'results','m4','no_regen_p1a_preflight.json');
pre=jsondecode(fileread(preflightPath));
assert(strcmp(pre.status,'PASS_PREFLIGHT_ONLY_NOT_A_SIMULATION'),'m4:Preflight','Run independent preflight first');
for k=1:numel(pre.input_files)
    f=pre.input_files(k);
    assert(strcmp(sha256(fullfile(root,f.path)),f.sha256),'m4:StaleInput','Input changed after preflight: %s',f.path);
end
c=m1_load(root,false);
dt=c.stage.numerics.sample_interval_s;
assert(dt==cfg.sampling.expected_configured_interval_s,'m4:Sampling','Do not change M1 sampling');
assert(c.stage.numerics.point_power_tolerance_W==cfg.thresholds_registered_before_execution.point_power_tolerance_W);
assert(c.stage.numerics.energy_relative_tolerance==cfg.thresholds_registered_before_execution.energy_relative_tolerance);
o=m1_options(c); names=fieldnames(cfg.options);
for k=1:numel(names)
    value=cfg.options.(names{k});
    if numel(value)>1, value=reshape(value,1,[]); end
    o.(names{k})=value;
end
assert(~any(o.regen_available) && o.battery_charge_cap_total_kW==0);
assert(cfg.initial_speed_kmh==80 && cfg.final_speed_kmh==0 && cfg.deceleration_g==0.6);
assert(o.road_load && o.grade_rad==0 && all(o.wheel_speed_ratio==1) && all(o.rear_force_share==0.5));
mkdir(out); diary(fullfile(out,'matlab_generation.log'));
cleanup=onCleanup(@()diary('off'));
fprintf('P1-A generation only. MATLAB %s, release %s\n',version,version('-release'));
assert(strcmp(version('-release'),'2025a'),'m4:Software','MATLAB R2025a required');
fprintf('Scenario: %s; configured dt %.17g s\n',cfg.scenario_id,dt);
[tr,summary]=m1_trace(c,o,cfg.initial_speed_kmh,cfg.final_speed_kmh,-cfg.deceleration_g,dt,cfg.scenario_id);
assert(summary.trace_feasible,'m4:Infeasible','Do not export an infeasible braking source');
writetable(tr,fullfile(out,'vehicle_trace.csv'));
writejson(fullfile(out,'matlab_summary.json'),summary);
for side={'left','right'}
    [q,meta]=m1_sources(c,tr,side{1},cfg.source_mode,cfg.partition_overrides);
    csvRel=[cfg.output_directory '/' side{1} '_sources.csv'];
    writetable(q,fullfile(root,csvRel));
    meta.case_id=cfg.scenario_id; meta.scenario_id=cfg.scenario_id;
    meta.partition_scenario_id=c.partition.metadata.scenario_id;
    meta.trace_file=[cfg.output_directory '/vehicle_trace.csv'];
    meta.csv_file=csvRel; meta.csv_sha256=sha256(fullfile(root,csvRel));
    meta.trace_sha256=sha256(fullfile(out,'vehicle_trace.csv'));
    meta.source_config=configRel; meta.source_config_sha256=sha256(fullfile(root,configRel));
    meta.input_files=pre.input_files;
    meta.source_code_commit=pre.workspace_head;
    meta.source_code_identity='Commit plus preflight SHA256 of new scripts; final delivery commit recorded by Git/PR';
    meta.regen_available=[false false]; meta.battery_regen_recovery_W=0;
    meta.loss_budget_zero_interpretation=cfg.omission_policy;
    meta.actual_unpowered_motor_drag_W=NaN; meta.actual_inverter_standby_W=NaN;
    meta.actual_no_load_gear_churning_W=NaN;
    meta.unknown_representation='Unmeasured physical losses remain JSON null; calibrated winding samples remain CSV NaN';
    meta.single_disc_and_pad_pair_both_faces_combined=true;
    meta.single_side_only_not_two_rear_sides=true;
    units=struct; vars=q.Properties.VariableNames;
    for j=1:numel(vars)
        key=vars{j}; unit='1';
        if endsWith(key,'_W'), unit='W';
        elseif endsWith(key,'_s'), unit='s';
        elseif endsWith(key,'_m_s'), unit='m/s';
        elseif endsWith(key,'_rpm'), unit='rpm';
        elseif endsWith(key,'_Nm'), unit='N*m';
        elseif endsWith(key,'_rad_s'), unit='rad/s';
        elseif endsWith(key,'_Arms'), unit='A_RMS_proxy_not_measured'; end
        units.(key)=unit;
    end
    units.vehicle_speed_m_s='m/s'; units.disc_speed_rad_s='rad/s';
    meta.units=units;
    writejson(fullfile(out,[side{1} '_sources.json']),meta);
end
run=struct('schema_version',cfg.schema_version,'scenario_id',cfg.scenario_id, ...
    'status','GENERATED_PENDING_INDEPENDENT_AUDIT','matlab_version',version,'matlab_release',version('-release'), ...
    'workspace_head_before_run',pre.workspace_head,'input_files',pre.input_files, ...
    'preflight_sha256',sha256(preflightPath),'scenario',cfg,'vehicle_configuration',c.base, ...
    'm1_configuration',c.stage,'partition_configuration',c.partition,'options',o, ...
    'configured_dt_s',dt,'actual_uniform_dt_s',tr.time_s(2)-tr.time_s(1), ...
    'sample_count',height(tr),'omission_policy',cfg.omission_policy, ...
    'strict_data_mode_executed',false,'temperature_solver_executed',false, ...
    'ANSYS_executed',false,'Fluent_executed',false,'preheat_executed',false,'cooldown_executed',false);
writejson(fullfile(out,'run_metadata.json'),run);
fprintf('Generated %d samples, %.15g s; %s\n',height(tr),summary.duration_s,out);
fprintf('Generation finished; independent Python audit is still required.\n');
diary off;
files=dir(out); records=struct('path',{},'bytes',{},'sha256',{});
for k=1:numel(files)
    if files(k).isdir, continue; end
    records(end+1)=struct('path',[cfg.output_directory '/' files(k).name], ...
        'bytes',files(k).bytes,'sha256',sha256(fullfile(out,files(k).name))); %#ok<AGROW>
end
writejson(fullfile(out,'generated_files.json'),struct('hash_definition','raw bytes SHA256', ...
    'scenario_id',cfg.scenario_id,'files',records));
end

function value=sha256(path)
fid=fopen(path,'rb'); assert(fid>=0); cl=onCleanup(@()fclose(fid)); bytes=fread(fid,Inf,'*uint8');
md=java.security.MessageDigest.getInstance('SHA-256'); md.update(bytes);
value=lower(reshape(dec2hex(typecast(md.digest(),'uint8'),2).',1,[]));
end

function writejson(path,value)
fid=fopen(path,'w','n','UTF-8'); assert(fid>=0); cl=onCleanup(@()fclose(fid));
% jsondecode maps JSON null to []; restore those unknown scalars as null on
% export, without changing c or any archived M1 configuration.
fprintf(fid,'%s\n',jsonencode(restoreUnknowns(value),'PrettyPrint',true));
end

function value=restoreUnknowns(value)
if isstruct(value)
    names=fieldnames(value);
    for j=1:numel(value)
        for k=1:numel(names), value(j).(names{k})=restoreUnknowns(value(j).(names{k})); end
    end
elseif iscell(value)
    for j=1:numel(value), value{j}=restoreUnknowns(value{j}); end
elseif isempty(value)
    value=NaN;
end
end
