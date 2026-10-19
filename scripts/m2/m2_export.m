function m2_export(c,r,f,out)
if ~exist(out,'dir'),mkdir(out);end
tab=table(r.t,'VariableNames',{'time_s'});
for j=1:c.N,tab.([c.ids{j} '_K'])=r.T_K(:,j);end
tab.source_total_W=r.source_total_W;tab.ambient_net_out_W=r.ambient_W;tab.coolant_net_out_W=r.coolant_W;
tab.source_energy_J=r.Y(:,c.N+1);tab.ambient_net_out_J=r.Y(:,c.N+2);tab.coolant_net_out_J=r.Y(:,c.N+3);
tab.stored_energy_change_J=r.stored_J;tab.energy_residual_J=r.energy_residual_J;tab.drive_energy_residual_J=r.drive_energy_residual_J;
tab.drive_source_energy_J=r.Y(:,end-1);tab.drive_boundary_net_out_J=r.Y(:,end);
for j=1:c.M
    tab.([c.edge_names{j} '_W'])=r.edge_W(:,j);
    tab.([c.edge_names{j} '_net_J'])=r.Y(:,c.N+3+j);
    tab.([c.edge_names{j} '_forward_J'])=r.Y(:,c.N+3+c.M+j);
end
paths={'radiation','hotair','solid'};
for k=1:3
    tab.([paths{k} '_into_drive_W'])=r.path_W(:,k);
    tab.([paths{k} '_net_J'])=r.path_net_J(:,k);tab.([paths{k} '_forward_J'])=r.path_forward_J(:,k);
end
writetable(tab,fullfile(out,[r.id '.csv']));
source=table(f.edges_s(1:end-1),f.edges_s(2:end),f.speed_m_s,f.motor_rpm,f.motor_torque_Nm, ...
    'VariableNames',{'start_s','end_s','speed_m_s','motor_rpm','motor_torque_Nm'});
names={'copper','iron','rotor_other','inverter_external','gear_mesh','gear_bearing','gear_other','disc','pad'};
for j=1:9,source.([names{j} '_engineering_W'])=f.parts_W(:,j);end
source.emot_reference_W=f.reference_budgets_W(:,1);source.gear_reference_W=f.reference_budgets_W(:,2);source.disc_contact_W=f.reference_budgets_W(:,3);
source.segment_id=f.segment_id;source.calibrated_winding_heat_W=nan(height(source),1);
writetable(source,fullfile(out,[r.id '_forcing.csv']));
meta=struct('id',r.id,'classification',r.configuration_class,'schema','m2-lptn-concept-1.0', ...
    'temperature_unit','K','mask_motor_gear_brake',r.mask,'parameters',r.parameters,'M1_tag',c.p.metadata.baseline_tag, ...
    'baseline_commit',c.p.metadata.baseline_commit,'segment_labels',{f.segment_labels},'segment_boundaries_s',f.segment_boundaries_s, ...
    'source_sampling','exact interval average of each piecewise-linear M1 segment; no cross-segment interpolation', ...
    'inverter_loaded_in_thermal_domain',false,'total_loss_sensitivity_recontrols_vehicle',false, ...
    'path_definition','unique cut into output bearing + gear + motor domain; shaft internal sequential flux not summed twice', ...
    'forward_definition','sum of time-integrated positive oriented flux on each cut edge; not positive part of a cancelling aggregate', ...
    'energy_quadrature','same RK4 quadrature as thermal state; CSV instantaneous flux is a diagnostic right-side sample', ...
    'node_ids',{c.ids},'heat_capacity_J_K',c.C,'drive_domain_indices',find(c.drive),'provenance',c.provenance);
fid=fopen(fullfile(out,[r.id '.json']),'w','n','UTF-8');cl=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(meta,'PrettyPrint',true));
end
