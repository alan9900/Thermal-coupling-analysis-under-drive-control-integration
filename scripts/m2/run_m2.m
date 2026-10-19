function run_m2
root=fileparts(fileparts(fileparts(mfilename('fullpath'))));addpath(fullfile(root,'scripts','m1'));
out=fullfile(root,'results','m2');casesDir=fullfile(out,'cases');if ~exist(casesDir,'dir'),mkdir(casesDir);end
c=m2_load(root);p=c.p;s=m2_segments(root,p);
save(fullfile(out,'source_segments.mat'),'s');
dt=p.numerics.maximum_step_s;f=m2_forcing(p,s,false,dt);fd=m2_forcing(p,s,true,dt);
tests=m2_tests(c,s,root);writejson(fullfile(out,'tests.json'),tests);
results={};models={};forces={};
masks={[1 1 0],[0 0 1],[1 1 1],[1 1 1]};names={'A_internal_only','B_brake_only','C_combined','D_preheat_braking'};
for k=1:4
    forcing=f;if k==4,forcing=fd;end
    results{k}=m2_simulate(c,forcing,masks{k},names{k});models{k}=c;forces{k}=forcing;
    m2_export(c,results{k},forcing,casesDir);
end
% Path-removal interventions are not additive temperature contributions.
for k=1:3
    enabled=[1 1 1];enabled(k)=0;cc=m2_network(p,struct('path_enabled',enabled));cc.provenance=c.provenance;
    name=sprintf('C_remove_path_%d',k);r=m2_simulate(cc,f,[1 1 1],name);
    results{end+1}=r;models{end+1}=cc;forces{end+1}=f; %#ok<AGROW>
    m2_export(cc,r,f,casesDir);
end
summary=struct2table(cellfun(@(r)r.summary,results,'UniformOutput',true));
% cellfun struct output can be a row; struct2table makes one row per case.
writetable(summary,fullfile(out,'case_summary.csv'));
comparison=table(string(c.ids(:)),max(results{3}.T_K-results{1}.T_K,[],1)', ...
    (max(results{3}.T_K,[],1)-max(results{1}.T_K,[],1))', ...
    'VariableNames',{'node','max_C_minus_A_K','peak_C_minus_peak_A_K'});
for k=1:3,comparison.(sprintf('peak_C_minus_remove_path%d_K',k))=(max(results{3}.T_K,[],1)-max(results{4+k}.T_K,[],1))';end
writetable(comparison,fullfile(out,'coupling_comparison.csv'));
% Physical-parameter and TOTAL loss error sensitivities, keeping coherent parts.
sensResults={};sensRows={};keys=fieldnames(p.sensitivity);
for k=1:numel(keys)
    range=p.sensitivity.(keys{k});
    for endpoint=[1 3]
        ov=struct;ov.(keys{k})=range(endpoint);cc=m2_network(p,ov);
        id=sprintf('%s_endpoint%d',keys{k},endpoint);r=m2_simulate(cc,f,[1 1 1],id);
        sensResults{end+1}=compact(r);z=r.summary;z.parameter=keys{k};z.value=range(endpoint);sensRows{end+1}=z; %#ok<AGROW>
    end
end
% Coherent M1 source-allocation alternatives; do not combine marginal upper bounds.
for k=1:2
    raw=jsondecode(fileread(fullfile(root,'results','m1','inputs.json')));params=raw.engineering_partition_configuration.parameters;
    ov=struct;
    choose={'torque_constant_Nm_per_Arms','iron_hysteresis_ref_W','iron_eddy_ref_W','rotor_speed_squared_ref_W','fallback_inverter_fraction'};
    for j=1:numel(choose),v=params.(choose{j});if k==1,ov.(choose{j})=v(1);else,ov.(choose{j})=v(3);end,end
    ss=m2_segments(root,p,ov);ff=m2_forcing(p,ss,false,dt);id=sprintf('coherent_M1_allocation_%d',k);
    r=m2_simulate(c,ff,[1 1 1],id);sensResults{end+1}=compact(r);z=r.summary;z.parameter='coherent_M1_allocation';z.value=k;sensRows{end+1}=z; %#ok<AGROW>
end
sensitivity=struct2table([sensRows{:}]);writetable(sensitivity,fullfile(out,'sensitivity_summary.csv'));
refinedD=m2_simulate(c,m2_forcing(p,s,true,dt/2),[1 1 1],'D_refined');
Derr=max(abs(max(refinedD.T_K,[],1)-max(results{4}.T_K,[],1)));
assert(Derr<p.numerics.convergence_temperature_tolerance_K,'m2:Convergence','Preheat case time-step error too large');
validation=struct('status','PASS','stage_status','CONCEPT_PREDICTION_PENDING_REVIEW','node_count',c.N, ...
    'primary_cases',4,'path_interventions',3,'sensitivity_cases',numel(sensResults), ...
    'test_groups',tests.test_group_count,'D_time_refinement_peak_error_K',Derr, ...
    'maximum_main_energy_residual_relative',max(summary.energy_residual_relative), ...
    'maximum_main_drive_residual_J',max(summary.max_drive_domain_residual_J), ...
    'high_load_preheat_motor_power_each_W',s.hold_motor_mechanical_W, ...
    'preheat_continuous_capability','UNVERIFIED; instantaneous envelope only, engineering stress scenario', ...
    'no_load_drag_and_temperature_loss_feedback','NOT MODELLED','M1_tag',p.metadata.baseline_tag, ...
    'M1_merge_commit',p.metadata.baseline_commit,'matlab',version,'release',version('-release'), ...
    'experimental_validation','NOT EXECUTED','M3_started',false);
writejson(fullfile(out,'validation.json'),validation);
save(fullfile(out,'m2_results.mat'),'results','summary','comparison','sensResults','sensitivity','tests','validation','refinedD');
% Compiled coefficients make every flow reconstructible independently.
net=struct('ids',{c.ids},'C_J_K',c.C,'from',c.from,'to',c.to,'G0_W_K',c.G0,'Gv',c.Gv, ...
    'Rad_W_K4',c.Rad,'cut_group',c.cut,'AmbG0',c.AmbG0,'AmbGv',c.AmbGv,'AmbRad',c.AmbRad, ...
    'CoolG',c.CoolG,'Tambient_K',c.Tambient,'Tcoolant_K',c.Tcoolant,'drive',c.drive,'edge_names',{c.edge_names});
writejson(fullfile(out,'compiled_network.json'),net);
m2_plots(c,results,sensitivity,comparison,out);
disp(summary(:,{'case_id','peak_disc_C','peak_gear_case_C','peak_winding_C','energy_residual_relative'}));disp(validation);
end

function s=compact(r)
s=rmfield(r,{'Y','source_W','edge_W','ambient_W','coolant_W','source_total_W','stored_J','energy_residual_J','drive_energy_residual_J'});
end
function writejson(path,value)
fid=fopen(path,'w','n','UTF-8');assert(fid>=0);cl=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(value,'PrettyPrint',true));
end
