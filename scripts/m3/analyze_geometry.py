"""Geometry-derived candidates, signed applicability limits and range screening.
No M2 network rerun or ANSYS/Fluent solution is performed.
"""
import itertools,json,math
import numpy as np
from cad_model import ROOT,config
from run_geometry import OUT,csvout,writejson

def shield_mask(y,z,p):
    s=p['shield_design'];rad=np.hypot(y,z);a=np.degrees(np.arctan2(z,y))%360
    solid=(rad>=s['inner_radius_mm'])&(rad<=s['outer_radius_mm'])
    solid&=np.abs(a-180)>s['caliper_cutout_deg']/2
    vi=s['vent_inner_radius_mm'];vo=s['vent_outer_radius_mm']
    w=(360-s['caliper_cutout_deg'])*s['opening_fraction']*(s['outer_radius_mm']**2-s['inner_radius_mm']**2)/(vo**2-vi**2)/4
    for angle in s['vent_angles_deg']:solid&=~((np.abs((a-angle+180)%360-180)<=w/2)&(rad>=vi)&(rad<=vo))
    for angle in [30,90,330]:
        yy,zz=145*np.cos(np.radians(angle)),145*np.sin(np.radians(angle));solid&=np.hypot(y-yy,z-zz)>2.2
    return solid

def interval(o,d,lo,hi):
    lo=np.asarray(lo);hi=np.asarray(hi)
    safe=np.where(np.abs(d)>1e-14,d,1e-14)
    t1=(lo-o)/safe;t2=(hi-o)/safe
    en=np.maximum(0,np.max(np.minimum(t1,t2),axis=1));ex=np.min(np.maximum(t1,t2),axis=1)
    return en,ex

def box_entry(o,d,lo,hi):
    en,ex=interval(o,d,lo,hi);return np.where(ex>en+1e-8,en,np.inf)

def ring_entry(o,d,ro,ri,x0,x1):
    aa=np.sum(d[:,1:]**2,axis=1);bb=2*np.sum(o[:,1:]*d[:,1:],axis=1)
    def disk_interval(radius):
        cc=np.sum(o[:,1:]**2,axis=1)-radius**2;delta=bb**2-4*aa*cc
        rt=np.sqrt(np.maximum(delta,0));a=(-bb-rt)/(2*aa);b=(-bb+rt)/(2*aa)
        tx1=(x0-o[:,0])/d[:,0];tx2=(x1-o[:,0])/d[:,0]
        en=np.maximum.reduce([a,np.minimum(tx1,tx2),np.zeros(len(o))]);ex=np.minimum(b,np.maximum(tx1,tx2))
        return en,ex,delta>=0
    en,ex,valid=disk_interval(ro)
    if ri:
        ei,xi,vi=disk_interval(ri)
        # If entry lies in hollow bore, the first solid can start at bore exit.
        en=np.where(vi&(ei<=en+1e-8)&(xi>en),xi,en)
    return np.where(valid&(ex>en+1e-8),en,np.inf)

def rays(p,n):
    rng=np.random.default_rng(p['screening']['radiation_seed']);q=rng.random((n,4))
    # Only exposed gear-facing annulus: hat covers radius85..88 at x=205.
    r=np.sqrt(88**2+q[:,0]*(140**2-88**2));a=2*np.pi*q[:,1]
    o=np.column_stack([np.full(n,p['brake_design']['near_face_x_mm']),r*np.cos(a),r*np.sin(a)])
    u=q[:,2];phi=2*np.pi*q[:,3];d=np.column_stack([-np.sqrt(1-u),np.sqrt(u)*np.cos(phi),np.sqrt(u)*np.sin(phi)])
    return o,d

