function run_m0_review
% M0 algebraic feasibility and stop-integral audit, MATLAB R2025a.
% No transient heat-source model, thermal network, CAD or optimization.
root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
out = fullfile(root,'results','m0');
c = jsondecode(fileread(fullfile(out,'baseline_vehicle.json')));
map = jsondecode(fileread(fullfile(out,'epa_map_numeric.json')));
v = c.vehicle; d = c.drive; b = c.brakes;
m = v.mass_kg; g = v.gravity_m_s2; r = v.wheel_effective_rolling_radius_m;
i = d.rear_gearbox_per_side.reduction_motor_to_wheel;
assert(strcmp(c.metadata.version,'v0.4') && strcmp(d.driven_axle,'rear'));
assert(d.independent_motor_count==2 && ~d.differential_present);
assert(b.front_conventional_service_brakes_retained && b.rear_rotor_count==2);
assert(b.rotor_speed_to_own_wheel_speed_ratio==1);
assert(isempty(d.rear_motor_per_side.motor_loss_map_file));
assert(isempty(d.rear_motor_per_side.continuous_mechanical_power_kw));
assert(i>0 && r>0 && m>0 && v.wheelbase_m>0);
assert(all(diff(map.speed_rpm)>0));
assert(isequal(size(map.electrical_power_W),[14 39]));
assert(all(isfinite(map.electrical_power_W),'all'));
assert(max(abs(map.positive_torque_limit_Nm+map.negative_torque_limit_Nm))<1e-9);
assert(max(map.speed_rpm)<d.rear_motor_per_side.max_mechanical_speed_rpm);
checks = ["V0.4 rear independent topology";"null continuous power preserved";"null winding loss map preserved";"EPA numeric shape finite";"EPA symmetric torque bounds"];

% Explicit S3 screening additions; never silently turn into verified inputs.
s.rho_air_kg_m3 = 1.225;
s.eta_emot_regen = 0.90;
s.regen_cutoff_kmh = 5;
s.regen_torque_cap_Nm = 130; % assumed regen cap, NOT traction cap evidence
s.road_load_pitch_moment = 'ignored; approximate load transfer based on a/g';
writejson(fullfile(out,'screening_assumptions.json'),s);

% Pointwise speed/traction review: EPA torque envelope, no extrapolation.
speed_kmh = [5;50;100;160];
omega_wheel = speed_kmh/3.6/r;
motor_rpm = omega_wheel*i*60/(2*pi);
ideal_torque_Nm = min(d.rear_motor_per_side.configured_traction_torque_limit_nm, ...
    d.rear_motor_per_side.peak_mechanical_power_kw*1000./(omega_wheel*i));
epa_torque_Nm = interp1(map.speed_rpm,map.positive_torque_limit_Nm,motor_rpm,'linear',NaN);
allowed_torque_Nm = min(ideal_torque_Nm,epa_torque_Nm);
eta_d = d.rear_gearbox_per_side.peak_drive_efficiency_screening;
wheel_available_kW = 2*allowed_torque_Nm.*(omega_wheel*i)*eta_d/1000;
road_force_N = m*g*v.rolling_resistance_coefficient + .5*s.rho_air_kg_m3*v.drag_coefficient*v.frontal_area_m2.*(speed_kmh/3.6).^2;
road_power_kW = road_force_N.*(speed_kmh/3.6)/1000;
shaft_required_each_kW = road_power_kW/(2*eta_d);
S = table(speed_kmh,motor_rpm,ideal_torque_Nm,epa_torque_Nm,allowed_torque_Nm,wheel_available_kW,road_power_kW,shaft_required_each_kW);
writetable(S,fullfile(out,'speed_power_review.csv'));
assert(motor_rpm(end)<d.rear_motor_per_side.max_mechanical_speed_rpm);
assert(wheel_available_kW(end)>road_power_kW(end));
metrics = struct('wheel_rpm_at_100',100/3.6/r*60/(2*pi), ...
    'motor_rpm_at_160',motor_rpm(end),'speed_limit_only_kmh',13500*2*pi/60*r/i*3.6, ...
    'map_speed_limit_kmh',max(map.speed_rpm)*2*pi/60*r/i*3.6, ...
    'max_ratio_at_160_hardware',13500*2*pi/60*r/(160/3.6), ...
    'max_ratio_at_160_map',max(map.speed_rpm)*2*pi/60*r/(160/3.6), ...
    'hardware_ideal_base_speed_rpm',60000/207*60/(2*pi), ...
    'software_ideal_base_speed_rpm',60000/130*60/(2*pi), ...
    'traction_wheel_torque_each_Nm',130*i*eta_d, ...
    'rear_adhesion_acceleration_g',v.tire_road_mu*v.static_rear_axle_fraction/(1-v.tire_road_mu*v.cg_height_m/v.wheelbase_m), ...
    'software_force_acceleration_g',2*130*i*eta_d/(m*g*r), ...
    'initial_kinetic_energy_J',.5*m*(c.cases.nominal_stop_initial_speed_kmh/3.6)^2);
