function r=m2_simulate(c,f,mask,id)
% RK4 with exact interval-average source input and the SAME quadrature for heat ledgers.
if nargin<4,id='case';end
assert(numel(mask)==3 && all(ismember(mask,[0 1])),'m2:Mask','motor/gear/brake masks');
N=c.N; M=c.M; t=f.edges_s; steps=numel(t)-1;
assert(all(diff(t)>0) && size(f.parts_W,1)==steps,'m2:Time','One source average per interval');
parts=f.parts_W; parts(:,1:3)=parts(:,1:3)*c.values.motor_total_loss_scale*mask(1);
parts(:,4)=parts(:,4)*c.values.motor_total_loss_scale; % inverter always outside this thermal domain
parts(:,5:7)=parts(:,5:7)*c.values.gear_total_loss_scale*mask(2);
parts(:,8:9)=parts(:,8:9)*mask(3);
Q=zeros(steps,N);dest=[10 9 11 0 5 4 6 1 2];
for k=1:9,if dest(k)>0,Q(:,dest(k))=Q(:,dest(k))+parts(:,k);end,end
% Layout: T, source, ambient, coolant, all edge net, all edge forward-positive, drive-source, drive-boundary.
Y=zeros(steps+1,N+3+2*M+2);Y(1,1:N)=c.initial_T';
qedge=zeros(steps+1,M);qambient=zeros(steps+1,1);qcool=qambient;qsource=qambient;
for k=1:steps
    h=t(k+1)-t(k);x=Y(k,:)'; heat=Q(k,:)';v=f.speed_m_s(k);
    a=rhs(x,heat,v);b=rhs(x+h*a/2,heat,v);d=rhs(x+h*b/2,heat,v);e=rhs(x+h*d,heat,v);
    Y(k+1,:)=(x+h*(a+2*b+2*d+e)/6)';
    [~,qe,qa,qc]=m2_flux(c,x(1:N),heat,v);qedge(k,:)=qe';qambient(k)=sum(qa);qcool(k)=sum(qc);qsource(k)=sum(heat);
end
[~,qe,qa,qc]=m2_flux(c,Y(end,1:N)',Q(end,:)',f.speed_m_s(end));
qedge(end,:)=qe';qambient(end)=sum(qa);qcool(end)=sum(qc);qsource(end)=sum(Q(end,:));
T=Y(:,1:N); Estored=(T-c.initial_T')*c.C;
energy=Y(:,N+1)-Y(:,N+2)-Y(:,N+3)-Estored;
Enet=Y(:,N+3+(1:M));Epos=Y(:,N+3+M+(1:M));
pathNet=zeros(numel(t),3);pathPos=pathNet;pathQ=pathNet;
for k=1:3
    take=c.cut==k;pathNet(:,k)=sum(Enet(:,take),2);pathPos(:,k)=sum(Epos(:,take),2);pathQ(:,k)=sum(qedge(:,take),2);
end
driveStored=(T(:,c.drive)-c.initial_T(c.drive)')*c.C(c.drive);
driveEnergy=Y(:,end-1)+sum(pathNet,2)-Y(:,end)-driveStored;
denom=max(1,Y(end,N+1));
summary=struct('case_id',id,'duration_s',t(end),'sample_count',numel(t),'source_energy_J',Y(end,N+1), ...
    'ambient_net_out_J',Y(end,N+2),'coolant_net_out_J',Y(end,N+3),'stored_energy_change_J',Estored(end), ...
    'max_energy_residual_J',max(abs(energy)),'energy_residual_relative',max(abs(energy))/denom, ...
    'max_drive_domain_residual_J',max(abs(driveEnergy)), ...
    'radiation_net_J',pathNet(end,1),'hotair_net_J',pathNet(end,2),'solid_net_J',pathNet(end,3), ...
    'radiation_forward_J',pathPos(end,1),'hotair_forward_J',pathPos(end,2),'solid_forward_J',pathPos(end,3), ...
    'excluded_inverter_energy_J',sum(parts(:,4).*diff(t)), ...
    'peak_disc_C',max(T(:,1))-273.15,'peak_gear_case_C',max(T(:,7))-273.15, ...
    'peak_oil_C',max(T(:,6))-273.15,'peak_winding_C',max(T(:,10))-273.15,'final_winding_C',T(end,10)-273.15);
assert(summary.energy_residual_relative<c.p.numerics.energy_relative_tolerance && ...
    max(abs(driveEnergy))/denom<c.p.numerics.energy_relative_tolerance,'m2:Energy','Thermal energy ledger does not close');
r=struct('id',id,'t',t,'T_K',T,'Y',Y,'source_W',Q,'edge_W',qedge,'ambient_W',qambient, ...
    'coolant_W',qcool,'source_total_W',qsource,'path_W',pathQ,'path_net_J',pathNet,'path_forward_J',pathPos, ...
    'stored_J',Estored,'energy_residual_J',energy,'drive_energy_residual_J',driveEnergy,'summary',summary, ...
    'mask',mask,'parameters',c.values,'configuration_class','S3_CONCEPT_PREDICTION_NOT_CALIBRATED');

    function z=rhs(x,heat,v)
        [dT,q,ambient,coolant]=m2_flux(c,x(1:N),heat,v);
        z=[dT;sum(heat);sum(ambient);sum(coolant);q;max(q,0);sum(heat(c.drive));sum(ambient(c.drive)+coolant(c.drive))];
    end
end
