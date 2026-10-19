function run_m1_sources
% Prepare/verify inputs for a FUTURE M2. No thermal state is integrated.
root=fileparts(fileparts(fileparts(mfilename('fullpath')))); c=m1_load(root);
out=fullfile(root,'results','m1','engineering'); dest=fullfile(out,'interface');
if ~exist(dest,'dir'), mkdir(dest); end
s=load(fullfile(root,'results','m1','m1_results.mat'),'traces','summary','input_provenance');
assert(isfield(s,'input_provenance'),'m1:StaleTrace','Dynamics provenance missing; re-run run_m1');
m1_check_trace_provenance(c,s.input_provenance);
tests=m1_source_tests(c,root,s.traces,s.summary); writejson(fullfile(out,'tests.json'),tests);
energies={}; maxResidual=0;
for k=1:height(s.summary)
    for side={'left','right'}
        [q,meta]=m1_sources(c,s.traces{k},side{1},'engineering');
        id=char(s.summary.case_id(k)); meta.case_id=id;
        meta.trace_file=['results/m1/traces/' id '.csv'];
        base=[id '_' side{1}];
        writetable(q,fullfile(dest,[base '.csv'])); writejson(fullfile(dest,[base '.json']),meta);
        energies{end+1}=energyRow(q,id,side{1},'nominal'); %#ok<AGROW>
        maxResidual=max(maxResidual,max(abs([q.emot_partition_residual_W q.gear_partition_residual_W q.disc_partition_residual_W]),[],'all'));
    end
end
E=struct2table([energies{:}]); writetable(E,fullfile(out,'nominal_energies.csv'));
[v,p]=m1_partition_parameters(c); names=fieldnames(v); rows={}; rng(p.controls.random_seed,'twister');
choices={struct}; ids={'nominal'};
for j=1:numel(names)
    r=p.parameters.(names{j});
    for endpoint=[1 3]
        ov=struct; ov.(names{j})=r(endpoint); choices{end+1}=ov; %#ok<AGROW>
        ids{end+1}=sprintf('%s_endpoint%d',names{j},endpoint); %#ok<AGROW>
    end
end
for sample=1:p.controls.joint_parameter_samples
    ov=struct;
    for j=1:numel(names)
        r=p.parameters.(names{j}); ov.(names{j})=r(1)+rand*(r(3)-r(1));
    end
    choices{end+1}=ov; ids{end+1}=sprintf('joint_box_sample_%03d',sample); %#ok<AGROW>
end
% Store every actual scenario parameter vector for reproducibility.
parameterRows=cell(size(choices));
for j=1:numel(choices)
    x=m1_partition_parameters(c,choices{j}); x.scenario=ids{j}; parameterRows{j}=x;
end
writetable(struct2table([parameterRows{:}]),fullfile(out,'sensitivity_parameters.csv'));
for k=1:numel(p.controls.sensitivity_cases)
    id=char(p.controls.sensitivity_cases{k}); idx=find(strcmp(s.summary.case_id,id));
    for j=1:numel(choices)
        z=m1_sources(c,s.traces{idx},'left','engineering',choices{j});
        rows{end+1}=energyRow(z,id,'left',ids{j}); %#ok<AGROW>
    end
end
sensitivity=struct2table([rows{:}]); writetable(sensitivity,fullfile(out,'sensitivity_energies.csv'));
writejson(fullfile(out,'validation.json'),struct('status','PASS','concept_numerical_gate','PASS_PENDING_RESEARCHER_REVIEW', ...
    'stage_status','PARTIAL_REAL_COMPONENT_CALIBRATION','single_side_exports',height(E), ...
    'test_groups',tests.test_group_count,'scenario_count_per_case',numel(choices), ...
    'sensitivity_case_count',numel(p.controls.sensitivity_cases),'sensitivity_runs',height(sensitivity), ...
    'maximum_partition_residual_W',maxResidual,'interval_enclosure_checks','PASS_ALL_RUNS', ...
    'uncertainty_interpretation','deterministic conditional box, NOT statistical confidence', ...
    'strict_mode','EXPECTED_REJECTION','M1_approved',false,'M1_tag_created',false,'M2_executed',false));
save(fullfile(out,'partition_results.mat'),'E','sensitivity','choices','tests');
plots(c,s,out,E,sensitivity);
disp(tests); disp(sensitivity(1:3,:));
end