writejson(fullfile(out,'derived_metrics.json'),metrics);

% Stop-integral review, both road-free baseline and road-load screening.
rows = {}; k=0;
for road = [false true]
    for z = c.cases.stop_deceleration_g_scan(:)'
        for cap = c.cases.total_battery_regen_acceptance_kw_screening(:)'
            k=k+1; rows{k}=stopcase(c,map,s,z,cap,road,20001); %#ok<AGROW>
        end
    end
end
B=struct2table([rows{:}]); writetable(B,fullfile(out,'braking_review.csv'));
assert(all(B.energy_residual_relative<1e-9));
assert(all(B.min_friction_power_W>=-1e-8));
assert(all(B.max_battery_power_W<=B.battery_cap_kW*1000+1e-6));
assert(all(B.max_rear_adhesion_utilization<=v.tire_road_mu+1e-10));
assert(all(B.max_front_adhesion_utilization<=v.tire_road_mu+1e-10));
assert(all(B.max_generator_torque_excess_Nm<1e-8));
assert(all(B.regen_cutoff_power_W==0));
checks=[checks;"front plus two rear sides plus road energy closure";"nonnegative friction and battery cap";"front/rear adhesion";"generator torque limits and zero low-speed regen"];

% Independent analytic no-road/no-regen checks (not a restatement of quadrature).
z=.6; f=v.static_rear_axle_fraction-z*v.cg_height_m/v.wheelbase_m;
ref=B(~B.road_load & B.deceleration_g==z & B.battery_cap_kW==0,:);
assert(abs(ref.initial_disc_torque_Nm-m*z*g*f*r/2)<1e-8);
assert(abs(ref.disc_friction_energy_kJ-.5*m*(100/3.6)^2*f/2/1000)<1e-8);
assert(abs(ref.initial_disc_torque_Nm-752.839091)<.001);
assert(abs(ref.disc_friction_energy_kJ-149.5)<.1);
% Independent integral of a simple power-capped constant-force regen envelope.
a=z*g; F=2000; P=30000; v0=100/3.6; vc=P/F;
analytic=(F*vc^2/2+P*(v0-vc))/a;
numeric=integral(@(x)min(F*x,P)/a,0,v0,'Waypoints',vc);
assert(abs(analytic-numeric)<1e-7);
% Refinement only where cutoff/cap produces integration kinks.
coarse=stopcase(c,map,s,.6,30,true,10001);
fine=stopcase(c,map,s,.6,30,true,40001);
refinement=abs(coarse.disc_friction_energy_kJ-fine.disc_friction_energy_kJ)/fine.disc_friction_energy_kJ;
assert(refinement<5e-4);
checks=[checks;"0.6g analytic torque and energy regression";"independent capped-power integral";"stop-integral refinement <0.05 percent"];

