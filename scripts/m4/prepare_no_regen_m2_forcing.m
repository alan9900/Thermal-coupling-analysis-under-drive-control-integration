function prepare_no_regen_m2_forcing
% P2-A input-only adapter. Never calls m2_simulate, m2_flux or m2_export.
root=fileparts(fileparts(fileparts(mfilename('fullpath'))));
addpath(fullfile(root,'scripts','m2'));
configRel='configs/m4_no_regen_m2_baseline.json';cfg=jsondecode(fileread(fullfile(root,configRel)));
pre=jsondecode(fileread(fullfile(root,cfg.preflight_file)));
assert(strcmp(pre.status,'PASS_INPUT_PREFLIGHT_ONLY'),'m4p2:Preflight','Independent preflight required');
for j=1:numel(pre.input_files)
    z=pre.input_files(j);assert(strcmp(sha256(fullfile(root,z.path)),z.sha256),'m4p2:StaleInput','Changed input %s',z.path);
end
[status,branch]=system('git branch --show-current');
assert(status==0 && strcmp(strtrim(branch),cfg.required_branch),'m4p2:Branch','Wrong branch');
out=fullfile(root,cfg.output_directory);assert(~exist(out,'dir'),'m4p2:NoOverwrite','Preserve existing output');
mkdir(out);diary(fullfile(out,'matlab_preparation.log'));cl=onCleanup(@()diary('off'));
fprintf('P2-A INPUT ONLY; MATLAB %s / %s\n',version,version('-release'));
assert(strcmp(version('-release'),'2025a'),'m4p2:Software','R2025a required');
profile on;
c=m2_load(root,'engineering');p=c.p;dt=p.numerics.maximum_step_s;
assert(c.N==13 && dt==cfg.expected_maximum_step_s);
tr=readtable(fullfile(root,cfg.input_directory,[cfg.side '_sources.csv']));
assert(all(isnan(tr.calibrated_winding_heat_W)) && tr.time_s(1)==0);
% m2_forcing's public builder hardcodes multiple drive/brake/rest blocks. Its
% terminal-block branch also runs the SAME original primitive on one table.
% Use that branch with no cycles and a unit time multiplier, then remove its
% historical label. This adds no physical rest/cooldown and no new samples.
carrier=struct('cases',struct('cycles',cfg.single_segment_adapter.carrier_cycles, ...
    'final_cool_s',cfg.single_segment_adapter.carrier_time_scale));
segments=struct('rest',tr);f=m2_forcing(carrier,segments,false,dt);
f.segment_labels={'single_brake'};f.segment_boundaries_s=[tr.time_s(1) tr.time_s(end)];
assert(numel(f.segment_labels)==1 && all(f.segment_id==1) && f.edges_s(end)==tr.time_s(end));
profile off;info=profile('info');called={info.FunctionTable.FunctionName};
m2calls=called(startsWith(called,'m2_'));
forbidden=contains(called,'m2_simulate') | contains(called,'m2_flux') | strcmp(called,'run_m2') | contains(called,'m2_export');
assert(~any(forbidden),'m4p2:Scope','Temperature or full-result exporter was called');
% Read the existing mapping as text; never execute the integration function.
solverText=fileread(fullfile(root,'scripts','m2','m2_simulate.m'));
token=regexp(solverText,'dest=\[([^\]]+)\]','tokens','once');assert(~isempty(token));
dest=sscanf(token{1},'%d')';assert(isequal(dest,[10 9 11 0 5 4 6 1 2]));
keys=cellstr(string(cfg.part_keys));expected=cellstr(string(cfg.source_destination_node_ids));
for j=1:9
    if dest(j)==0,assert(strcmp(expected{j},'EXTERNAL'));
    else,assert(strcmp(c.ids{dest(j)},expected{j}));end
end
% Export only the source-table schema from m2_export, not fabricated r.T/Y.
source=table(f.edges_s(1:end-1),f.edges_s(2:end),f.speed_m_s,f.motor_rpm,f.motor_torque_Nm, ...
    'VariableNames',{'start_s','end_s','speed_m_s','motor_rpm','motor_torque_Nm'});
for j=1:9,source.([keys{j} '_engineering_W'])=f.parts_W(:,j);end
source.emot_reference_W=f.reference_budgets_W(:,1);source.gear_reference_W=f.reference_budgets_W(:,2);
source.disc_contact_W=f.reference_budgets_W(:,3);source.segment_id=f.segment_id;
source.calibrated_winding_heat_W=nan(height(source),1);
writetable(source,fullfile(out,'single_brake_forcing.csv'));
mask=reshape(cfg.expected_mask_motor_gear_brake,1,[]);
save(fullfile(out,'m2_forcing_input.mat'),'f','mask');
saved=load(fullfile(out,'m2_forcing_input.mat'));assert(isequaln(saved.f,f) && isequal(saved.mask,[0 0 1]));
Q=zeros(height(source),c.N);parts=f.parts_W;
parts(:,1:3)=parts(:,1:3)*c.values.motor_total_loss_scale*mask(1);
parts(:,5:7)=parts(:,5:7)*c.values.gear_total_loss_scale*mask(2);parts(:,8:9)=parts(:,8:9)*mask(3);
for j=1:9,if dest(j)>0,Q(:,dest(j))=Q(:,dest(j))+parts(:,j);end,end
nodeSource=array2table([source.start_s source.end_s Q],'VariableNames',[{'start_s','end_s'} strcat(c.ids,'_source_W')]);
writetable(nodeSource,fullfile(out,'node_source_input.csv'));
net=struct('ids',{c.ids},'C_J_K',c.C,'from',c.from,'to',c.to,'G0_W_K',c.G0,'Gv',c.Gv, ...
    'Rad_W_K4',c.Rad,'cut_group',c.cut,'AmbG0',c.AmbG0,'AmbGv',c.AmbGv,'AmbRad',c.AmbRad, ...
    'CoolG',c.CoolG,'Tambient_K',c.Tambient,'Tcoolant_K',c.Tcoolant,'drive',c.drive,'edge_names',{c.edge_names});
