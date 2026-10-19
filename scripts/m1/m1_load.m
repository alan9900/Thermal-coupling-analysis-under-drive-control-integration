function c = m1_load(root, strict)
% Load audited reference data. strict=true rejects unsupported thermal claims.
if nargin<2, strict=false; end
p=jsondecode(fileread(fullfile(root,'results','m1','inputs.json')));
c.base=p.vehicle_configuration; c.stage=p.stage_configuration; c.provenance=p.provenance;
assert(strcmp(c.base.metadata.version,'v0.4') && strcmp(c.base.drive.driven_axle,'rear'),'m1:Topology','Require V0.4 rear drive');
assert(~c.base.drive.differential_present && c.base.drive.independent_motor_count==2,'m1:Topology','No differential');
assert(c.base.brakes.rotor_speed_to_own_wheel_speed_ratio==1,'m1:Topology','Disc must follow its own wheel');
assert(isempty(c.base.drive.rear_motor_per_side.motor_loss_map_file),'m1:Evidence','Do not relabel EMOT as winding loss');
if strict
    error('m1:EvidenceGap','Validated motor internal losses, gearbox maps, heat partition and battery limit data are unavailable.');
end
mp=jsondecode(fileread(fullfile(root,c.stage.inputs.combined_emot_numeric)));
c.map=mp; c.map.speed_rpm=mp.speed_rpm(:); c.map.torque_Nm=mp.torque_Nm(:);
mechanical=c.map.speed_rpm*(2*pi/60)*c.map.torque_Nm';
loss=mp.electrical_power_W-mechanical;
assert(all(loss>=0,'all') && isequal(size(loss),[14 39]));
c.loss=griddedInterpolant({c.map.speed_rpm,c.map.torque_Nm},loss,'linear','none');
raw=readtable(fullfile(root,c.stage.inputs.separate_drive_efficiencies));
eta_m=raw.motor_efficiency_norm; eta_i=raw.inverter_efficiency_norm;
lm=1./eta_m-1; li=(1./eta_i-1)./eta_m;
fraction=lm./(lm+li);
assert(all(fraction>=0 & fraction<=1));
% Normalize coordinates before triangulation; return NaN outside measured hull.
c.drive_ratio=scatteredInterpolant(raw.speed_rpm/13000,raw.torque_Nm/200,fraction,'linear','none');
c.raw_drive=raw;
end