% Assumption sensitivity, no design optimization.
sens={}; k=0;
for eta=[.8 .9 1]
    for cutoff=[0 5 10]
        st=s; st.eta_emot_regen=eta; st.regen_cutoff_kmh=cutoff;
        for cap=[30 60]
            k=k+1; sens{k}=stopcase(c,map,st,.6,cap,true,20001); %#ok<AGROW>
        end
    end
end
writetable(struct2table([sens{:}]),fullfile(out,'regen_assumption_sensitivity.csv'));
geom={}; k=0;
for f0=[.50 .55 .60]
    for h=[.45 .55 .65]
        for rr=[.32 .33 .34]
            k=k+1;
            ff=f0-.6*h/v.wheelbase_m;
            geom{k}=struct('static_rear_fraction',f0,'cg_height_m',h,'rolling_radius_m',rr, ...
                'rear_dynamic_fraction',ff,'disc_torque_06g_Nm',m*.6*g*ff*rr/2, ...
                'disc_energy_06g_kJ',.5*m*(100/3.6)^2*ff/2/1000, ...
                'motor_rpm_160',160/3.6/rr*i*60/(2*pi)); %#ok<AGROW>
        end
    end
end
writetable(struct2table([geom{:}]),fullfile(out,'geometry_assumption_sensitivity.csv'));
radius_m=[.32;.33;.34]; rpm_at_160=160/3.6./radius_m*i*60/(2*pi);
writetable(table(radius_m,rpm_at_160),fullfile(out,'radius_speed_sensitivity.csv'));

% Plots explicitly labelled with evidence boundaries.
fig=figure('Visible','off','Color','w','Position',[100 100 1000 450]);
tiledlayout(1,2);
nexttile; plot(map.speed_rpm,map.positive_torque_limit_Nm,'LineWidth',1.8); hold on;
nn=linspace(1,13000,500); plot(nn,min(130,60000./(nn*2*pi/60)),'--','LineWidth',1.4);
xline(motor_rpm(end),':','160 km/h','LabelVerticalAlignment','bottom'); xlabel('Motor speed (rpm)'); ylabel('Torque (N m)');
legend('EPA 650 V envelope','ASSUMED ideal 130 N m / 60 kW','Location','northeast'); grid on;
nexttile; R=B(~B.road_load,:); E=reshape(R.disc_friction_energy_kJ,3,3)';
bar([.3 .6 .8],E); xlabel('Deceleration (g)'); ylabel('One rear disc friction work (kJ)');
legend('Battery cap 0 kW','30 kW','60 kW'); title('ASSUMED regen screening; no road load'); grid on;
exportgraphics(fig,fullfile(out,'m0_review.png'),'Resolution',180);
exportgraphics(fig,fullfile(out,'m0_review.svg'),'ContentType','vector'); close(fig);

validation=struct('status','PASS','matlab',version,'release',version('-release'), ...
    'checks',checks,'max_energy_residual_relative',max(B.energy_residual_relative), ...
    'integral_refinement_relative',refinement,'thermal_models','NOT EXECUTED; outside M0', ...
    'ANSYS','NOT EXECUTED; outside M0','optimization','NOT EXECUTED; outside M0');
writejson(fullfile(out,'validation.json'),validation);
save(fullfile(out,'m0_results.mat'),'c','map','s','S','B','metrics','validation');
disp(S); disp(B(:,{'road_load','deceleration_g','battery_cap_kW','initial_disc_torque_Nm','initial_disc_power_kW','disc_friction_energy_kJ'}));
disp(validation);
end