function row=energyRow(q,id,side,scenario)
row=struct('case_id',id,'side',side,'scenario',scenario);
keys={'copper','iron','rotor_other','inverter','gear_mesh','gear_bearing','gear_other','disc','pad'};
for k=1:numel(keys)
    key=keys{k}; row.([key '_kJ'])=trapz(q.time_s,q.([key '_engineering_W']))/1000;
    row.([key '_lower_kJ'])=trapz(q.time_s,q.([key '_lower_W']))/1000;
    row.([key '_upper_kJ'])=trapz(q.time_s,q.([key '_upper_W']))/1000;
end
scale=q.motor_budget_normalization; active=isfinite(scale);
if any(active), row.motor_scale_min=min(scale(active)); row.motor_scale_max=max(scale(active));
else, row.motor_scale_min=NaN; row.motor_scale_max=NaN; end
end

function plots(c,s,out,E,sensitivity)
ids={'stop_z06_bat30_road1','short_drive_0_to_80'};
f=figure('Visible','off','Color','w','Position',[50 50 1200 740]); tiledlayout(2,2);
for j=1:2
    tr=s.traces{find(strcmp(s.summary.case_id,ids{j}))}; q=m1_sources(c,tr,'left','engineering');
    nexttile; area(q.time_s,[q.copper_engineering_W q.iron_engineering_W q.rotor_other_engineering_W q.inverter_engineering_W]/1000);
    hold on; plot(q.time_s,q.emot_total_reference_W/1000,'k--','LineWidth',1.2);
    xlabel('Time (s)'); ylabel('Single-side heat (kW)'); title({ids{j},'S3 ENGINEERING allocation; EPA reference/estimated total'},'Interpreter','none','FontSize',10);
    legend('Copper','Iron','Rotor/other','Inverter external','EMOT total','Location','best'); grid on;
    nexttile; plot(q.time_s,[q.gear_mesh_engineering_W q.gear_bearing_engineering_W q.gear_other_engineering_W]/1000,'LineWidth',1.4);
    xlabel('Time (s)'); ylabel('Single-side gear heat (kW)'); title('S3 ENGINEERING; fixed total gearbox-loss budget');
    legend('Mesh','Bearing','Oil/seal/other','Location','best'); grid on;
end
exportgraphics(f,fullfile(out,'component_source_power.png'),'Resolution',180);
exportgraphics(f,fullfile(out,'component_source_power.svg'),'ContentType','vector'); close(f);
f=figure('Visible','off','Color','w','Position',[50 50 1200 730]); tiledlayout(2,2);
for j=1:2
    tr=s.traces{find(strcmp(s.summary.case_id,ids{j}))}; q=m1_sources(c,tr,'left','engineering');
    nexttile; hold on;
    fill([q.time_s;flipud(q.time_s)],[q.copper_lower_W;flipud(q.copper_upper_W)]/1000,[.8 .88 1],'EdgeColor','none');
    plot(q.time_s,q.copper_engineering_W/1000,'b','LineWidth',1.5);
    xlabel('Time (s)'); ylabel('Copper allocation (kW)'); title({ids{j},'S3 conditional interval; NOT measured confidence'},'Interpreter','none');
    legend('Parameter-box enclosure','Nominal'); grid on;
end
nexttile; take=strcmp(E.case_id,'stop_z06_bat30_road1') & strcmp(E.side,'left');
keys={'copper','iron','rotor_other','inverter','gear_mesh','gear_bearing','gear_other','disc','pad'};
nom=zeros(1,9); low=nom; high=nom;
for k=1:9, key=keys{k}; nom(k)=E.([key '_kJ'])(take); low(k)=E.([key '_lower_kJ'])(take); high(k)=E.([key '_upper_kJ'])(take); end
errorbar(1:9,nom,nom-low,high-nom,'o','LineWidth',1.3); xticks(1:9); xticklabels(keys); xtickangle(35);
ylabel('Single-side energy (kJ)'); title('S3 marginal envelopes: extrema NOT simultaneous'); grid on;
nexttile; z=sensitivity(strcmp(sensitivity.case_id,'stop_z06_bat30_road1'),:);
scatter(z.copper_kJ,z.inverter_kJ,12,z.iron_kJ,'filled'); colorbar; xlabel('Copper energy (kJ)'); ylabel('External inverter energy (kJ)');
title('S3 joint-box + endpoint sensitivity; color = iron kJ'); grid on;
exportgraphics(f,fullfile(out,'uncertainty_sensitivity.png'),'Resolution',180);
exportgraphics(f,fullfile(out,'uncertainty_sensitivity.svg'),'ContentType','vector'); close(f);
end

function writejson(path,value)
fid=fopen(path,'w','n','UTF-8'); assert(fid>=0); cl=onCleanup(@()fclose(fid));
fprintf(fid,'%s\n',jsonencode(value,'PrettyPrint',true));
end
