function q=m1_emot(c, rpm, torque, active)
% Signed DC input, signed mechanical output. Heat is always dissipative.
if nargin<4, active=true(size(rpm)); end
assert(isequal(size(rpm),size(torque),size(active)),'m1:Dimensions','Speed, torque and active arrays must have identical shapes');
assert(c.stage.inputs.source_voltage_V==650,'m1:Voltage','Only the 650 V reference map is supported');
assert(all(isfinite(rpm)) && all(isfinite(torque)),'m1:Nonfinite','Finite inputs required');
assert(all(rpm>=0 & rpm<=max(c.map.speed_rpm)),'m1:MapBounds','EPA speed map ends at 13000 rpm');
assert(all(torque>=min(c.map.torque_Nm) & torque<=max(c.map.torque_Nm)),'m1:MapBounds','Outside numeric torque grid');
positive=interp1(c.map.speed_rpm,c.map.positive_torque_limit_Nm,rpm,'linear');
negative=interp1(c.map.speed_rpm,c.map.negative_torque_limit_Nm,rpm,'linear');
assert(all(torque<=positive+1e-8 & torque>=negative-1e-8),'m1:TorqueLimit','Outside reference torque envelope');
omega=rpm*(2*pi/60); pm=omega.*torque;
assert(all(abs(pm)<=60000+1e-5),'m1:PowerLimit','Outside declared peak power');
if any(torque(active)<0) && ~c.stage.assumptions.allow_estimated_regen_map
    error('m1:EstimatedRegenRejected','Negative torque map is estimated, not measured');
end
L=reshape(c.loss(rpm(:),torque(:)),size(rpm)); assert(all(isfinite(L) & L>=0));
% Inactive means an assumed disconnected inverter with omitted drag; no idle-map double counting.
assert(all(abs(torque(~active))<1e-12),'m1:InactiveTorque','Inactive motor cannot supply commanded torque');
L(~active)=c.stage.assumptions.unpowered_emot_loss_W;
pm(~active)=0; pdc=pm+L;
motor=nan(size(L)); inverter=nan(size(L)); ratio=nan(size(L));
drive=active & torque>0;
if any(drive)
    ratio(drive)=c.drive_ratio(rpm(drive)/13000,torque(drive)/200);
    motor(drive)=L(drive).*ratio(drive);
    inverter(drive)=L(drive).*(1-ratio(drive));
end
motor(~active)=0; inverter(~active)=0;
unknown=L; known=isfinite(motor) & isfinite(inverter); unknown(known)=0;
q=struct('mechanical_W',pm,'dc_W',pdc,'combined_heat_W',L, ...
    'motor_total_heat_estimated_W',motor,'inverter_heat_estimated_W',inverter, ...
    'unallocated_emot_heat_W',unknown,'winding_heat_W',nan(size(L)), ...
    'drive_split_ratio',ratio,'split_is_estimated',drive & isfinite(ratio), ...
    'regen_is_estimated',active & torque<0);
end