def view(p,case,n):
    o,d=rays(p,n);tc=(160-o[:,0])/d[:,0];target=o+d*tc[:,None];y,z=target[:,1],target[:,2]
    r=p['reducer'];hit=((y>=-110)&(y<=285)&(z>=-110)&(z<=265))|((y>=-175)&(y<=-105)&(np.abs(z)<=45))
    a1=r['module_stage1_mm']*(r['teeth_pinion']+r['teeth_gear'])/2
    a2=r['module_stage2_mm']*(r['teeth_pinion']+r['teeth_gear'])/2
    centers=[(a2,a1,'input'),(a2,0,'intermediate'),(0,0,'output')]
    for yy,zz,key in centers:hit&=np.hypot(y-yy,z-zz)>r[key+'_bearing']['od_mm']/2
    for zz in [-30,30]:hit&=np.hypot(y+160,z-zz)>5.5
    first=np.where(hit,tc,np.inf);label=np.where(hit,1,0)
    def add(t,kind):
        nonlocal first,label
        take=t<first;label=np.where(take,kind,label);first=np.minimum(first,t)
    xd=p['brake_design']['near_face_x_mm']
    # Caliper C envelope = outer box minus inner window, plus bracket boxes.
    en,ex=interval(o,d,[xd-18,-178,-45],[xd+40,-90,45]);ei,xi=interval(o,d,[xd-9,-145,-46],[xd+31,-85,46])
    en=np.where((ei<=en+1e-8)&(xi>en),xi,en);add(np.where(ex>en+1e-8,en,np.inf),4)
    for lo,hi in [([160,-175,-45],[xd-18,-145,45]),([160,-145,-45],[170,-105,45])]:add(box_entry(o,d,lo,hi),4)
    for ro,ri,x0,x1 in [(88,79,xd-15,xd),(88,34,xd-20,xd-15),(65,22.5,xd-25,xd-20),(34,22.5,xd-25,xd),(22.5,0,0,260)]:add(ring_entry(o,d,ro,ri,x0,x1),4)
    s=p['shield_design'];layers=[]
    if case!='Case0':
        xx=xd-s['disc_gap_mm']-s['thickness_mm'];layers=[xx]
        if case=='CaseB':layers=[xx-s['double_air_gap_mm']-s['thickness_mm'],xx]
        for k,x in enumerate(layers):
            tt=np.full(n,np.inf)
            for xp in [x,x+s['thickness_mm']/2,x+s['thickness_mm']]:
                t=(xp-o[:,0])/d[:,0];pt=o+d*t[:,None];solid=shield_mask(pt[:,1],pt[:,2],p)
                tt=np.minimum(tt,np.where(solid,t,np.inf))
            add(tt,2+k)
        if case=='CaseC':
            # Slanted rectangular duct, exactly the same four plane equations
            # as the CAD loft; open inlet/outlet, no assumed fan or mass flow.
            oo=o.copy();dd=d.copy();slope=np.tan(np.radians(s['outlet_angle_deg']))
            oo[:,0]-=slope*(oo[:,2]-145);dd[:,0]-=slope*dd[:,2]
            cx=xd+11;wx=s['duct_width_x_mm'];wy=s['duct_width_y_mm'];wall=s['thickness_mm'];zt=145+s['duct_height_mm']
            en,ex=interval(oo,dd,[cx-wx/2,-wy/2,145],[cx+wx/2,wy/2,zt]);ei,xi=interval(oo,dd,[cx-wx/2+wall,-wy/2+wall,145],[cx+wx/2-wall,wy/2-wall,zt])
            en=np.where((ei<=en+1e-8)&(xi>en),xi,en);add(np.where(ex>en+1e-8,en,np.inf),2)
    fractions={name:float(np.mean(label==k)) for k,name in enumerate(['escape','case_direct','shield_1','shield_2','other_fixed'])}
    return dict(case=case,samples=n,**fractions,sampling_standard_error=math.sqrt(fractions['case_direct']*(1-fractions['case_direct'])/n),
                emitter_exposed_area_m2=math.pi*(140**2-88**2)*1e-6,direct_AF_m2=math.pi*(140**2-88**2)*1e-6*fractions['case_direct'])

