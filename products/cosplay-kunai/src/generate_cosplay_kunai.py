from __future__ import annotations

import math
import struct
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
MODEL_OUTPUT = ROOT / "models" / "historical"
RENDER_OUTPUT = ROOT / "renders" / "previews"
MODEL_OUTPUT.mkdir(parents=True, exist_ok=True)
RENDER_OUTPUT.mkdir(parents=True, exist_ok=True)


Triangle = tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]


def signed_area(points: list[tuple[float, float]]) -> float:
    return 0.5 * sum(
        points[i][0] * points[(i + 1) % len(points)][1]
        - points[(i + 1) % len(points)][0] * points[i][1]
        for i in range(len(points))
    )


def extrude_polygon(points: list[tuple[float, float]], z0: float, z1: float) -> list[Triangle]:
    """Extrude a convex, counter-clockwise polygon into a closed triangle mesh."""
    if signed_area(points) < 0:
        points = list(reversed(points))

    cx = sum(p[0] for p in points) / len(points)
    cy = sum(p[1] for p in points) / len(points)
    tris: list[Triangle] = []

    for i, p0 in enumerate(points):
        p1 = points[(i + 1) % len(points)]
        # Top and bottom fans.
        tris.append(((cx, cy, z1), (p0[0], p0[1], z1), (p1[0], p1[1], z1)))
        tris.append(((cx, cy, z0), (p1[0], p1[1], z0), (p0[0], p0[1], z0)))
        # Outside wall.
        tris.append(((p0[0], p0[1], z0), (p1[0], p1[1], z0), (p1[0], p1[1], z1)))
        tris.append(((p0[0], p0[1], z0), (p1[0], p1[1], z1), (p0[0], p0[1], z1)))
    return tris


def rounded_rectangle(cx: float, cy: float, width: float, height: float, radius: float, segments: int = 8) -> list[tuple[float, float]]:
    radius = min(radius, width / 2, height / 2)
    corners = [
        (cx + width / 2 - radius, cy + height / 2 - radius, 0),
        (cx - width / 2 + radius, cy + height / 2 - radius, 90),
        (cx - width / 2 + radius, cy - height / 2 + radius, 180),
        (cx + width / 2 - radius, cy - height / 2 + radius, 270),
    ]
    points: list[tuple[float, float]] = []
    for x, y, start in corners:
        for i in range(segments + 1):
            a = math.radians(start + i * 90 / segments)
            points.append((x + radius * math.cos(a), y + radius * math.sin(a)))
    return points


def annulus(cx: float, cy: float, outer_r: float, inner_r: float, z0: float, z1: float, segments: int = 96) -> list[Triangle]:
    tris: list[Triangle] = []
    for i in range(segments):
        a0 = 2 * math.pi * i / segments
        a1 = 2 * math.pi * (i + 1) / segments
        o0 = (cx + outer_r * math.cos(a0), cy + outer_r * math.sin(a0))
        o1 = (cx + outer_r * math.cos(a1), cy + outer_r * math.sin(a1))
        i0 = (cx + inner_r * math.cos(a0), cy + inner_r * math.sin(a0))
        i1 = (cx + inner_r * math.cos(a1), cy + inner_r * math.sin(a1))

        # Top and bottom annular faces.
        tris.extend(
            [
                ((o0[0], o0[1], z1), (o1[0], o1[1], z1), (i1[0], i1[1], z1)),
                ((o0[0], o0[1], z1), (i1[0], i1[1], z1), (i0[0], i0[1], z1)),
                ((o0[0], o0[1], z0), (i1[0], i1[1], z0), (o1[0], o1[1], z0)),
                ((o0[0], o0[1], z0), (i0[0], i0[1], z0), (i1[0], i1[1], z0)),
            ]
        )
        # Outer wall and inner wall.
        tris.extend(
            [
                ((o0[0], o0[1], z0), (o1[0], o1[1], z0), (o1[0], o1[1], z1)),
                ((o0[0], o0[1], z0), (o1[0], o1[1], z1), (o0[0], o0[1], z1)),
                ((i0[0], i0[1], z0), (i1[0], i1[1], z1), (i1[0], i1[1], z0)),
                ((i0[0], i0[1], z0), (i0[0], i0[1], z1), (i1[0], i1[1], z1)),
            ]
        )
    return tris


