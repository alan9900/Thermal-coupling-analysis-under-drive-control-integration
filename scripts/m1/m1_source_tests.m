function result=m1_source_tests(c,root,traces,summary)
% Independent acceptance checks for the engineering source preparation layer.
groups={}; maxResidual=0;
for k=1:numel(traces)
    for side={'left','right'}
        q=m1_sources(c,traces{k},side{1},'engineering');
        M=q.copper_engineering_W+q.iron_engineering_W+q.rotor_other_engineering_W+q.inverter_engineering_W;
        G=q.gear_mesh_engineering_W+q.gear_bearing_engineering_W+q.gear_other_engineering_W;
        D=q.disc_engineering_W+q.pad_engineering_W;
        err=max(abs([M-q.emot_total_reference_W G-q.gear_total_assumed_W D-q.disc_contact_W]),[],'all');
        maxResidual=max(maxResidual,err); assert(err<1e-7);
        assert(abs(trapz(q.time_s,M-q.emot_total_reference_W))<1e-7);
        assert(abs(trapz(q.time_s,G-q.gear_total_assumed_W))<1e-7);
        assert(all(isnan(q.calibrated_winding_heat_W)) && all(q.source_class_code==3));
    end
end
groups{end+1}='46 single-side exports: motor, inverter, gear and disc instantaneous/integral closure';
idx=find(strcmp(summary.case_id,'stop_z06_bat30_road1')); tr=traces{idx};
[q,meta]=m1_sources(c,tr,'left','engineering');
assert(strcmp(meta.inverter_thermal_destination,'external_boundary_not_motor_internal'));
assert(~meta.original_calibrated_data_modified && ~meta.M2_executed);
groups{end+1}='engineering classification, raw NaN preservation and external inverter destination';
mustError(@()m1_sources(c,tr,'left','strict'),'m1:StrictEvidenceGap');
mustError(@()m1_sources(c,tr,'left','measurement'),'m1:Mode');
groups{end+1}='strict mode rejects internal loss output before any file write; invalid mode rejected';
[v,p]=m1_partition_parameters(c);
R=.077*(1+.00393*(v.winding_temperature_C-20))/(1+.00393);
n=q.motor_speed_rpm; T=abs(q.motor_torque_Nm);
I=T/v.torque_constant_Nm_per_Arms.*sqrt(1+v.field_weakening_current_factor*max(n/4500-1,0).^2);
expected=3*R*I.^2.*(1+v.ac_copper_speed_factor*(n/6000).^2);
assert(max(abs(expected-q.copper_raw_weight_W))<1e-9);
assert(all(abs(q.copper_engineering_W-expected.*q.motor_budget_normalization)<1e-8 | isnan(q.motor_budget_normalization)));
groups{end+1}='independent 3*R*Irms^2 raw weight and explicit motor-budget normalization';
meshRaw=v.gear_mesh_power_coefficient*abs(tr.motor_mechanical_power_W_left/.96);
assert(all(abs(q.gear_mesh_engineering_W-meshRaw.*q.gear_budget_normalization)<1e-8 | isnan(q.gear_budget_normalization)));
groups{end+1}='independent backdrive mesh weight and normalization; total gear loss unchanged';
low=m1_sources(c,tr,'left','engineering',struct('disc_heat_fraction',.85));
high=m1_sources(c,tr,'left','engineering',struct('disc_heat_fraction',.95));
assert(max(abs(high.disc_engineering_W-low.disc_engineering_W-.10*q.disc_contact_W))<1e-9);
assert(isequal(low.emot_total_reference_W,high.emot_total_reference_W));
assert(trapz(q.time_s,high.disc_engineering_W)>trapz(q.time_s,low.disc_engineering_W));
groups{end+1}='disc sensitivity exact linear slope with conserved disc-plus-pad heat';
for id={'high_soc_no_regen','temperature_charge_disabled'}
    k=find(strcmp(summary.case_id,id{1})); z=m1_sources(c,traces{k},'left','engineering');
    assert(all(z.emot_total_reference_W==0) && all(z.copper_engineering_W==0));
    assert(any(z.disc_engineering_W>0));
