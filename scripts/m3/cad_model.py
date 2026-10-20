"""Millimetre B-rep geometry. YAML + this Python file are the editable CAD source.
No OEM reconstruction, structural/thermal solver, CFD or cooling claim is implied.
"""
import math
from pathlib import Path
import cadquery as cq
import yaml

ROOT=Path(__file__).resolve().parents[2]

def config():
    p=yaml.safe_load((ROOT/'configs/m3_geometry.yaml').read_text(encoding='utf-8'))
    assert p['metadata']['length_unit']=='mm'
    assert all(v is None for v in p['unknown_actual'].values())
    return p

def box(x0,x1,y0,y1,z0,z1):
    assert x1>x0 and y1>y0 and z1>z0
    return cq.Solid.makeBox(x1-x0,y1-y0,z1-z0,cq.Vector(x0,y0,z0))

def cyl(r,x0,x1,y=0,z=0):
    return cq.Solid.makeCylinder(r,x1-x0,cq.Vector(x0,y,z),cq.Vector(1,0,0))

def ring(ro,ri,x0,x1,y=0,z=0):
    return cyl(ro,x0,x1,y,z).cut(cyl(ri,x0-.01,x1+.01,y,z))

def fused(shapes):
    return shapes[0].fuse(*shapes[1:]).clean() if len(shapes)>1 else shapes[0]

def sector(ri,ro,a0,a1,x0,x1):
    # Polygon edges approximate circular arcs to <=0.04mm at radius150.
    n=max(2,math.ceil((a1-a0)/2))
    outer=[(ro*math.cos(math.radians(a0+(a1-a0)*k/n)),ro*math.sin(math.radians(a0+(a1-a0)*k/n))) for k in range(n+1)]
    inner=[(ri*math.cos(math.radians(a0+(a1-a0)*k/n)),ri*math.sin(math.radians(a0+(a1-a0)*k/n))) for k in range(n,-1,-1)]
    return cq.Workplane('YZ',origin=(x0,0,0)).polyline(outer+inner).close().extrude(x1-x0).val()

def shield(p,x0):
    s=p['shield_design'];ro=s['outer_radius_mm'];ri=s['inner_radius_mm'];t=s['thickness_mm']
    result=ring(ro,ri,x0,x0+t)
    half=s['caliper_cutout_deg']/2
    cuts=[sector(ri-.1,ro+.1,180-half,180+half,x0-.1,x0+t+.1)]
    # Four windows, all outside the caliper cutout. Opening ratio is relative
    # to remaining 280deg; cutout and vent openings are reported separately.
    width=(360-s['caliper_cutout_deg'])*s['opening_fraction']/4
    for a in [10,70,290,350]:cuts.append(sector(ri-.1,ro+.1,a-width/2,a+width/2,x0-.1,x0+t+.1))
    for a in [30,90,330]:
        y,z=145*math.cos(math.radians(a)),145*math.sin(math.radians(a))
        cuts.append(cyl(2.2,x0-.1,x0+t+.1,y,z))
    return result.cut(cq.Compound.makeCompound(cuts)).clean()

def gear(m,z,bore,width,x,yc,zc,phase,backlash):
    """Standard 20deg full-depth involute; six samples/flank, no root fillet.
    Positive backlash. Not a manufacturing or tooth stress model.
    """
    rp=m*z/2;rb=rp*math.cos(math.radians(20));ra=rp+m;rf=rp-1.25*m
    inv=lambda a:math.tan(a)-a
    def beta(r):return math.pi/(2*z)+inv(math.radians(20))-inv(math.acos(min(1,rb/r)))-backlash/(2*rp)
    pts=[]
    for k in range(z):
        a=math.radians(phase)+2*math.pi*k/z
        def point(r,ang):return (r*math.cos(ang),r*math.sin(ang))
        r0=max(rf,rb);b0=beta(r0)
        pts.append(point(rf,a-b0))
        for j in range(7):
            r=r0+(ra-r0)*j/6;pts.append(point(r,a-beta(r)))
        for j in range(6,-1,-1):
            r=r0+(ra-r0)*j/6;pts.append(point(r,a+beta(r)))
        pts.append(point(rf,a+b0))
        end=a+2*math.pi/z-b0
        for j in [1,2]:pts.append(point(rf,a+b0+(end-a-b0)*j/3))
    clean=[]
    for pt in pts:
        if not clean or math.dist(clean[-1],pt)>1e-8:clean.append(pt)
    return cq.Workplane('YZ',origin=(x,yc,zc)).polyline(clean).close().extrude(width).val().cut(cyl(bore/2,x-.1,x+width+.1,yc,zc))

