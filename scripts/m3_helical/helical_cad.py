"""Independent S3 transverse-system helical revision; old CAD is read-only.

Involute flanks use the same six straight segments as the archived spur model.
OCCT screw extrusion creates genuinely helical side surfaces, not rotated spur
solids. Transverse pressure angle, addendum and dedendum remain unchanged.
"""
import functools, math, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'scripts/m3_review'))
import review_cad as old
import cadquery as cq
import yaml

def settings():
    p = yaml.safe_load((ROOT/'configs/m3_helical.yaml').read_text(encoding='utf-8'))
    assert all(v is None for v in p['unknown_actual'].values())
    assert p['helix_angle_deg'] == 20 and p['transverse_pressure_angle_deg'] == 20
    return p

@functools.lru_cache(maxsize=8)
def helical_gear(mt, z, bore, width, x, yc, zc, phase, backlash):
    beta = math.radians(settings()['helix_angle_deg'])
    # Both pinions RH, both driven wheels LH about the common positive x axis.
    hand = 1 if z == 20 else -1
    rp = mt*z/2
    twist = math.degrees(hand*width*math.tan(beta)/rp)
    # Reuse the exact archived polygonal involute section, including backlash.
    straight = old_spur(mt, z, 0, 1, 0, 0, 0, phase-twist/2, backlash)
    face = min(straight.Faces(), key=lambda f: abs(f.Center().x))
    assert abs(face.Center().x) < 1e-7
    wire = face.outerWire()
    solid = cq.Solid.extrudeLinearWithRotation(wire, [], cq.Vector(0,0,0), cq.Vector(width,0,0), twist)
    solid = solid.translate((x,yc,zc))
    if bore > 0:
        solid = solid.cut(old.cyl(bore/2,x-.1,x+width+.1,yc,zc))
    assert solid.isValid() and len(solid.Solids()) == 1
    return solid

old_spur = old.gear

def build(case='Case0', thermal=False):
    # Restore the module immediately: no hidden persistent mutation of old API.
    previous = old.gear
    try:
        old.gear = helical_gear
        return old.build_review(50,case,thermal)
    finally:
        old.gear = previous
