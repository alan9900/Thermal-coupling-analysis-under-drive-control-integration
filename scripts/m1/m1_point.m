function q=m1_point(c, speed_m_s, accel_m_s2, o)
% One prescribed longitudinal state, two independent rear power ports.
% Negative acceleration = braking. No yaw dynamics or temperature integration.
v=speed_m_s; a=accel_m_s2; b=c.base; s=c.stage.assumptions;
m=b.vehicle.mass_kg; g=b.vehicle.gravity_m_s2; r=b.vehicle.wheel_effective_rolling_radius_m;
i=b.drive.rear_gearbox_per_side.reduction_motor_to_wheel;
assert(isscalar(v) && isfinite(v) && v>=0 && isfinite(a),'m1:State','Forward motion only');
assert(all(o.wheel_speed_ratio>=0) && abs(mean(o.wheel_speed_ratio)-1)<1e-10,'m1:WheelSpeeds','Side speeds must average prescribed center speed');
assert(all(o.rear_force_share>=0) && abs(sum(o.rear_force_share)-1)<1e-10,'m1:ForceShares','Rear shares sum to one');
assert(o.battery_charge_cap_total_kW>=0 && o.battery_discharge_cap_total_kW>=0);
assert(o.battery_soc>=0 && o.battery_soc<=1 && o.temperature_charge_factor>=0 && o.temperature_charge_factor<=1);
assert(all(o.rear_mu>=0) && o.front_mu>=0);
wheel_v=v*o.wheel_speed_ratio; wheel_omega=wheel_v/r;
rpm=wheel_omega*i*60/(2*pi);
assert(all(rpm<=max(c.map.speed_rpm)),'m1:MapBounds','No EPA speed extrapolation');
Ntotal=m*g*cos(o.grade_rad);
Nrear=m*g*(b.vehicle.static_rear_axle_fraction*cos(o.grade_rad)+b.vehicle.cg_height_m/b.vehicle.wheelbase_m*sin(o.grade_rad)) ...
    +m*a*b.vehicle.cg_height_m/b.vehicle.wheelbase_m;
Nfront=Ntotal-Nrear;
assert(Nrear>0 && Nfront>0,'m1:AxleLift','Outside quasi-static axle-load model');
rearN=[Nrear/2 Nrear/2]; rearCap=o.rear_mu.*rearN;
Froad=double(o.road_load)*(m*g*cos(o.grade_rad)*b.vehicle.rolling_resistance_coefficient ...
    +.5*s.air_density_kg_m3*b.vehicle.drag_coefficient*b.vehicle.frontal_area_m2*v^2);
Fgrade=m*g*sin(o.grade_rad);
Frequest=m*b.vehicle.rotational_inertia_factor*a+Froad+Fgrade;
Tm=[0 0]; frontFriction=0; rearFriction=[0 0]; rearRegen=[0 0];
rearActual=[0 0]; requestedBrake=[0 0]; chargeCap=0;
if Frequest<0
    % Ideal equal adhesion-utilization reference; no commercial EBD claim.
    B=-Frequest; rearFraction=Nrear/Ntotal;
    requestedBrake=B*rearFraction*o.rear_force_share;
    rearActual=min(requestedBrake,rearCap);
    frontFriction=min(B*(1-rearFraction),o.front_mu*Nfront);
    etaB=b.drive.rear_gearbox_per_side.peak_backdrive_efficiency_screening;
    bound=abs(interp1(c.map.speed_rpm,c.map.negative_torque_limit_Nm,rpm,'linear'));
    fade=max(0,min(1,(v*3.6-s.regen_disable_below_kmh)/(s.regen_full_above_kmh-s.regen_disable_below_kmh)));
    Tmax=min([bound; s.regen_torque_limit_each_Nm*ones(1,2); ...
        60000./max(wheel_omega*i,eps);rearActual*r*etaB/i],[],1);
    Tmax=Tmax*fade.*double(o.regen_available);
    chargeCap=o.battery_charge_cap_total_kW*1000*o.temperature_charge_factor*double(o.battery_soc<o.soc_charge_disable_at);
    [Tm,e]=budget_regen(c,rpm,Tmax,chargeCap);
    rearRegen=abs(Tm)*i/(r*etaB);
    rearFriction=max(0,rearActual-rearRegen);
    wheelMotorPower=-rearRegen.*wheel_v;
    actualForce=-(frontFriction+sum(rearActual));
else
    etaD=b.drive.rear_gearbox_per_side.peak_drive_efficiency_screening;
    rearDemand=Frequest*o.rear_force_share;
    bound=interp1(c.map.speed_rpm,c.map.positive_torque_limit_Nm,rpm,'linear');
    Tallowed=min([bound; b.drive.rear_motor_per_side.configured_traction_torque_limit_nm*ones(1,2); ...
        60000./max(wheel_omega*i,eps)],[],1);
    Tdesired=min(min(rearDemand,rearCap)*r/(i*etaD),Tallowed);
    Tm=Tdesired;
    e=m1_emot(c,rpm,Tm,Tm>0);
    if sum(e.dc_W)>o.battery_discharge_cap_total_kW*1000
        lo=0; hi=1;
        for k=1:c.stage.numerics.battery_bisection_iterations
            mid=(lo+hi)/2; em=m1_emot(c,rpm,Tdesired*mid,Tdesired*mid>0);
            if sum(em.dc_W)<=o.battery_discharge_cap_total_kW*1000, lo=mid; else, hi=mid; end
        end
        Tm=Tdesired*lo; e=m1_emot(c,rpm,Tm,Tm>0);
    end
    rearActual=Tm*i*etaD/r;
    wheelMotorPower=rearActual.*wheel_v;
    actualForce=sum(rearActual);