writejson(fullfile(out,'compiled_network_input.json'),net);
mapping=struct('part_keys',{keys},'destination_index_MATLAB',dest,'destination_node_ids',{expected}, ...
    'mask_motor_gear_brake',mask,'inverter_loaded_in_thermal_domain',false,'values',c.values, ...
    'mapping_source','scripts/m2/m2_simulate.m: textual dest vector, not executed', ...
    'node_input_unit','W','schema','m2-lptn-concept-1.0','temperature_integration_executed',false);
writejson(fullfile(out,'source_mapping.json'),mapping);
units=struct;names=source.Properties.VariableNames;
for j=1:numel(names),units.(names{j})='W';end
units.start_s='s';units.end_s='s';units.speed_m_s='m/s';units.motor_rpm='rpm';units.motor_torque_Nm='N*m';units.segment_id='1';
meta=struct('scenario_id',cfg.scenario_id,'p1a_scenario_id',cfg.p1a_scenario_id,'p1a_commit',cfg.p1a_commit, ...
    'configuration_version',cfg.configuration_version,'model_version',p.metadata.model_version,'schema',p.metadata.model_version, ...
    'classification','S3_CONCEPT_INPUT_NOT_CALIBRATED','mode','engineering','side',cfg.side, ...
    'source_csv',[cfg.input_directory '/' cfg.side '_sources.csv'],'source_metadata',[cfg.input_directory '/' cfg.side '_sources.json'], ...
    'source_sampling',cfg.sampling_policy,'single_segment_adapter',cfg.single_segment_adapter, ...
    'input_files',pre.input_files,'workspace_head_before_run',pre.workspace_head,'m2_code_commit',pre.m2_code_commit, ...
    'preflight_sha256',sha256(fullfile(root,cfg.preflight_file)),'matlab_release',version('-release'), ...
    'configured_maximum_step_s',dt,'actual_interval_s',f.edges_s(2)-f.edges_s(1),'interval_count',height(source), ...
    'segment_labels',{f.segment_labels},'segment_boundaries_s',f.segment_boundaries_s,'mask_motor_gear_brake',mask, ...
    'units',units,'single_side_multiplier',1,'disc_face_multiplier',1, ...
    'inverter_loaded_in_thermal_domain',false,'calibrated_winding_heat_W',NaN, ...
    'raw_integral_J',f.raw_integral_J,'resampling_energy_residual_J',f.resampling_energy_residual_J, ...
    'unknowns',cfg.unknowns,'omission_policy',cfg.omission_policy,'topology_limit',cfg.topology_limit, ...
    'temperature_integration_executed',false,'cooldown_added',false,'preheat_added',false,'repeated_cycles_added',false, ...
    'forcing_csv_sha256',sha256(fullfile(out,'single_brake_forcing.csv')));
writejson(fullfile(out,'single_brake_forcing.json'),meta);
writejson(fullfile(out,'matlab_input_checks.json'),struct('status','PASS_INPUT_PREPARATION_ONLY', ...
    'network_node_count',c.N,'mapping_read_without_execution',true,'mat_file_readback','PASS', ...
    'profiled_m2_functions',{m2calls},'forbidden_temperature_functions_called',false, ...
    'interval_count',height(source),'duration_s',f.edges_s(end),'temperature_results_created',false));
fprintf('Prepared %d intervals / %.15g s, 13 nodes; MAT input readback PASS. No temperature integration.\n',height(source),f.edges_s(end));
diary off;
files=dir(out);records=struct('path',{},'bytes',{},'sha256',{});
for j=1:numel(files)
    if ~files(j).isdir,records(end+1)=struct('path',[cfg.output_directory '/' files(j).name], ...
        'bytes',files(j).bytes,'sha256',sha256(fullfile(out,files(j).name)));end %#ok<AGROW>
end
writejson(fullfile(out,'generated_files.json'),struct('files',records,'hash_definition','raw bytes SHA256'));
end

function h=sha256(path)
fid=fopen(path,'rb');assert(fid>=0);cl=onCleanup(@()fclose(fid));v=fread(fid,Inf,'*uint8');
md=java.security.MessageDigest.getInstance('SHA-256');md.update(v);h=lower(reshape(dec2hex(typecast(md.digest(),'uint8'),2).',1,[]));
end
function writejson(path,v)
fid=fopen(path,'w','n','UTF-8');assert(fid>=0);cl=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(nulls(v),'PrettyPrint',true));
end
function v=nulls(v)
if isstruct(v)
    keys=fieldnames(v);for j=1:numel(v),for k=1:numel(keys),v(j).(keys{k})=nulls(v(j).(keys{k}));end,end
elseif iscell(v),for j=1:numel(v),v{j}=nulls(v{j});end
elseif isempty(v),v=NaN;end
end
