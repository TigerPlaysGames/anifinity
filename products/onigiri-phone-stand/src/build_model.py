from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

import cadquery as cq
from cadquery import exporters

OUT = ROOT / "models"
OUT.mkdir(parents=True, exist_ok=True)

# Design parameters, millimetres.
BASE_W, BASE_D, BASE_H = 132.0, 96.0, 6.0
BODY_W, BODY_H, CORE_T = 122.0, 126.0, 5.0
LEAN_DEG = -20.0               # 70 degrees above the desktop
SHELL_T = 2.4
PEG_D, HOLE_D = 4.0, 4.45      # 0.225 mm radial press-fit clearance
SHELF_DEPTH, LIP_H = 23.0, 8.5
CABLE_GAP = 18.0


def rounded_onigiri(w, h):
    """Smooth sampled Bezier outline with a gently rounded rice-ball crown."""
    def bezier(p0, p1, p2, p3, t):
        u = 1-t
        return (u**3*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3*p3[0],
                u**3*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3*p3[1])
    left = [bezier((-0.43*w,0),(-0.54*w,0.30*h),(-0.28*w,0.84*h),(0,h),i/16) for i in range(17)]
    right = [(-x,z) for x,z in reversed(left[:-1])]
    bottom = []
    for i in range(1,9):
        t=i/9
        bottom.append((0.43*w*(1-2*t), -3.5*4*t*(1-t)))
    return left + right + bottom


def local_body(profile, y_start, thickness):
    return (
        cq.Workplane("XZ")
        .workplane(offset=y_start)
        .polyline(profile)
        .close()
        .extrude(thickness)
    )


def rotate_about_anchor(obj):
    return obj.rotate((0, 0, BASE_H), (1, 0, BASE_H), LEAN_DEG)


profile = rounded_onigiri(BODY_W, BODY_H)

# BLACK STRUCTURAL CORE -----------------------------------------------------
core_plate_local = local_body(profile, -CORE_T/2, CORE_T)

# Four blind sockets in the front of the core for the white decorative shell.
peg_points = [(-38, 38), (38, 38), (-30, 88), (30, 88)]
for x, z in peg_points:
    socket = (
        cq.Workplane("XZ")
        .workplane(offset=CORE_T/2)
        .center(x, z)
        .circle(HOLE_D/2)
        .extrude(-4.6)
    )
    core_plate_local = core_plate_local.cut(socket)

core_plate = rotate_about_anchor(core_plate_local.translate((0, 0, BASE_H)))

# Stable rounded base.
base = (
    cq.Workplane("XY")
    .box(BASE_W, BASE_D, BASE_H, centered=(True, True, False))
    .edges("|Z")
    .fillet(7.0)
)

# Horizontal split shelf and retaining lip with charging-cable clearance.
half_w = (BODY_W - CABLE_GAP) / 2
left_shelf = cq.Workplane("XY").box(half_w, SHELF_DEPTH, 5.5,
    centered=(True, True, False)).translate((-(CABLE_GAP+half_w)/2, -23, BASE_H))
right_shelf = cq.Workplane("XY").box(half_w, SHELF_DEPTH, 5.5,
    centered=(True, True, False)).translate(((CABLE_GAP+half_w)/2, -23, BASE_H))
left_lip = cq.Workplane("XY").box(half_w, 5.5, LIP_H,
    centered=(True, True, False)).translate((-(CABLE_GAP+half_w)/2, -34.5, BASE_H))
right_lip = cq.Workplane("XY").box(half_w, 5.5, LIP_H,
    centered=(True, True, False)).translate(((CABLE_GAP+half_w)/2, -34.5, BASE_H))

# One broad central rear wedge keeps the support hidden behind the onigiri body
# in every front/hero view while giving the phone plate a large load path.
rear_brace = (
    cq.Workplane("YZ")
    # Its front edge follows the tilted plate's rear surface instead of
    # crossing through it, so no support geometry shows through the face.
    .polyline([(15, BASE_H), (43, BASE_H), (43, BASE_H+5), (30, BASE_H+82)])
    .close().extrude(46).translate((-23, 0, 0))
)

black_core = base.union(core_plate).union(rear_brace).union(left_shelf).union(right_shelf).union(left_lip).union(right_lip)
black_core = black_core.clean()

# WHITE SNAP-ON RICE SHELL -------------------------------------------------
shell_local = local_body(profile, CORE_T/2, SHELL_T)

# Reveal the black core as a nori patch and kawaii facial features.
nori_window = (
    cq.Workplane("XZ").workplane(offset=CORE_T/2 - 0.2)
    .center(0, 25).rect(80, 48).extrude(SHELL_T + 0.5)
    .edges("|Y").fillet(8)
)
shell_local = shell_local.cut(nori_window)

for x in (-21, 21):
    eye = (
        cq.Workplane("XZ").workplane(offset=CORE_T/2 - 0.2)
        .center(x, 75).ellipse(5.2, 8.5).extrude(SHELL_T + 0.5)
    )
    shell_local = shell_local.cut(eye)

mouth_outer = (cq.Workplane("XZ").workplane(offset=CORE_T/2 - 0.2)
    .center(0, 61).ellipse(11, 6).extrude(SHELL_T + 0.5))
mouth_inner = (cq.Workplane("XZ").workplane(offset=CORE_T/2 - 0.3)
    .center(0, 64).ellipse(9, 5).extrude(SHELL_T + 0.7))
mouth = mouth_outer.cut(mouth_inner)
shell_local = shell_local.cut(mouth)

# Press-fit pegs grow from the shell's rear into the core sockets.
for x, z in peg_points:
    peg = (
        cq.Workplane("XZ").workplane(offset=CORE_T/2)
        .center(x, z).circle(PEG_D/2).extrude(-4.0)
    )
    # Small lead-in nose eases assembly.
    lead = (
        cq.Workplane("XZ").workplane(offset=CORE_T/2 - 4.0)
        .center(x, z).circle((PEG_D-0.7)/2).extrude(-0.6)
    )
    shell_local = shell_local.union(peg).union(lead)

white_shell = rotate_about_anchor(shell_local.translate((0, 0, BASE_H))).clean()

# Export manufacturing and review formats.
exporters.export(black_core, str(OUT / "black_core.stl"), tolerance=0.05, angularTolerance=0.1)
exporters.export(white_shell, str(OUT / "white_shell.stl"), tolerance=0.05, angularTolerance=0.1)
exporters.export(black_core, str(OUT / "black_core.step"))
exporters.export(white_shell, str(OUT / "white_shell.step"))

assembly = cq.Assembly(name="Onigiri Phone Stand V2")
assembly.add(black_core, name="Black structural core", color=cq.Color(0.04, 0.04, 0.04))
assembly.add(white_shell, name="White snap-on rice shell", color=cq.Color(0.95, 0.95, 0.92))
assembly.save(str(OUT / "assembly.step"))

print({
    "base_mm": [BASE_W, BASE_D, BASE_H],
    "body_mm": [BODY_W, BODY_H, CORE_T],
    "phone_angle_deg": 90 + LEAN_DEG,
    "shelf_depth_mm": SHELF_DEPTH,
    "cable_gap_mm": CABLE_GAP,
    "press_fit_radial_clearance_mm": (HOLE_D - PEG_D)/2,
})