function q=stopcase(c,map,s,z,cap,road,N)
v=c.vehicle; d=c.drive; m=v.mass_kg; g=v.gravity_m_s2;
r=v.wheel_effective_rolling_radius_m; a=z*g; v0=c.cases.nominal_stop_initial_speed_kmh/3.6;
x=linspace(0,v0,N); % integrate in speed: dt = dv/a
f=v.static_rear_axle_fraction-z*v.cg_height_m/v.wheelbase_m;
Froad=double(road)*(m*g*v.rolling_resistance_coefficient+.5*s.rho_air_kg_m3*v.drag_coefficient*v.frontal_area_m2*x.^2);
Fbrake=m*a-Froad; assert(min(Fbrake)>0);
Frear=f*Fbrake; Ffront=(1-f)*Fbrake;
ratio=d.rear_gearbox_per_side.reduction_motor_to_wheel;
eta_g=d.rear_gearbox_per_side.peak_backdrive_efficiency_screening;
rpm=x/r*ratio*60/(2*pi);
Tmap=interp1(map.speed_rpm,abs(map.negative_torque_limit_Nm),rpm,'linear',NaN);
assert(all(isfinite(Tmap)),'M0 does not extrapolate EPA maps');
Tallowed=min(Tmap,s.regen_torque_cap_Nm);
% Backdrive: P_motor_in=eta_g*P_wheel_regen, hence F_wheel=T_motor*i/(r*eta_g).
Ftorque=2*Tallowed*ratio/(r*eta_g);
Fpower=2*d.rear_motor_per_side.peak_mechanical_power_kw*1000./max(x,eps)/eta_g;
Fbatt=cap*1000./(max(x,eps)*eta_g*s.eta_emot_regen);
Fadh=v.tire_road_mu*m*g*f;
Fregen=min([Frear;Ftorque;Fpower;Fbatt;Fadh*ones(size(x))],[],1);
Fregen(x<s.regen_cutoff_kmh/3.6 | x==0)=0;
Fdisc=(Frear-Fregen)/2;
Pdisc=Fdisc.*x; Preg=Fregen.*x;
Pbatt=Preg*eta_g*s.eta_emot_regen;
Pgear=Preg*(1-eta_g); Pemot=Preg*eta_g*(1-s.eta_emot_regen);
integ=@(p)trapz(x,p)/a;
Efront=integ(Ffront.*x); Edisc=integ(Pdisc); Eroad=integ(Froad.*x);
Ebatt=integ(Pbatt); Egear=integ(Pgear); Eemot=integ(Pemot);
E0=.5*m*v0^2;
q=struct('road_load',road,'deceleration_g',z,'battery_cap_kW',cap, ...
    'eta_emot_regen_ASSUMED',s.eta_emot_regen,'regen_cutoff_kmh_ASSUMED',s.regen_cutoff_kmh, ...
    'rear_dynamic_fraction',f,'stopping_time_s',v0/a,'stopping_distance_m',v0^2/(2*a), ...
    'initial_disc_torque_Nm',Fdisc(end)*r,'peak_disc_torque_Nm',max(Fdisc)*r, ...
    'initial_disc_power_kW',Pdisc(end)/1000,'peak_disc_power_kW',max(Pdisc)/1000, ...
    'disc_friction_energy_kJ',Edisc/1000,'front_axle_friction_energy_kJ',Efront/1000, ...
    'battery_recovered_energy_kJ',Ebatt/1000,'gear_backdrive_loss_energy_kJ',Egear/1000, ...
    'emot_combined_loss_energy_kJ',Eemot/1000,'road_energy_kJ',Eroad/1000, ...
    'energy_residual_relative',abs(E0-Efront-2*Edisc-Ebatt-Egear-Eemot-Eroad)/E0, ...
    'min_friction_power_W',min(Pdisc),'max_battery_power_W',max(Pbatt), ...
    'max_rear_adhesion_utilization',max(Frear)/(m*g*f), ...
    'max_front_adhesion_utilization',max(Ffront)/(m*g*(1-f)), ...
    'max_generator_torque_excess_Nm',max(Fregen*r*eta_g/(2*ratio)-Tallowed), ...
    'regen_cutoff_power_W',max([0 Preg(x<s.regen_cutoff_kmh/3.6)]));
end

function writejson(path,data)
fid=fopen(path,'w','n','UTF-8'); assert(fid>=0); cl=onCleanup(@()fclose(fid));
fprintf(fid,'%s\n',jsonencode(data,'PrettyPrint',true));
end
