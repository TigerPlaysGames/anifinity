import math
import struct
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "models"
OUT.mkdir(exist_ok=True)


def prism(poly, z0, z1):
    n = len(poly)
    verts = [(x, y, z0) for x, y in poly] + [(x, y, z1) for x, y in poly]
    faces = []
    for i in range(1, n - 1):
        faces.append((0, i + 1, i))
        faces.append((n, n + i, n + i + 1))
    for i in range(n):
        j = (i + 1) % n
        faces.extend([(i, j, n + j), (i, n + j, n + i)])
    return verts, faces


def annulus(cx, cy, ro, ri, z0, z1, segments=64):
    verts = []
    for z in (z0, z1):
        for r in (ro, ri):
            for i in range(segments):
                a = 2 * math.pi * i / segments
                verts.append((cx + r * math.cos(a), cy + r * math.sin(a), z))
    faces = []
    oo, oi, to, ti = 0, segments, 2 * segments, 3 * segments
    for i in range(segments):
        j = (i + 1) % segments
        faces += [
            (to+i, to+j, ti+j), (to+i, ti+j, ti+i),
            (oo+i, oi+j, oo+j), (oo+i, oi+i, oi+j),
            (oo+i, oo+j, to+j), (oo+i, to+j, to+i),
            (oi+i, ti+j, oi+j), (oi+i, ti+i, ti+j),
        ]
    return verts, faces


def rounded_rect(w, h, r, segments=12):
    pts = []
    for cx, cy, start in ((w/2-r, h/2-r, 0), (-w/2+r, h/2-r, 90),
                          (-w/2+r, -h/2+r, 180), (w/2-r, -h/2+r, 270)):
        for k in range(segments + 1):
            a = math.radians(start + 90*k/segments)
            pts.append((cx + r*math.cos(a), cy + r*math.sin(a)))
    return pts


def add(meshes, part):
    vs, fs = part
    offset = sum(len(v) for v, _ in meshes)
    meshes.append((vs, [(a+offset, b+offset, c+offset) for a, b, c in fs]))


def write_stl(path, meshes, name):
    verts = [p for vs, _ in meshes for p in vs]
    faces = [f for _, fs in meshes for f in fs]
    with open(path, "wb") as f:
        f.write(name.encode("ascii", "ignore")[:80].ljust(80, b" "))
        f.write(struct.pack("<I", len(faces)))
        for a, b, c in faces:
            p, q, r = verts[a], verts[b], verts[c]
            ux, uy, uz = q[0]-p[0], q[1]-p[1], q[2]-p[2]
            vx, vy, vz = r[0]-p[0], r[1]-p[1], r[2]-p[2]
            nx, ny, nz = uy*vz-uz*vy, uz*vx-ux*vz, ux*vy-uy*vx
            mag = math.sqrt(nx*nx+ny*ny+nz*nz) or 1
            f.write(struct.pack("<12fH", nx/mag, ny/mag, nz/mag, *p, *q, *r, 0))


# Original decorative overlay: 50 x 240 mm, suitable for a 256 mm P1S plate.
base = []
add(base, prism(rounded_rect(50, 240, 4), 0, 1.6))

white = []
# Masked head and scarf: bold, original geometric silhouette.
add(white, prism([(-14,72), (-9,88), (0,98), (9,88), (14,72), (9,58),
                  (0,50), (-9,58)], 1.6, 2.4))
add(white, prism([(-10,75), (-3,70), (-7,66)], 2.4, 2.8))
add(white, prism([(10,75), (3,70), (7,66)], 2.4, 2.8))
add(white, prism([(-16,50), (0,38), (16,50), (12,35), (0,25), (-12,35)], 1.6, 2.4))

# Thick speed strokes, deliberately sparse for reliable two-color printing.
for poly in [
    [(-18,108), (-8,121), (-12,105), (-21,92)],
    [(6,116), (18,132), (13,110), (3,95)],
    [(-19,18), (-9,32), (-13,12), (-21,-2)],
    [(8,20), (20,38), (15,13), (4,-4)],
    [(-18,-55), (-7,-38), (-12,-64), (-21,-79)],
    [(7,-48), (19,-30), (14,-58), (3,-75)],
]:
    add(white, prism(poly, 1.6, 2.4))

# Original energy crest near lower third.
add(white, annulus(0, -92, 15, 11, 1.6, 2.4))
add(white, annulus(0, -92, 7, 4, 1.6, 2.4))
for a in range(0, 360, 45):
    t = math.radians(a)
    px, py = math.cos(t), math.sin(t)
    sx, sy = -py, px
    r1, r2, half = 16, 23, 1.4
    poly = [((r1*px)+(half*sx), -92+(r1*py)+(half*sy)),
            ((r2*px)+(half*sx), -92+(r2*py)+(half*sy)),
            ((r2*px)-(half*sx), -92+(r2*py)-(half*sy)),
            ((r1*px)-(half*sx), -92+(r1*py)-(half*sy))]
    add(white, prism(poly, 1.6, 2.4))

write_stl(OUT / "cyber_shinobi_insert_black_base.stl", base, "Anifinity cyber shinobi black base")
write_stl(OUT / "cyber_shinobi_insert_white_detail.stl", white, "Anifinity cyber shinobi white detail")
write_stl(OUT / "cyber_shinobi_insert_combined_preview.stl", base + white, "Anifinity cyber shinobi combined")

print("Created black base, white detail, and combined preview STLs")