end
exit=q.vehicle_speed_m_s*3.6<5;
assert(all(q.motor_torque_Nm(exit)==0) && all(q.copper_engineering_W(exit)==0));
groups{end+1}='low-speed fade, high SOC and temperature-disabled regeneration retain friction heating';
k=find(strcmp(summary.case_id,'left_regen_unavailable'));
l=m1_sources(c,traces{k},'left','engineering'); r=m1_sources(c,traces{k},'right','engineering');
assert(all(l.emot_total_reference_W==0) && any(r.emot_total_reference_W>0));
assert(trapz(l.time_s,l.disc_engineering_W)>trapz(r.time_s,r.disc_engineering_W));
k=find(strcmp(summary.case_id,'unequal_wheel_speed_port_test'));
l=m1_sources(c,traces{k},'left','engineering'); r=m1_sources(c,traces{k},'right','engineering');
assert(max(abs(l.motor_speed_rpm-r.motor_speed_rpm))>100);
assert(max(abs(l.motor_speed_rpm*2*pi/60-9*l.disc_speed_rad_s))<1e-8);
groups{end+1}='independent left/right speed and one-side regen-failure interface, no doubling of single-side heat';
bad=c; bad.partition.parameters=rmfield(p.parameters,'iron_eddy_ref_W');
mustError(@()m1_sources(bad,tr,'left','engineering'),'m1:MissingParameter');
bad=c; bad.partition.parameters.iron_eddy_ref_W=[];
mustError(@()m1_sources(bad,tr,'left','engineering'),'m1:InvalidRange');
bad=c; bad.partition.parameters.fallback_inverter_fraction=[.5 .2 .1];
mustError(@()m1_sources(bad,tr,'left','engineering'),'m1:InvalidRange');
mustError(@()m1_sources(c,tr,'left','engineering',struct('disc_heat_fraction',1)),'m1:ParameterOutsideRange');
mustError(@()m1_sources(c,tr,'front','engineering'),'m1:Side');
badtr=tr; badtr.time_s(2)=badtr.time_s(1);
mustError(@()m1_sources(c,badtr,'left','engineering'),'m1:SourceTime');
groups{end+1}='missing/null/reversed/out-of-range parameters, invalid side and duplicate time rejected';
% Every parameter endpoint: check timewise enclosures against independent runs.
names=fieldnames(v);
for j=1:numel(names)
    range=p.parameters.(names{j});
    for endpoint=[1 3]
        ov=struct; ov.(names{j})=range(endpoint);
        z=m1_sources(c,tr,'left','engineering',ov); checkBounds(z);
    end
end
groups{end+1}='all 32 one-at-a-time parameter endpoints inside deterministic interval enclosure';
assert(isempty(c.base.drive.rear_motor_per_side.motor_loss_map_file));
assert(isempty(c.partition.metadata.actual_internal_loss_map));
assert(exist(fullfile(root,'data','raw','m1','manifest.json'),'file')==2);
groups{end+1}='M0 reference unknowns and actual-map nulls preserved; traceable source manifest exists';
result=struct('status','PASS','test_group_count',numel(groups),'test_groups',{groups}, ...
    'single_side_cases',2*numel(traces),'maximum_partition_residual_W',maxResidual, ...
    'strict_mode','EXPECTED_REJECTION','experimental_validation','NOT EXECUTED','M2_executed',false, ...
    'matlab',version,'release',version('-release'));
end

function checkBounds(z)
names={'copper','iron','rotor_other','inverter','gear_mesh','gear_bearing','gear_other','disc','pad'};
for j=1:numel(names)
    key=names{j}; assert(all(z.([key '_engineering_W'])>=z.([key '_lower_W'])-1e-7));
    assert(all(z.([key '_engineering_W'])<=z.([key '_upper_W'])+1e-7));
end
end

function mustError(fun,id)
try
    fun();
catch exception
    assert(strcmp(exception.identifier,id),'m1:WrongError','Expected %s; got %s',id,exception.identifier); return
end
error('m1:MissingError','Expected rejection %s',id);
end
