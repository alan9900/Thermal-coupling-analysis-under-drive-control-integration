function c=m2_network(p,overrides)
% All engineering candidates are separate from original unknown actual inputs.
if nargin<2, overrides=struct; end
assert(strcmp(p.metadata.temperature_unit,'K'),'m2:Unit','Internal temperature must be K');
unknown=struct2cell(p.unknown_actual); assert(all(cellfun(@isempty,unknown)),'m2:Evidence','Do not relabel assumed parameters as calibrated');
keys=fieldnames(p.sensitivity); v=struct;
assert(isempty(setdiff(fieldnames(overrides),[keys;{'path_enabled'}])),'m2:UnknownParameter','Unknown override');
for k=1:numel(keys)
    key=keys{k}; r=p.sensitivity.(key);
    assert(isnumeric(r) && numel(r)==3 && all(isfinite(r)) && all(diff(r(:))>=0) && r(1)>0, ...
        'm2:Parameter','Every uncertainty parameter requires finite positive [lower nominal upper]');
    v.(key)=r(2);
    if isfield(overrides,key), v.(key)=overrides.(key); end
    a=v.(key); assert(isscalar(a) && isfinite(a) && a>=r(1) && a<=r(3),'m2:Parameter','Override outside range');
end
path_enabled=[1 1 1]; if isfield(overrides,'path_enabled'), path_enabled=overrides.path_enabled; end
assert(numel(path_enabled)==3 && all(ismember(path_enabled,[0 1])),'m2:Parameter','Three path switches required');
ids={p.nodes.id}; N=numel(ids); assert(N==13 && numel(unique(ids))==N,'m2:Topology','13 distinct dynamic nodes');
c=struct('p',p,'values',v,'ids',{ids},'N',N,'sigma',5.670374419e-8,'path_enabled',path_enabled);
c.C=[p.nodes.mass_kg]'.*[p.nodes.cp_J_kgK]'*v.heat_capacity_scale;
assert(all(isfinite(c.C) & c.C>0),'m2:HeatCapacity','Positive finite heat capacity required');
c.drive=ismember(ids,p.drive_domain)'; c.Tambient=p.cooling.ambient_temperature_K; c.Tcoolant=v.coolant_temperature_K;
assert(c.Tambient>=200 && c.Tcoolant>=200,'m2:Unit','Boundary temperatures must be absolute K');
c.initial_T=c.Tambient*ones(N,1);
c.from=[]; c.to=[]; c.G0=[];c.Gv=[];c.Rad=[];c.cut=[];c.edge_names={};
% Selected R include the uncertain contacts, not every internal fluid exchange.
contacts=[1 2 3 4 5 10 11 12 15];
for k=1:numel(p.conduction)
    e=p.conduction(k); R=e.R_K_W;
    assert(isscalar(R) && isfinite(R) && R>0,'m2:Resistance','Positive equivalent R required');
    if ismember(k,contacts),R=R*v.contact_resistance_scale;end
    c=append(c,e.from,e.to,1/R,0,0,e.cut);
end
for k=1:numel(p.convection)
    e=p.convection(k); c=append(c,e.from,e.to,e.area_m2*e.h0_W_m2K*v.convection_scale, ...
        e.area_m2*e.hv*v.convection_scale,0,e.cut);
end
for k=1:numel(p.radiation)
    e=p.radiation(k); a=find(strcmp(ids,e.from));b=find(strcmp(ids,e.to));
    eps1=p.nodes(a).emissivity;eps2=p.nodes(b).emissivity;
    assert(eps1>0 && eps1<=1 && eps2>0 && eps2<=1 && e.view_factor>=0 && e.view_factor<=1,'m2:Radiation','Invalid gray exchange');
    effective=1/(1/eps1+1/eps2-1);
    c=append(c,e.from,e.to,0,0,c.sigma*e.area_m2*e.view_factor*effective*v.radiation_exchange_scale,e.cut);
end
c.M=numel(c.from); c.B=zeros(N,c.M);
for j=1:c.M
    c.B(c.from(j),j)=1;c.B(c.to(j),j)=-1;
    crossed=~c.drive(c.from(j)) && c.drive(c.to(j));
    assert((c.cut(j)>0)==crossed && ~(c.drive(c.from(j)) && ~c.drive(c.to(j))), ...
        'm2:Cut','Every crossing must be uniquely oriented into drive domain');
    if c.cut(j)>0 && ~path_enabled(c.cut(j)),c.G0(j)=0;c.Gv(j)=0;c.Rad(j)=0;end
end
c.AmbG0=zeros(N,1);c.AmbGv=c.AmbG0;c.AmbRad=c.AmbG0;c.CoolG=c.AmbG0;
for k=1:numel(p.ambient_convection)
    e=p.ambient_convection(k);j=find(strcmp(ids,e.node));
    c.AmbG0(j)=c.AmbG0(j)+e.area_m2*e.h0_W_m2K*v.convection_scale;
    c.AmbGv(j)=c.AmbGv(j)+e.area_m2*e.hv*v.convection_scale;
end
for k=1:numel(p.ambient_radiation)
    e=p.ambient_radiation(k);j=find(strcmp(ids,e.node));
    c.AmbRad(j)=c.AmbRad(j)+c.sigma*e.area_m2*e.view_factor*p.nodes(j).emissivity;
end
c.CoolG(strcmp(ids,p.cooling.node))=p.cooling.conductance_W_K*v.coolant_conductance_scale;
assert(all([c.G0 c.Gv c.Rad c.AmbG0' c.AmbGv' c.AmbRad' c.CoolG']>=0),'m2:Conductance','Passive conductances must be nonnegative');
end

function c=append(c,a,b,g0,gv,rad,cut)
i=find(strcmp(c.ids,a));j=find(strcmp(c.ids,b));assert(numel(i)==1 && numel(j)==1 && i~=j,'m2:Topology','Invalid edge');
c.from(end+1)=i;c.to(end+1)=j;c.G0(end+1)=g0;c.Gv(end+1)=gv;c.Rad(end+1)=rad;c.cut(end+1)=cut;
c.edge_names{end+1}=[a '_to_' b];
end