def cylinder_x(x0: float, x1: float, radius: float, segments: int = 48) -> list[Triangle]:
    """Closed cylinder whose axis runs along X."""
    tris: list[Triangle] = []
    c0 = (x0, 0.0, 0.0)
    c1 = (x1, 0.0, 0.0)
    for i in range(segments):
        a0 = 2 * math.pi * i / segments
        a1 = 2 * math.pi * (i + 1) / segments
        p00 = (x0, radius * math.cos(a0), radius * math.sin(a0))
        p01 = (x0, radius * math.cos(a1), radius * math.sin(a1))
        p10 = (x1, radius * math.cos(a0), radius * math.sin(a0))
        p11 = (x1, radius * math.cos(a1), radius * math.sin(a1))
        tris += [(p00, p10, p11), (p00, p11, p01), (c0, p01, p00), (c1, p10, p11)]
    return tris


def torus_z(cx: float, cy: float, major_r: float, tube_r: float, major_segments: int = 96, tube_segments: int = 20) -> list[Triangle]:
    """Torus centered in the XY blade plane with its hole axis along Z."""
    tris: list[Triangle] = []

    def p(u: float, v: float) -> tuple[float, float, float]:
        radial = major_r + tube_r * math.cos(v)
        return (cx + radial * math.cos(u), cy + radial * math.sin(u), tube_r * math.sin(v))

    for i in range(major_segments):
        u0 = 2 * math.pi * i / major_segments
        u1 = 2 * math.pi * (i + 1) / major_segments
        for j in range(tube_segments):
            v0 = 2 * math.pi * j / tube_segments
            v1 = 2 * math.pi * (j + 1) / tube_segments
            p00, p10, p11, p01 = p(u0, v0), p(u1, v0), p(u1, v1), p(u0, v1)
            tris += [(p00, p10, p11), (p00, p11, p01)]
    return tris


def helix_tube_x(x0: float, x1: float, helix_r: float, tube_r: float, pitch: float, turns_steps: int = 420, tube_steps: int = 10) -> list[Triangle]:
    """A small raised helical tube around the grip to represent cloth wrapping."""
    tris: list[Triangle] = []
    turns = (x1 - x0) / pitch

    def ring_point(t: float, phi: float) -> tuple[float, float, float]:
        theta = 2 * math.pi * turns * t
        x = x0 + (x1 - x0) * t
        radial = np.array((0.0, math.cos(theta), math.sin(theta)), dtype=float)
        tangent = np.array(
            ((x1 - x0), -2 * math.pi * turns * helix_r * math.sin(theta), 2 * math.pi * turns * helix_r * math.cos(theta)),
            dtype=float,
        )
        tangent /= np.linalg.norm(tangent)
        binormal = np.cross(tangent, radial)
        binormal /= np.linalg.norm(binormal)
        center = np.array((x, helix_r * math.cos(theta), helix_r * math.sin(theta)), dtype=float)
        point = center + tube_r * (math.cos(phi) * radial + math.sin(phi) * binormal)
        return tuple(point.tolist())

    for i in range(turns_steps):
        t0, t1 = i / turns_steps, (i + 1) / turns_steps
        for j in range(tube_steps):
            p0, p1 = 2 * math.pi * j / tube_steps, 2 * math.pi * (j + 1) / tube_steps
            q00, q10, q11, q01 = ring_point(t0, p0), ring_point(t1, p0), ring_point(t1, p1), ring_point(t0, p1)
            tris += [(q00, q10, q11), (q00, q11, q01)]
    return tris


def faceted_blade(outline: list[tuple[float, float]], apex_xy: tuple[float, float], edge_half_thickness: float, apex_half_thickness: float) -> list[Triangle]:
    """Create the characteristic convex Naruto-style blade from two faceted fans."""
    if signed_area(outline) < 0:
        outline = list(reversed(outline))
    ax, ay = apex_xy
    top = (ax, ay, apex_half_thickness)
    bottom = (ax, ay, -apex_half_thickness)
    tris: list[Triangle] = []
    for i, p0 in enumerate(outline):
        p1 = outline[(i + 1) % len(outline)]
        t0, t1 = (p0[0], p0[1], edge_half_thickness), (p1[0], p1[1], edge_half_thickness)
        b0, b1 = (p0[0], p0[1], -edge_half_thickness), (p1[0], p1[1], -edge_half_thickness)
        tris += [(top, t0, t1), (bottom, b1, b0), (b0, b1, t1), (b0, t1, t0)]
    return tris


def normal(tri: Triangle) -> tuple[float, float, float]:
    a, b, c = (np.asarray(v, dtype=float) for v in tri)
    n = np.cross(b - a, c - a)
    length = float(np.linalg.norm(n))
    return (0.0, 0.0, 0.0) if length == 0 else tuple((n / length).tolist())


