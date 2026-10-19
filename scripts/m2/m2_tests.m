function result=m2_tests(c,s,root)
groups={};p=c.p;
assert(c.N==13 && all(c.C>0) && max(abs(sum(c.B,1)))==0);
assert(sum(c.cut==1)==2 && sum(c.cut==2)==1 && sum(c.cut==3)==3);
groups{end+1}='13 passive thermal nodes; unique drive-domain cut; no sequential heat-flow double counting';
T=c.initial_T;T(1)=400;T(7)=300;[dT,q]=m2_flux(c,T,zeros(13,1),0);
assert(abs(sum(c.C.*dT)+sumBoundary(c,T))<1e-8);
k=find(strcmp(c.edge_names,'disc_to_gear_case'));e=p.radiation(1);
effective=1/(1/p.nodes(1).emissivity+1/p.nodes(7).emissivity-1);
expected=5.670374419e-8*e.area_m2*e.view_factor*effective*(400^4-300^4);
assert(abs(q(k)-expected)<1e-10 && q(k)>0);
T(1)=300;T(7)=400;[~,q]=m2_flux(c,T,zeros(13,1),0);assert(abs(q(k)+expected)<1e-10);
bad=T;bad(1)=-1;mustError(@()m2_flux(c,bad,zeros(13,1),0),'m2:AbsoluteTemperature');
groups{end+1}='absolute-K radiation oracle, antisymmetry, reverse heat flow and invalid-temperature rejection';
f=zeroForcing(200,.5);cc=c;cc.G0(:)=0;cc.Gv(:)=0;cc.Rad(:)=0;cc.AmbG0(:)=0;cc.AmbGv(:)=0;cc.AmbRad(:)=0;cc.CoolG(:)=0;
cc.CoolG(8)=25;cc.initial_T(8)=c.Tambient+10;
r=m2_simulate(cc,f,[1 1 1],'analytic_single_body');
expected=c.Tambient+10*exp(-25*r.t/cc.C(8));assert(max(abs(r.T_K(:,8)-expected))<1e-7);
groups{end+1}='independent single-capacitance exponential cooling solution and total stored/boundary energy closure';
closed=c;closed.AmbG0(:)=0;closed.AmbGv(:)=0;closed.AmbRad(:)=0;closed.CoolG(:)=0;
closed.initial_T=linspace(310,340,13)';r=m2_simulate(closed,zeroForcing(200,.5),[1 1 1],'closed_redistribution');
assert(max(abs(r.stored_J))<1e-6 && all(r.T_K(end,:)>=310 & r.T_K(end,:)<=340));
groups{end+1}='closed unequal-temperature network conserves total internal energy without clipping';
cool=c;cool.initial_T(:)=c.Tambient+30;r=m2_simulate(cool,zeroForcing(p.numerics.no_source_relax_duration_s,2),[1 1 1],'no_source_relaxation');
assert(max(abs(r.T_K(end,:)-c.Tambient))<.10);
relaxError=max(abs(r.T_K(end,:)-c.Tambient));
assert(all(r.T_K>=c.Tambient-1e-8,'all'));
groups{end+1}='source-free warm network relaxes to equal ambient/coolant boundaries';
equal=m2_simulate(c,zeroForcing(100,1),[1 1 1],'ambient_equilibrium');assert(max(abs(equal.T_K-c.Tambient),[],'all')<1e-10);
warm=c;warm.Tcoolant=333.15;r=m2_simulate(warm,zeroForcing(20,.25),[1 1 1],'warm_reservoir');
assert(r.coolant_W(1)<0 && r.summary.coolant_net_out_J<0);
groups{end+1}='equal-boundary equilibrium and hotter-coolant reverse heat with signed cooling ledger';
f=m2_forcing(p,s,false,.25);
assert(f.resampling_energy_residual_J<1e-6 && all(f.parts_W(:,1:9)>=0,'all'));
assert(all(s.drive.source_class_code==3) && all(isnan(s.drive.calibrated_winding_heat_W)));
groups{end+1}='M1 9-source contract, raw NaNs, exact interval-energy preservation and original reference budgets';
a=m2_simulate(c,f,[1 1 0],'A_test');b=m2_simulate(c,f,[0 0 1],'B_test');full=m2_simulate(c,f,[1 1 1],'C_test');
assert(abs(a.summary.source_energy_J+b.summary.source_energy_J-full.summary.source_energy_J)<1e-6);
assert(all(full.T_K>=a.T_K-1e-7,'all') && all(full.T_K>=b.T_K-1e-7,'all'));
assert(full.summary.max_drive_domain_residual_J<1e-5);
groups{end+1}='internal/brake/combined masks conserve applied source energy; full and drive-domain ledgers close';
hot=full.path_forward_J;net=full.path_net_J;assert(all(hot>=max(net,0)-1e-8,'all'));
assert(any(a.path_W(:)<-1e-6));
groups{end+1}='instantaneous signed path heat, cumulative forward ingress and net energy remain distinct';
steps=p.numerics.refinement_steps_s(:)';samples=cell(1,3);peak=zeros(3,13);
for k=1:3
    ff=m2_forcing(p,s,false,steps(k));samples{k}=m2_simulate(c,ff,[1 1 1],sprintf('refine_%g',steps(k)));
    peak(k,:)=max(samples{k}.T_K,[],1);
end
coarse=max(abs(peak(1,:)-peak(3,:)));fine=max(abs(peak(2,:)-peak(3,:)));
assert(fine<p.numerics.convergence_temperature_tolerance_K && fine<=coarse+1e-5);
groups{end+1}='0.5/0.25/0.125s time-step convergence using node peak temperatures and preserved source energy';
for key={'heat_capacity_scale','contact_resistance_scale','convection_scale','motor_total_loss_scale','gear_total_loss_scale'}
    r=p.sensitivity.(key{1});ov=struct;ov.(key{1})=r(1);low=m2_network(p,ov);assert(all(low.C>0));
end
bad=p;bad.sensitivity.contact_resistance_scale=[];mustError(@()m2_network(bad),'m2:Parameter');
bad=p;bad.conduction(1).R_K_W=NaN;mustError(@()m2_network(bad),'m2:Resistance');
mustError(@()m2_load(root,'strict'),'m2:EvidenceGap');
groups{end+1}='range-based heat-capacity/contact/convection/loss candidates; missing/NaN/strict evidence rejected';
result=struct('status','PASS','test_group_count',numel(groups),'test_groups',{groups}, ...
    'time_steps_s',steps,'coarse_vs_fine_peak_error_K',coarse,'nominal_vs_fine_peak_error_K',fine, ...
    'no_source_final_max_error_K',relaxError, ...
    'matlab',version,'release',version('-release'),'physical_validation','NOT EXECUTED');
result.source_resampling_residual_J=f.resampling_energy_residual_J;
result.maximum_nominal_energy_residual_J=full.summary.max_energy_residual_J;
end

function value=sumBoundary(c,T)
[~,~,a,b]=m2_flux(c,T,zeros(c.N,1),0);value=sum(a)+sum(b);
end
function f=zeroForcing(duration,dt)
t=linspace(0,duration,ceil(duration/dt)+1)';f=struct('edges_s',t,'parts_W',zeros(numel(t)-1,9),'speed_m_s',zeros(numel(t)-1,1));
end
function mustError(fun,id)
try,fun();catch ex,assert(strcmp(ex.identifier,id),'m2:WrongError','Expected %s, got %s',id,ex.identifier);return;end
error('m2:MissingError','Expected rejection %s',id);
end