def build(p,case='Case0'):
    assert case in ['Case0','CaseA','CaseB','CaseC']
    r=p['reducer'];b=p['brake_design'];s=p['shield_design'];mr=p['motor_reference'];md=p['motor_design'];br=p['brake_reference']
    a1=r['module_stage1_mm']*(r['teeth_pinion']+r['teeth_gear'])/2
    a2=r['module_stage2_mm']*(r['teeth_pinion']+r['teeth_gear'])/2
    axes={'input':(a2,a1),'intermediate':(a2,0),'output':(0,0)}
    parts={};materials={};roles={}
    def add(name,shape,material,role='solid'):
        assert shape.isValid() and shape.Volume()>0,name
        parts[name]=shape;materials[name]=material;roles[name]=role
    y,z=axes['input'];L=mr['casing_length_mm'];R=mr['casing_diameter_mm']/2;end=md['endcap_mm']
    shell=ring(R,mr['stator_od_mm']/2,-L+end,-end,y,z)
    jacket=ring(md['jacket_outer_radius_mm'],md['jacket_inner_radius_mm'],md['jacket_start_x_mm'],md['jacket_end_x_mm'],y,z)
    caps=[ring(R,md['stub_diameter_mm']/2+.2,-L,-L+end,y,z),ring(R,md['stub_diameter_mm']/2+.2,-end,0,y,z)]
    add('motor_case',fused([shell.cut(jacket)]+caps),'aluminium')
    add('motor_water_jacket',jacket,'water_equivalent','fluid')
    x=md['core_start_x_mm'];xe=x+mr['stator_stack_mm']
    core=ring(mr['stator_od_mm']/2,mr['stator_id_mm']/2,x,xe,y,z)
    slots=[];wires=[]
    for k in range(md['slot_count']):
        lo=md['slot_radial_start_mm'];hi=lo+md['slot_depth_mm'];w=md['slot_width_mm'];wc=md['copper_width_mm']
        slots.append(box(x-.01,xe+.01,lo,hi,-w/2,w/2).rotate((0,0,0),(1,0,0),360*k/md['slot_count']).translate((0,y,z)))
        wires.append(box(x,xe,lo+.2,hi-.2,-wc/2,wc/2).rotate((0,0,0),(1,0,0),360*k/md['slot_count']).translate((0,y,z)))
    add('motor_stator',core.cut(cq.Compound.makeCompound(slots)),'steel')
    ew=md['end_winding_length_mm'];wires.extend([ring(120,90,x-ew,x,y,z),ring(120,90,xe,xe+ew,y,z)])
    add('motor_winding',cq.Compound.makeCompound(wires),'copper')
    add('motor_rotor_other',ring(mr['rotor_od_mm']/2,mr['rotor_lamination_id_mm']/2,x,x+mr['rotor_stack_mm'],y,z),'steel')
    add('input_rotor_shaft',fused([cyl(md['stub_diameter_mm']/2,-L+1,160,y,z),cyl(mr['rotor_lamination_id_mm']/2,x-3,xe+3,y,z)]),'steel')
    add('intermediate_shaft',cyl(r['intermediate_shaft_diameter_mm']/2,0,160,*axes['intermediate']),'steel')
    add('output_shaft',cyl(r['output_shaft_diameter_mm']/2,-5,260),'steel')
    gears=[('stage1_pinion',r['module_stage1_mm'],20,r['face_stage1_mm'],r['stage1_start_x_mm'],'input',-90,md['stub_diameter_mm']),
           ('stage1_gear',r['module_stage1_mm'],60,r['face_stage1_mm'],r['stage1_start_x_mm'],'intermediate',87,r['intermediate_shaft_diameter_mm']),
           ('stage2_pinion',r['module_stage2_mm'],20,r['face_stage2_mm'],r['stage2_start_x_mm'],'intermediate',180,r['intermediate_shaft_diameter_mm']),
           ('stage2_gear',r['module_stage2_mm'],60,r['face_stage2_mm'],r['stage2_start_x_mm'],'output',-3,r['output_shaft_diameter_mm'])]
    for name,m,n,w,xg,ax,phase,bore in gears:add(name,gear(m,n,bore,w,xg,*axes[ax],phase,r['backlash_mm']),'steel')
    cuts=[]
    for ax in axes:
        bearing=r[ax+'_bearing'];yy,zz=axes[ax];bw=bearing['width_mm'];od=bearing['od_mm']/2;ir=bearing['bore_mm']/2
        # Bearing envelopes have geometric mass; catalogue rolling-element
        # mass/life is kept independent. Front/back end supports, axial span.
        for j,xb in enumerate([0,160-bw]):
            add(ax+f'_bearing_{j+1}',ring(od,ir,xb,xb+bw,yy,zz),'steel')
        cuts.extend([cyl(od,-.1,bw,yy,zz),cyl(od,160-bw,160.1,yy,zz)])
    yl,yh=r['case_y_limits_mm'];zl,zh=r['case_z_limits_mm'];t=r['case_wall_mm']
    outer=box(0,160,yl,yh,zl,zh);inner=box(t,160-t,yl+t,yh-t,zl+t,zh-t)
    housing=outer.cut(inner)
    # Local bosses bridge inner bearing envelopes to sidewalls/endplates.
    bosses=[]
    for ax,(yy,zz) in axes.items():
        be=r[ax+'_bearing'];od=be['od_mm']/2;bw=be['width_mm']
        bosses.extend([ring(od+7,od,0,bw+3,yy,zz),ring(od+7,od,160-bw-3,160,yy,zz)])
    housing=fused([housing]+bosses+[box(148,160,-175,-105,-45,45)])
    housing=housing.cut(cq.Compound.makeCompound(cuts))
    holes=[cyl(5.5,147,197,-160,zz) for zz in [-30,30]]
    add('gear_case',housing.cut(cq.Compound.makeCompound(holes)),'aluminium')
    # Oil inventory is specified independently, not all unfilled cavity volume.
    oil=box(20,140,yl+10,yh-10,zl+8,zl+28)
    for shape in parts.values():
        if shape.BoundingBox().xmin<140 and shape.BoundingBox().xmax>20:oil=oil.cut(shape)
    add('oil_inventory',oil,'oil','fluid')
    xd=b['near_face_x_mm'];th=br['thickness_mm'];ro=br['outer_diameter_mm']/2;ri=b['friction_inner_radius_mm'];f=b['face_plate_mm'];pilot=br['pilot_diameter_mm']/2
    rotor=[ring(ro,ri,xd,xd+f),ring(ro,ri,xd+th-f,xd+th),ring(88,pilot,xd-20,xd-15),ring(88,79,xd-15,xd)]
    for k in range(b['vane_count']):rotor.append(box(xd+f,xd+th-f,ri,ro-2,-b['vane_width_mm']/2,b['vane_width_mm']/2).rotate((0,0,0),(1,0,0),360*k/b['vane_count']))
    bolt_holes=[]
    for k in range(b['hub_bolt_count']):
        a=2*math.pi*k/b['hub_bolt_count'];bolt_holes.append(cyl(b['hub_bolt_hole_mm']/2,xd-26,xd-14,b['hub_pcd_mm']/2*math.cos(a),b['hub_pcd_mm']/2*math.sin(a)))
    add('brake_disc_hat',fused(rotor).cut(cq.Compound.makeCompound(bolt_holes)),'cast_iron')
    hub=fused([ring(65,r['output_shaft_diameter_mm']/2,xd-25,xd-20),ring(pilot,r['output_shaft_diameter_mm']/2,xd-25,xd)])
    add('disc_hub',hub.cut(cq.Compound.makeCompound(bolt_holes)),'steel')
    # Caliper C envelope clears rotor sweep; pads face a 0.5mm running gap.
    caliper=box(xd-18,xd+40,-178,-90,-45,45).cut(box(xd-9,xd+31,-145,-85,-46,46))
    add('caliper',caliper.cut(cq.Compound.makeCompound(holes)),'aluminium')
    add('pad_near',box(xd-9,xd-b['pad_running_gap_mm'],-132,-95,-24,24),'pad')
    add('pad_far',box(xd+th+b['pad_running_gap_mm'],xd+31,-132,-95,-24,24),'pad')
    bracket=fused([box(160,xd-18,-175,-145,-45,45),box(160,170,-145,-105,-45,45)])
    add('caliper_reaction_bracket',bracket.cut(cq.Compound.makeCompound(holes)),'steel')
    # Actual mounting holes exist; bolt preload/friction/slip/fatigue remain unknown.
    for k,zz in enumerate([-30,30]):add(f'caliper_mount_bolt_{k+1}',cyl(5,148,xd-9,-160,zz),'steel')
    if case!='Case0':
        sx=xd-s['disc_gap_mm']-s['thickness_mm'];layers=[sx]
        if case=='CaseB':layers=[sx-s['double_air_gap_mm']-s['thickness_mm'],sx]
        shields=[]
        for k,xx in enumerate(layers):shields.append(shield(p,xx))
        if case=='CaseC':
            z0=145;h=s['duct_height_mm'];cx=xd+11;shift=h*math.tan(math.radians(s['outlet_angle_deg']));wx=s['duct_width_x_mm'];wy=s['duct_width_y_mm'];tt=s['thickness_mm']
            def loft(w,hwidth):
                return cq.Workplane('XY',origin=(cx,0,z0)).rect(w,hwidth).workplane(offset=h).center(shift,0).rect(w,hwidth).loft().val()
            duct=loft(wx,wy).cut(loft(wx-2*tt,wy-2*tt))
            tabs=[box(sx+tt,cx-wx/2+tt,-22,-18,140,148),box(sx+tt,cx-wx/2+tt,18,22,140,148)]
            shields[0]=fused([shields[0],duct]+tabs)
        for k,sh in enumerate(shields):add(f'shield_layer_{k+1}',sh,'stainless')
        intervals=[(160,layers[0])]+[(layers[k]+s['thickness_mm'],layers[k+1]) for k in range(len(layers)-1)]
        for j,(lo,hi) in enumerate(intervals):
            for k,a in enumerate([30,90,330]):
                yy,zz=145*math.cos(math.radians(a)),145*math.sin(math.radians(a))
                add(f'shield_standoff_{j}_{k}',ring(4,2.2,lo,hi,yy,zz),'stainless')
    return dict(parts=parts,materials=materials,roles=roles,axes=axes,case=case,parameters=p)

def air_domain(model):
    # Local external domain only, separate from oil and water. Open ports are
    # not CFD boundary conditions; domain extent/rotation/mesh remain M5 work.
    air=box(160,290,-210,320,-190,285)
    for sh in model['parts'].values():
        bb=sh.BoundingBox()
        if bb.xmax>160 and bb.xmin<290:air=air.cut(sh)
    assert air.isValid() and air.Volume()>0
    return air