def write_binary_stl(path: Path, triangles: list[Triangle]) -> None:
    with path.open("wb") as f:
        header = b"Blunt cosplay kunai - nonfunctional costume prop"
        f.write(header.ljust(80, b" ")[:80])
        f.write(struct.pack("<I", len(triangles)))
        for tri in triangles:
            values = [*normal(tri), *tri[0], *tri[1], *tri[2]]
            f.write(struct.pack("<12fH", *values, 0))


def build_mesh() -> list[Triangle]:
    tris: list[Triangle] = []

    # Ratios measured from several straight-on images of the licensed 28–29 cm
    # replicas: blade ~= 52%, wrapped grip ~= 32%, ring assembly ~= 16%.
    # The overall size is 280 mm, matching the licensed foam cosplay version.
    blade = [
        (-145.0, -2.0),
        (-42.0, -22.5),
        (-4.0, -7.0),
        (-4.0, 7.0),
        (-42.0, 22.5),
        (-145.0, 2.0),
    ]
    tris += faceted_blade(blade, (-42.0, 0.0), edge_half_thickness=1.8, apex_half_thickness=12.5)

    # Rounded blade collar, cylindrical wrapped handle, end collar, and connector.
    tris += cylinder_x(-5.0, 4.0, 9.5)
    tris += cylinder_x(2.0, 96.0, 7.0)
    tris += cylinder_x(93.0, 101.0, 8.8)
    tris += cylinder_x(98.0, 103.0, 5.0)
    tris += helix_tube_x(5.0, 93.0, helix_r=7.15, tube_r=0.85, pitch=8.0)

    # Rounded 36 mm OD / 18 mm ID torus pommel, rather than a flat washer.
    tris += torus_z(117.0, 0.0, major_r=13.5, tube_r=4.5)
    return tris


def render_preview(path: Path) -> None:
    scale = 4
    width, height = 1040, 340
    image = Image.new("RGB", (width, height), (27, 30, 38))
    draw = ImageDraw.Draw(image)

    def pt(x: float, y: float) -> tuple[int, int]:
        return (int(590 + x * 3.35), int(height / 2 - y * 3.35))

    blade = [(-145, -2), (-42, -22.5), (-4, -7), (-4, 7), (-42, 22.5), (-145, 2)]
    draw.polygon([pt(*p) for p in blade], fill=(24, 29, 29), outline=(117, 128, 125), width=3)
    draw.line([pt(-145, 0), pt(-42, 0), pt(-4, 0)], fill=(88, 99, 96), width=3)
    draw.line([pt(-42, -22.5), pt(-42, 22.5)], fill=(55, 64, 62), width=2)
    draw.rounded_rectangle([*pt(-5, 9.5), *pt(4, -9.5)], radius=10, fill=(22, 26, 27), outline=(90, 99, 97), width=2)
    draw.rectangle([*pt(2, 7), *pt(96, -7)], fill=(228, 222, 205), outline=(75, 79, 77), width=2)
    # Alternating diagonal strokes convey the wrapped grip in the preview.
    for x in range(4, 95, 8):
        draw.line([pt(x, -7), pt(x + 7, 7)], fill=(165, 159, 145), width=4)
    draw.rounded_rectangle([*pt(93, 8.8), *pt(101, -8.8)], radius=9, fill=(22, 26, 27), outline=(90, 99, 97), width=2)
    ring_box = [pt(99, 18), pt(135, -18)]
    draw.ellipse([ring_box[0][0], ring_box[0][1], ring_box[1][0], ring_box[1][1]], fill=(25, 30, 30), outline=(117, 128, 125), width=3)
    hole_box = [pt(108, 9), pt(126, -9)]
    draw.ellipse([hole_box[0][0], hole_box[0][1], hole_box[1][0], hole_box[1][1]], fill=(27, 30, 38), outline=(10, 12, 17), width=2)

    draw.text((24, 24), "LICENSED-REFERENCE COSPLAY KUNAI — 280 mm", fill=(242, 244, 247))
    draw.text((24, 48), "52% faceted blade • 32% wrapped grip • 16% rounded ring assembly", fill=(170, 180, 194))
    image.resize((width // 2, height // 2), Image.Resampling.LANCZOS).save(path)


if __name__ == "__main__":
    mesh = build_mesh()
    stl_path = MODEL_OUTPUT / "cosplay_kunai_v3_reference_proportions.stl"
    preview_path = RENDER_OUTPUT / "cosplay_kunai_v3_preview.png"
    write_binary_stl(stl_path, mesh)
    render_preview(preview_path)
    print(f"Wrote {stl_path} with {len(mesh)} triangles")
    print(f"Wrote {preview_path}")