def main():
    p=config();OUT.mkdir(exist_ok=True,parents=True)
    # Mechanical statics: separate propulsion and braking load cases.
    b=p['brake_design'];s=p['screening'];r=p['reducer'];mat=p['materials'];xx=np.linspace(95,132,301);zz=np.linspace(-24,24,301)
    reff=float(np.mean(np.hypot(xx[:,None],zz[None,:])))/1000
    torque=s['brake_torque_Nm'];force=torque/reff;Tdrive=s['software_motor_torque_Nm']*9*s['transmission_efficiency_drive']
    # Simply supported output shaft. Loads at gear centroid or overhung disc.
    xa=r['output_bearing']['width_mm']/2/1000;xb=(160-r['output_bearing']['width_mm']/2)/1000;span=xb-xa
    xg=(r['stage2_start_x_mm']+r['face_stage2_mm']/2)/1000;xd=(b['near_face_x_mm']+11)/1000
    Ft=2*Tdrive/(r['module_stage2_mm']*r['teeth_gear']/1000);Fr=Ft*math.tan(math.radians(20));gearF=math.hypot(Ft,Fr)
    Mdrive=gearF*(xg-xa)*(xb-xg)/span;Mbrake=force*(xd-xb)
    stress=[]
    for d in p['ranges']['shaft_diameter_mm']:
        for name,T,M,F,xload in [('propulsion',Tdrive,Mdrive,gearF,xg),('braking',torque,Mbrake,force,xd)]:
            dm=d/1000;sig=32*M/(math.pi*dm**3);tau=16*T/(math.pi*dm**3);vm=s['shaft_notch_factor']*math.sqrt(sig**2+3*tau**2)/1e6
            RB=F*(xload-xa)/span;RA=F-RB
            stress.append(dict(load_case=name,diameter_mm=d,torque_Nm=T,bending_Nm=M,reaction_A_N=RA,reaction_B_N=RB,von_Mises_screen_MPa=vm,assumed_limit_MPa=s['shaft_screen_limit_MPa'],status='PASS_SCREEN_ONLY' if vm<s['shaft_screen_limit_MPa'] else 'REJECT_SCREEN'))
    csvout(OUT/'shaft_screening.csv',stress)
    # Bolt group centroid at y=-160, pad tangential force at effective radius.
    eccentric=(.160-reff);moment_group=force*eccentric;couple=moment_group/.060;bolt_force=math.hypot(force/2,couple)
    mechanics=dict(brake_effective_radius_m=reff,uniform_annulus_effective_radius_m=2/3*(.140**3-.085**3)/(.140**2-.085**2),
        rear_disc_torque_Nm=torque,pad_tangential_force_N=force,pad_normal_force_each_N=torque/(2*s['friction_mu']*reff),
        mount_group_eccentric_m=eccentric,mount_group_moment_Nm=moment_group,mount_bolt_shear_each_N=bolt_force,
        M10_thread_root_area_mm2_assumed=58,mount_thread_shear_MPa=bolt_force/58,assumed_bolt_shear_limit_MPa=120,
        design_motor_torque_Nm=s['software_motor_torque_Nm'],output_traction_torque_Nm=Tdrive,
        limitations='Static elementary screen only. No joint slip, preload, bolt bending, gear tooth fatigue, bearing life, fits, seals, shaft spline, steering/suspension or vehicle mounts verified.')
    writejson(OUT/'mechanical_screening.json',mechanics)
    # Explicitly reject incompatible parameter combinations, not a claim all
    # endpoints are manufacturable. These are analytic bounds, not CAD DOEs.
    ranges=[];exp=mat['cast_iron']['alpha_per_K']*b['rotor_hot_delta_K'];dr=140*exp;dx=11*exp
    for gap,g,t,air,op,angle in itertools.product(*[p['ranges'][k] for k in ['disc_case_gap_mm','shield_gap_mm','shield_thickness_mm','double_air_gap_mm','opening_fraction','outlet_angle_deg']]):
        for case in ['CaseA','CaseB','CaseC']:
            rear=gap-g-t-(air+t if case=='CaseB' else 0)
            shield_hot=g-dx-b['assembly_tolerance_mm']-b['axial_runout_budget_mm']
            bracket_margin=gap-28 # radial web endsx170; caliper starts160+gap-18
            valid=rear>=3 and shield_hot>=2 and bracket_margin>=1
            ranges.append(dict(case=case,disc_case_gap_mm=gap,shield_gap_mm=g,thickness_mm=t,air_gap_mm=air,opening_fraction=op,outlet_angle_deg=angle,
                               shield_case_clearance_mm=rear,shield_hot_clearance_mm=shield_hot,bracket_margin_mm=bracket_margin,status='CANDIDATE' if valid else 'REJECT_GEOMETRY'))
    csvout(OUT/'geometry_range_checks.csv',ranges)
    writejson(OUT/'clearance_checks.json',dict(disc_radial_expansion_mm=dr,disc_half_axial_expansion_mm=dx,expansion_temperature_rise_K=b['rotor_hot_delta_K'],
        nominal_disc_case_gap_mm=b['near_face_x_mm']-160,nominal_disc_caliper_radial_hot_clearance_mm=5-dr-b['assembly_tolerance_mm'],
        nominal_pad_hot_running_clearance_mm=b['pad_running_gap_mm']-dx-b['axial_runout_budget_mm']-b['pad_axial_tolerance_mm'],
        rejected_pad_clearance_with_1mm_runout_mm=b['pad_running_gap_mm']-dx-1-b['pad_axial_tolerance_mm'],range_cases=len(ranges),rejected=sum(x['status'].startswith('REJECT') for x in ranges),
        scope='Thermal expansion and tolerance budget only. Disc coning, pad wear, hot runout, mount deflection and fluid boiling unverified. 400K is stress assumption, not M2 predicted disc rise.'))
    # Solid bulk terms are lower bounds; unknown interfaces remain null.
    thermal=[]
    def add(name,L,A,k,m2,scope):thermal.append(dict(path=name,length_m=L,area_m2=A,k_W_mK=k,R_bulk_K_W=L/(k*A),M2_equivalent_K_W=m2,R_contact_K_W=None,scope=scope,classification='S3_GEOMETRY_CANDIDATE'))
    add('hub_to_output_bearing_axial',(.185-xb),math.pi*(.045**2)/4,45,2+1.5,'M2 series includes disc/hub/contact; this is shaft bulk only, not a replacement')
    # radial annular equivalent expressed as equivalent L/A, preserving exact log formula
    add('hat_radial_plate',.088-.034,2*math.pi*.005*(.088-.034)/math.log(88/34),45,2,'A is logarithmic equivalent area; R=ln(ro/ri)/(2pi*k*t), contact unknown')
    add('bearing_radial_continuum',.0425-.0225,2*math.pi*.019*(.0425-.0225)/math.log(85/45),45,1.5+.5,'Log annular lower bound; rolling-element/contacts not continuum; equivalent area, contact unknown')
    add('bracket_axial_bridge',(.205-.018)-.160,.03*.09,45,8,'Steel bulk only; bolts, mounting contacts and caliper interface unknown')
    add('motor_flange_bulk',.014,math.pi*(.151**2-.0152**2),170,.3,'Full-face area upper bound; actual clamped contact area unknown')
    csvout(OUT/'thermal_resistance_candidates.csv',thermal)
    views=[view(p,c,s['radiation_samples']) for c in ['Case0','CaseA','CaseB','CaseC']];fine=[view(p,c,4*s['radiation_samples']) for c in ['Case0','CaseA','CaseB','CaseC']]
    for a,bv in zip(views,fine):a['fine_case_direct']=bv['case_direct'];a['refinement_difference']=abs(a['case_direct']-bv['case_direct']);assert a['refinement_difference']<.01
    assert fine[1]['case_direct']<=fine[0]['case_direct'] and fine[2]['case_direct']<=fine[1]['case_direct'] and fine[3]['case_direct']<=fine[1]['case_direct']
    for a in views:assert abs(sum(a[k] for k in ['escape','case_direct','shield_1','shield_2','other_fixed'])-1)<1e-12
    csvout(OUT/'radiation_geometry.csv',views)
    # Independent textbook oracle: equal coaxial disks, cosine-weighted rays.
    rng=np.random.default_rng(15);q=rng.random((131072,4));rr=100*np.sqrt(q[:,0]);aa=2*np.pi*q[:,1];tt=50/np.sqrt(1-q[:,2]);yy=rr*np.cos(aa)+tt*np.sqrt(q[:,2])*np.cos(2*np.pi*q[:,3]);zz=rr*np.sin(aa)+tt*np.sqrt(q[:,2])*np.sin(2*np.pi*q[:,3]);observed=np.mean(yy**2+zz**2<=100**2);S=2+(.5)**2;exact=(S-math.sqrt(S*S-4))/2
    assert abs(observed-exact)<.005
    writejson(OUT/'analysis_checks.json',dict(status='PASS',geometry_range_cases=len(ranges),nominal_shaft_screen=all(x['status']=='PASS_SCREEN_ONLY' for x in stress if x['diameter_mm']==45),
        view_factor_disk_oracle=exact,view_factor_disk_sampling=float(observed),view_factor_error=abs(observed-exact),radiation_units='dimensionless F and m2 AF',
        M2_comparison_AF_m2=.04*.12,occlusion_model='Analytic intersection of source-facing case plane, stepped hub/shaft/caliper, finite shield planes/windows and slanted duct walls; three-plane finite-thickness approximation. No diffuse multibounce radiosity or CFD.',
        radiative_temperature_prediction='NOT EXECUTED; geometric direct-view reduction is not total heat reduction; shields absorb/re-emit and supports conduct.'))
    print('Analysis PASS; range rejects',sum(x['status'].startswith('REJECT') for x in ranges),'of',len(ranges),'F',[round(x['case_direct'],4) for x in views],flush=True)

if __name__=='__main__':main()