end
gear=m1_gear(c,wheelMotorPower);
assert(max(abs(gear.motor_shaft_power_W-e.mechanical_W))<1e-6,'m1:GearDirection','Motor and wheel power mismatch');
discPower=rearFriction.*wheel_v;
frontPower=frontFriction*v;
% Optional imposed L/R speeds require this signed external power port.
% It must not be silently absorbed into longitudinal kinetic energy.
if Frequest<0, signedRearForce=-rearActual; else, signedRearForce=rearActual; end
lrExchange=sum(signedRearForce.*(wheel_v-v));
unmetForce=Frequest-actualForce;
kineticRate=m*b.vehicle.rotational_inertia_factor*a*v;
roadPower=Froad*v; gradePower=Fgrade*v; unmetPower=unmetForce*v;
aux=s.electrical_auxiliary_power_W;
dcTotal=sum(e.dc_W)+aux;
rhs=kineticRate+roadPower+gradePower+frontPower+sum(discPower)+sum(gear.heat_W)+sum(e.combined_heat_W)+aux+lrExchange;
residual=dcTotal+unmetPower-rhs;
partition=s.disc_contact_heat_fraction;
assert(partition>=0 && partition<=1);
q=struct('speed_m_s',v,'accel_m_s2',a,'motor_rpm',rpm,'wheel_omega_rad_s',wheel_omega, ...
    'disc_omega_rad_s',wheel_omega,'motor_torque_Nm',Tm, ...
    'front_normal_force_N',Nfront,'rear_normal_force_N',rearN, ...
    'front_friction_force_N',frontFriction,'rear_friction_force_N',rearFriction, ...
    'rear_regen_force_N',rearRegen,'rear_total_force_N',abs(rearActual), ...
    'requested_rear_brake_force_N',requestedBrake,'disc_friction_torque_Nm',rearFriction*r, ...
    'disc_contact_power_W',discPower,'disc_deposited_heat_assumed_W',partition*discPower, ...
    'pad_deposited_heat_assumed_W',(1-partition)*discPower, ...
    'disc_heat_lower_assumed_W',min(s.disc_contact_heat_fraction_bounds)*discPower, ...
    'disc_heat_upper_assumed_W',max(s.disc_contact_heat_fraction_bounds)*discPower, ...
    'front_axle_friction_power_W',frontPower,'gear_heat_assumed_W',gear.heat_W, ...
    'emot_combined_heat_W',e.combined_heat_W,'motor_total_heat_estimated_W',e.motor_total_heat_estimated_W, ...
    'inverter_heat_estimated_W',e.inverter_heat_estimated_W,'unallocated_emot_heat_W',e.unallocated_emot_heat_W, ...
    'winding_heat_W',e.winding_heat_W,'motor_mechanical_power_W',e.mechanical_W, ...
    'dc_power_each_W',e.dc_W,'dc_power_total_W',dcTotal,'battery_charge_effective_cap_W',chargeCap, ...
    'kinetic_energy_rate_W',kineticRate,'road_power_W',roadPower,'grade_power_W',gradePower, ...
    'auxiliary_power_W',aux,'lr_kinematic_exchange_W',lrExchange,'unmet_force_N',unmetForce, ...
    'unmet_power_W',unmetPower,'power_residual_W',residual, ...
    'rear_adhesion_utilization',abs(rearActual)./rearN,'front_adhesion_utilization',frontFriction/Nfront, ...
    'regen_is_estimated',e.regen_is_estimated,'drive_split_is_estimated',e.split_is_estimated, ...
    'trace_feasible',abs(unmetForce)<1e-6);
end

function [T,e]=budget_regen(c,rpm,Tmax,cap)
if cap<=0 || all(Tmax==0)
    T=[0 0]; e=m1_emot(c,rpm,T,[false false]); return
end
[T,e]=regen_at(c,rpm,Tmax,1);
if -sum(e.dc_W)<=cap, return; end
lo=0; hi=1;
for k=1:c.stage.numerics.battery_bisection_iterations
    mid=(lo+hi)/2; [~,em]=regen_at(c,rpm,Tmax,mid);
    if -sum(em.dc_W)<=cap, lo=mid; else, hi=mid; end
end
[T,e]=regen_at(c,rpm,Tmax,lo);
assert(-sum(e.dc_W)<=cap+1e-5,'m1:BatteryCap','Total battery charge cap exceeded');
end

function [T,e]=regen_at(c,rpm,Tmax,scale)
T=-Tmax*scale;
e=m1_emot(c,rpm,T,abs(T)>1e-12);
% Only net generation is selected; the remaining braking demand is friction.
off=e.dc_W>=0 | Tmax==0 | rpm==0;
T(off)=0;
if any(off), e=m1_emot(c,rpm,T,~off); end
end
