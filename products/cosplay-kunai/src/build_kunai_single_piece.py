from pathlib import Path

import cadquery as cq
from cadquery import exporters


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "models" / "historical"
OUT.mkdir(parents=True, exist_ok=True)

STL_PATH = OUT / "cosplay_kunai_single_piece.stl"
STEP_PATH = OUT / "cosplay_kunai_single_piece.step"


def cylinder_x(x0: float, x1: float, radius: float) -> cq.Workplane:
    """Solid round cylinder along the X axis."""
    return cq.Workplane("YZ", origin=(x0, 0, 0)).circle(radius).extrude(x1 - x0)


# Restore the original narrow, faceted blade proportions. A chamfer on both
# faces produces the raised-center/falling-edge look without separate meshes.
blade_outline = [
    (-145.0, -2.0),
    (-42.0, -22.5),
    (-4.0, -7.0),
    (-4.0, 7.0),
    (-42.0, 22.5),
    (-145.0, 2.0),
]
blade = (
    cq.Workplane("XY")
    .polyline(blade_outline)
    .close()
    .extrude(12.0)
    .translate((0, 0, -6.0))
    .edges("not |Z")
    .chamfer(2.2)
)

# Original-style round grip and collars. Every neighboring part overlaps by at
# least 2 mm, allowing CadQuery to create one real Boolean union.
front_collar = cylinder_x(-7.0, 5.0, 9.5)
grip = cylinder_x(2.0, 97.0, 7.0)
rear_collar = cylinder_x(93.0, 103.0, 8.8)
connector = cylinder_x(99.0, 108.0, 5.2)

# Recessed wrap bands are cut into the grip rather than added as loose parts.
for x in range(10, 93, 9):
    cutter = (
        cq.Workplane("XY")
        .center(x, 0)
        .rect(1.25, 18.0)
        .extrude(2.0)
        .translate((0, 0, 5.7))
        .rotate((x, 0, 0), (x, 0, 1), -28)
    )
    grip = grip.cut(cutter)

# Rounded torus pommel from the original design: 36 mm OD and 18 mm opening.
torus = cq.Solid.makeTorus(
    13.5,
    4.5,
    cq.Vector(117.0, 0.0, 0.0),
    cq.Vector(0.0, 0.0, 1.0),
)
ring = cq.Workplane("XY").newObject([torus])

kunai = (
    blade
    .union(front_collar)
    .union(grip)
    .union(rear_collar)
    .union(connector)
    .union(ring)
    .clean()
)

solid_count = kunai.solids().size()
if solid_count != 1:
    raise RuntimeError(f"Expected one fused solid, found {solid_count}")

exporters.export(kunai, str(STL_PATH), tolerance=0.035, angularTolerance=0.07)
exporters.export(kunai, str(STEP_PATH))

box = kunai.val().BoundingBox()
print({
    "solid_count": solid_count,
    "dimensions_mm": [round(box.xlen, 2), round(box.ylen, 2), round(box.zlen, 2)],
    "round_grip_diameter_mm": 14.0,
    "ring_outside_diameter_mm": 36.0,
    "ring_inside_diameter_mm": 18.0,
    "stl": str(STL_PATH),
    "step": str(STEP_PATH),
})
