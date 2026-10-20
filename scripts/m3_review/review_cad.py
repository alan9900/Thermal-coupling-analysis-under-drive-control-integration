"""Independent M3 refinement; original M3 and M2 artefacts are read-only.

All added interfaces are S3 proposals. Keys are explicit fitted rectangles,
collars/rings equivalent retention envelopes, seals equivalent lip annuli.
No threads, rolling contacts, pretension or structural solution are implied.
"""
import copy,math,sys
from pathlib import Path
import cadquery as cq
import yaml
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/m3'))
from cad_model import config,build,box,cyl,ring,fused,gear

def review_config():
    p=yaml.safe_load((ROOT/'configs/m3_geometry_review.yaml').read_text(encoding='utf-8'))
    assert all(x is None for x in p['unknown_actual'].values())
    return p

def build_review(d=50,case='Case0',thermal=False,base=None):
    q=review_config();r=q['design'];p=config();p['reducer']['output_shaft_diameter_mm']=d
    m=copy.copy(base) if base else build(config(),case)
    # Fresh dictionaries: never mutate the shared concept model.
    m['parts']=dict(m['parts']);m['materials']=dict(m['materials']);m['roles']=dict(m['roles'])
    P=m['parts'];M=m['materials'];R=m['roles'];axes=m['axes']
    def remove(n):
        P.pop(n,None);M.pop(n,None);R.pop(n,None)
    def add(n,sh,mat='steel',role='solid'):
        assert sh.isValid() and sh.Volume()>0,n
        P[n]=sh;M[n]=mat;R[n]=role
    # Keep the reference motor dimensions intact; shift it for an adapter.
    offset=r['motor_adapter_length_mm']
    for n in list(P):
        if n.startswith('motor_') and not n.startswith('motor_mount_'):
            P[n]=P[n].translate((-offset,0,0))
    y,z=axes['input']
    old=P['input_rotor_shaft'].intersect(box(-170, -20,-1000,1000,-1000,1000)).translate((-offset,0,0))
    # Original rotor shaft ends at -60 after clipping; add a separate 30mm stub.
    old=fused([old,cyl(15,-offset-25,-30,y,z)])
    remove('input_rotor_shaft');add('motor_rotor_shaft',old)
    add('motor_input_coupling',ring(23,15,-58,-12,y,z))
    # Two opposed keys on each stub; normal clearance/fit remains unverified.
    for label,x0,x1 in [('motor',-52,-34),('input',-28,-12)]:
        for sign in [-1,1]:
            key=box(x0,x1,y-4,y+4,z+sign*15-3.5,z+sign*15+3.5)
            P['motor_input_coupling']=P['motor_input_coupling'].cut(key)
            if label=='motor':P['motor_rotor_shaft']=P['motor_rotor_shaft'].cut(key)
            add(f'coupling_{label}_key_{sign}',key)
    adapter=ring(151,45,-offset,0,y,z)
    motorholes=[]
    for k,a in enumerate(p['motor_design']['mounting_angles_deg']):
        yy=y+140*math.cos(math.radians(a));zz=z+140*math.sin(math.radians(a))
        motorholes.append(cyl(5.5,-offset-9,17,yy,zz))
        remove(f'motor_mount_bolt_{k+1}');add(f'motor_mount_bolt_{k+1}',cyl(5,-offset-8,16,yy,zz))
    # Real relief pockets for neighbouring front retainers and seals.
    for ax in ['intermediate','output']:
        yy,zz=axes[ax];adapter=adapter.cut(cyl(51 if ax=='intermediate' else d/2+31,-11,.1,yy,zz))
    add('motor_gear_adapter',adapter.cut(cq.Compound.makeCompound(motorholes)),'aluminium')
    for n in ['gear_case','oil_inventory','intermediate_shaft','output_shaft','stage1_pinion','stage1_gear','stage2_pinion','stage2_gear','disc_hub','caliper','caliper_reaction_bracket','caliper_mount_bolt_1','caliper_mount_bolt_2']:
        remove(n)
    bearings={ax:r['bearing_catalogue'][ax if ax!='output' else f'output_{d}'] for ax in axes}
    shafts={}
    for ax,(yy,zz) in axes.items():
        be=bearings[ax];D=be['bore_mm'];B=be['width_mm'];ro=be['od_mm']/2
        sh=cyl(D/2,-30 if ax=='input' else -10,168.5 if ax!='output' else 268,yy,zz)
        # Locating bearing inner-ring shoulder; rear inner ring retained by collar.
        sh=fused([sh,cyl(D/2+4,B,B+5,yy,zz),cyl(D/2+4,136,160-B,yy,zz)]) if 136<160-B else fused([sh,cyl(D/2+4,B,B+5,yy,zz)])
        if ax=='intermediate':sh=fused([sh,cyl(25,30,58,yy,zz),cyl(28,28,33,yy,zz)])
        if ax=='output':sh=fused([sh,cyl((d+16)/2,90,95),cyl((d+12)/2,95,127),cyl((d+8)/2,175,215),cyl((d+8)/2,244,268)])
        shafts[ax]=sh
        for j,xb in enumerate([0,160-B]):
            remove(ax+f'_bearing_{j+1}');add(ax+f'_bearing_{j+1}',ring(ro,D/2,xb,xb+B,yy,zz))
        # Rings/collars do not claim actual circlip or clamp load capacity.
        # Front groove sits ahead of the torque-bearing span.
        groove=ring(D/2+.1,D/2-1,-3,-1,yy,zz);shafts[ax]=shafts[ax].cut(groove)
        add(ax+'_front_retaining_ring',ring(D/2+3,D/2-1,-3,-1,yy,zz))
        add(ax+'_rear_clamp_collar',ring(D/2+4,D/2,160,164,yy,zz))
        for label,x0,x1 in [('front',-6,0),('rear',160.5,164.5)]:
            add(ax+'_'+label+'_outer_retainer',ring(ro+10,D/2+5,x0,x1,yy,zz),'aluminium')
        for label,x0,x1 in [('front',-10,-6),('rear',164.5,168.5)]:
            add(ax+'_'+label+'_seal',ring(D/2+5,D/2,x0,x1,yy,zz),'seal_equivalent')
    # Integral pinions remove weak separate pinion-bore key cuts.
    shafts['input']=fused([shafts['input'],gear(2.5,20,30,25,33,*axes['input'],-90,.15)])
    shafts['intermediate']=fused([shafts['intermediate'],gear(3,20,40,32,95,*axes['intermediate'],180,.15)])
    for ax,xg,w,seat,mn,phase,keyw,keyh in [('intermediate',33,25,50,2.5,87,14,9),('output',95,32,d+12,3,-3,18 if d==50 else 16,11 if d==50 else 10)]:
        yy,zz=axes[ax];g=gear(mn,60,seat,w,xg,yy,zz,phase,.15)
        key=box(xg+1,xg+w-1,yy-keyw/2,yy+keyw/2,zz+seat/2-keyh/2,zz+seat/2+keyh/2)
        shafts[ax]=shafts[ax].cut(key);g=g.cut(key)
        add(ax+'_gear_key',key);add('stage1_gear' if ax=='intermediate' else 'stage2_gear',g)
        add(ax+'_gear_retaining_collar',ring(seat/2+5,(40 if ax=='intermediate' else d)/2,xg+w,xg+w+4,yy,zz))
    # Hub pilot enlarged 68 -> 80mm; hat and hub changed together (S3).
    P['brake_disc_hat']=P['brake_disc_hat'].cut(cyl(40,184,191))
    hub=fused([ring(65,(d+8)/2,180,185),ring(40,(d+8)/2,175,215)])
    for sign in [-1,1]:
        key=box(177,212,-6,6,sign*(d+8)/2-4,sign*(d+8)/2+4)
        shafts['output']=shafts['output'].cut(key);hub=hub.cut(key);add('hub_key_'+str(sign),key)
    disc=P['brake_disc_hat']
    for k in range(5):
        a=2*math.pi*k/5;yy=56*math.cos(a);zz=56*math.sin(a)
        hole=cyl(5.5,179,191,yy,zz);hub=hub.cut(hole)
        add('disc_hub_bolt_'+str(k+1),cyl(5,180,190,yy,zz))
    add('disc_hub',hub)
    # Independent halfshaft mating flange, pilot, bolts and fitted drive dowels.
    flange=ring(60,(d+8)/2,248,264)
    mate=fused([cyl(60,264,272),cyl(15,272,322)])
    # Separate rotating pilot in matching recess, no overlapping solids.
    pilot=ring(35,(d+8)/2,264,266);flange=fused([flange,pilot]);mate=mate.cut(cyl(35,263.9,266))
    # Mate has central bore up to shaft end; stub starts beyond end268.
    mate=mate.cut(cyl((d+8)/2,263,268))
    for sign in [-1,1]:
        key=box(248,263,-6,6,sign*(d+8)/2-4,sign*(d+8)/2+4)
        shafts['output']=shafts['output'].cut(key);flange=flange.cut(key);add('halfshaft_key_'+str(sign),key)
    for k in range(8):
        a=2*math.pi*k/8;yy=45*math.cos(a);zz=45*math.sin(a)
        hole=cyl(5.5,247,273,yy,zz);flange=flange.cut(hole);mate=mate.cut(hole)
        add('halfshaft_bolt_'+str(k+1),cyl(5,248,272,yy,zz))
    for k in range(4):
        a=math.radians(22.5+90*k);yy=45*math.cos(a);zz=45*math.sin(a)
        hole=cyl(6,255,271,yy,zz);flange=flange.cut(hole);mate=mate.cut(hole)
        add('halfshaft_drive_dowel_'+str(k+1),cyl(6,255,271,yy,zz))
    add('output_halfshaft_flange',flange);add('wheel_halfshaft_interface',mate)
    for ax,sh in shafts.items():add(ax+'_shaft',sh)
    for sign in [-1,1]:
        key=P['coupling_input_key_'+str(sign)];P['input_shaft']=P['input_shaft'].cut(key)
    # Stronger M12 bracket, wider bolt span and matching case/caliper ears.
    holes=[cyl(6.5,147,197,-160,zz) for zz in [-40,40]]
    caliper=box(187,245,-178,-90,-60,60).cut(box(196,236,-145,-85,-61,61))
    bracket=fused([box(160,187,-175,-145,-60,60),box(160,170,-145,-105,-60,60)])
    add('caliper',caliper.cut(cq.Compound.makeCompound(holes)),'aluminium')
    add('caliper_reaction_bracket',bracket.cut(cq.Compound.makeCompound(holes)))
    for k,zz in enumerate([-40,40]):add('caliper_mount_bolt_'+str(k+1),cyl(6,148,196,-160,zz))
    # Original 30deg standoff hits the new input bearing cap. Move that anchor
    # to60deg, machining matching through holes; no ignored interference pair.
    shield_anchor_holes=[]
    for k,a in enumerate([60,90,330]):
        cy=145*math.cos(math.radians(a));cz=145*math.sin(math.radians(a))
        shield_anchor_holes.append(cyl(2.25,153.9,160.1,cy,cz))
        if case!='Case0':add('shield_anchor_bolt_'+str(k+1),cyl(2,154,195,cy,cz))
    if case!='Case0':
        for n in list(P):
            if n.startswith('shield_standoff_') and n.endswith('_0'):P[n]=P[n].rotate((0,0,0),(1,0,0),30)
            if n.startswith('shield_layer_'):
                cy=145*math.cos(math.radians(60));cz=145*math.sin(math.radians(60))
                P[n]=P[n].cut(cyl(2.2,180,196,cy,cz))
    # Rebuild case with coupled bores, bearing shoulders, split line and bolts.
    housing=box(0,160,-110,285,-110,265).cut(box(6,154,-104,279,-104,259))
    bosses=[];bores=[]
    for ax,(yy,zz) in axes.items():
        be=bearings[ax];ro=be['od_mm']/2;B=be['width_mm']
        bosses += [ring(ro+10,ro,0,B+3,yy,zz),ring(ro+10,ro,157-B,160,yy,zz),
                   ring(ro+10,ro-3,B,B+3,yy,zz),ring(ro+10,ro-3,157-B,159.5-B,yy,zz)]
        bores += [cyl(ro,-.1,B,yy,zz),cyl(ro,160-B,160.1,yy,zz)]
    bosses += [cyl(12,0,16,y+140*math.cos(math.radians(a)),z+140*math.sin(math.radians(a))) for a in p['motor_design']['mounting_angles_deg']]
    feet=[box(30,70,-140,-110,-110,-80),box(100,140,285,315,-110,-80)]
    housing=fused([housing]+bosses+feet+[box(148,160,-175,-105,-60,60)])
    frameholes=[cq.Solid.makeCylinder(7,32,cq.Vector(xx,yy,-111),cq.Vector(0,0,1)) for xx,yy in [(50,-125),(120,300)]]
    # Four longitudinal tie bolts in edge bosses connect the case split.
    split_holes=[]
    for k,(yy,zz) in enumerate([(-95,-95),(270,-95),(-95,250),(270,250)]):
        housing=housing.fuse(cyl(12,0,160,yy,zz));split_holes.append(cyl(5.5,-.1,160.1,yy,zz))
        add('case_tie_bolt_'+str(k+1),cyl(5,0,160,yy,zz))
    capholes=[]
    for ax,(yy,zz) in axes.items():
        ro=bearings[ax]['od_mm']/2
        for label,x0,x1 in [('front',-6,6),('rear',154,164.5)]:
            for k,a in enumerate([45,135,225,315]):
                cy=yy+(ro+5)*math.cos(math.radians(a));cz=zz+(ro+5)*math.sin(math.radians(a))
                cut=cyl(2.75,x0-.1,x1+.1,cy,cz);capholes.append(cut)
                name=ax+'_'+label+'_outer_retainer';P[name]=P[name].cut(cut)
                add(f'{ax}_{label}_cap_bolt_{k+1}',cyl(2.5,x0,x1,cy,cz))
    housing=housing.cut(cq.Compound.makeCompound(bores+holes+motorholes+frameholes+split_holes+capholes+shield_anchor_holes)).clean()
    add('gear_case_front',housing.intersect(box(-1,80,-500,500,-500,500)),'aluminium')
    add('gear_case_rear',housing.intersect(box(80,161,-500,500,-500,500)),'aluminium')
    oil=box(20,140,-100,275,-102,-82)
    for sh in P.values():
        bb=sh.BoundingBox()
        if bb.xmax>20 and bb.xmin<140:oil=oil.cut(sh)
    add('oil_inventory',oil,'oil','fluid')
    # Thermal version: smooth equal-volume gear regions, one connected winding,
    # omit macro bolts ONLY when their parallel conductance is mapped separately.
    if thermal:
        for n,x,w,bore,yy,zz in [('stage1_gear',33,25,50,120,0),('stage2_gear',95,32,d+12,0,0)]:
            # Preserve keyed bore; equivalent smooth OD adjusted to conserve V.
            original=P[n];ro=math.sqrt(original.Volume()/(math.pi*w)+(bore/2)**2)
            ax='input' if n=='stage1_gear' else 'intermediate'
            # Reserve the complete pinion swept envelope plus 0.2 mm. This
            # prevents smooth gears from intersecting a toothed mating pinion.
            cutter=cq.Compound.makeCompound([cyl(27.5+.2 if n=='stage1_gear' else 33+.2,x-.1,x+w+.1,*axes[ax]),P['oil_inventory']])
            # Correct missing keycut volume analytically via scalar bisection.
            lo,hi=ro,ro+8
            for _ in range(30):
                mid=(lo+hi)/2;sh=ring(mid,bore/2,x,x+w,yy,zz).cut(P['intermediate_gear_key' if n=='stage1_gear' else 'output_gear_key']).cut(cutter)
                if sh.Volume()<original.Volume():lo=mid
                else:hi=mid
            P[n]=sh
        # Integral pinions are retained to avoid accidentally changing shaft C
        # or creating thermally disconnected rings. Only driven gears simplified.
        wires=P['motor_winding'].Solids();P['motor_winding']=fused(wires)
    m.update(case=case,parameters=p,output_diameter_mm=d,variant='thermal' if thermal else 'full',bearings=bearings)
    return m

def external_air(m):
    sh=box(168,350,-220,330,-200,290)
    for s in m['parts'].values():
        bb=s.BoundingBox()
        if bb.xmax>168 and bb.xmin<350:sh=sh.cut(s)
    solids=sorted(sh.Solids(),key=lambda x:x.Volume(),reverse=True)
    return solids[0],[s.Volume() for s in solids[1:]]
