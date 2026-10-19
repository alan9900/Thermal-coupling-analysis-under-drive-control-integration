function q=m1_gear(c, wheel_power_W)
% Positive power: motor drives wheels. Negative: wheels backdrive motor.
g=c.base.drive.rear_gearbox_per_side;
assert(c.stage.assumptions.allow_constant_gear_efficiency,'m1:GearEvidenceGap','Directional validated loss maps absent');
assert(g.peak_drive_efficiency_screening>0 && g.peak_drive_efficiency_screening<=1);
assert(g.peak_backdrive_efficiency_screening>0 && g.peak_backdrive_efficiency_screening<=1);
shaft=wheel_power_W;
drive=wheel_power_W>=0;
shaft(drive)=wheel_power_W(drive)/g.peak_drive_efficiency_screening;
shaft(~drive)=wheel_power_W(~drive)*g.peak_backdrive_efficiency_screening;
heat=shaft-wheel_power_W;
assert(all(heat>=-1e-9));
q=struct('motor_shaft_power_W',shaft,'heat_W',max(0,heat),'evidence','ASSUMED_constant_directional_efficiencies');
end
