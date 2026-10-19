function [values,p]=m1_partition_parameters(c,overrides)
% Every uncertainty range is required, even for nominal engineering export.
if nargin<2, overrides=struct; end
assert(isfield(c,'partition'),'m1:MissingPartition','Engineering configuration required');
p=c.partition;
required={'torque_constant_Nm_per_Arms','winding_temperature_C','ac_copper_speed_factor', ...
    'field_weakening_current_factor','iron_hysteresis_ref_W','iron_eddy_ref_W', ...
    'rotor_speed_squared_ref_W','motor_stray_load_ref_W','drive_inverter_ratio_multiplier', ...
    'fallback_inverter_fraction','gear_mesh_power_coefficient','gear_bearing_torque_Nm', ...
    'gear_bearing_load_coefficient','gear_churning_ref_W','gear_seal_torque_Nm','disc_heat_fraction'};
assert(isfield(p,'parameters') && all(isfield(p.parameters,required)), ...
    'm1:MissingParameter','All engineering uncertainty parameters must be explicit');
assert(isempty(setdiff(fieldnames(p.parameters),required)) && isempty(setdiff(fieldnames(overrides),required)), ...
    'm1:UnknownParameter','Unknown parameter name');
values=struct;
for k=1:numel(required)
    key=required{k}; range=p.parameters.(key);
    assert(isnumeric(range) && numel(range)==3 && all(isfinite(range)) && all(diff(range(:))>=0), ...
        'm1:InvalidRange','%s requires ordered [lower nominal upper]',key);
    if strcmp(key,'winding_temperature_C')
        assert(range(1)>=-20 && range(3)<=180,'m1:InvalidRange','Temperature proxy outside supported range');
    else
        assert(range(1)>=0,'m1:InvalidRange','Negative loss parameter');
    end
    if ismember(key,{'fallback_inverter_fraction','disc_heat_fraction'})
        assert(range(1)>0 && range(3)<1,'m1:InvalidRange','Heat fraction must lie strictly in (0,1)');
    end
    if ismember(key,{'torque_constant_Nm_per_Arms','drive_inverter_ratio_multiplier'})
        assert(range(1)>0,'m1:InvalidRange','Positive conversion factors required');
    end
    value=range(2);
    if isfield(overrides,key), value=overrides.(key); end
    assert(isnumeric(value) && isscalar(value) && isfinite(value) && value>=range(1) && value<=range(3), ...
        'm1:ParameterOutsideRange','%s override outside configured bounds',key);
    values.(key)=value;
end
ref={'phase_resistance_ohm','resistance_temperature_C','copper_alpha_20_per_K','reference_speed_rpm','reference_torque_Nm'};
assert(isfield(p,'reference') && all(isfield(p.reference,ref)),'m1:MissingParameter','Reference values absent');
for k=1:numel(ref)
    val=p.reference.(ref{k});
    assert(isnumeric(val) && isscalar(val) && isfinite(val) && val>0,'m1:MissingParameter','Invalid reference value');
end
assert(isfield(p,'controls') && isscalar(p.controls.field_weakening_start_rpm) && ...
    isfinite(p.controls.field_weakening_start_rpm) && p.controls.field_weakening_start_rpm>0, ...
    'm1:MissingParameter','Positive weakening proxy onset required');
assert(p.controls.no_load_gear_drag_omitted && p.controls.interval_bounds_hold_total_emot_and_gear_fixed, ...
    'm1:UnsupportedModel','This schema only allocates existing total losses');
end
