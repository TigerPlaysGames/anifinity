import math
import struct
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "outputs" / "3D Prints"
OUT.mkdir(parents=True, exist_ok=True)


def box(x0, x1, y0, y1, z0, z1):
    v = [(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),
         (x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
    f = [(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),
         (1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
    return v, f


def prism_xz(poly, y0, y1):
    n = len(poly)
    v = [(x,y0,z) for x,z in poly] + [(x,y1,z) for x,z in poly]
    f = []
    for i in range(1,n-1):
        f += [(0,i,i+1),(n,n+i+1,n+i)]
    for i in range(n):
        j=(i+1)%n
        f += [(i,j,n+j),(i,n+j,n+i)]
    return v,f


def ellipse(cx, cz, rx, rz, n=40):
    return [(cx+rx*math.cos(2*math.pi*i/n), cz+rz*math.sin(2*math.pi*i/n)) for i in range(n)]


def add(parts, geom):
    v,f=geom
    off=sum(len(p[0]) for p in parts)
    parts.append((v,[(a+off,b+off,c+off) for a,b,c in f]))


def write_stl(path, parts, name):
    verts=[p for v,_ in parts for p in v]
    faces=[t for _,f in parts for t in f]
    with open(path,'wb') as out:
        out.write(name.encode()[:80].ljust(80,b' ')); out.write(struct.pack('<I',len(faces)))
        for a,b,c in faces:
            p,q,r=verts[a],verts[b],verts[c]
            u=(q[0]-p[0],q[1]-p[1],q[2]-p[2]); w=(r[0]-p[0],r[1]-p[1],r[2]-p[2])
            n=(u[1]*w[2]-u[2]*w[1],u[2]*w[0]-u[0]*w[2],u[0]*w[1]-u[1]*w[0])
            m=math.sqrt(sum(x*x for x in n)) or 1
            out.write(struct.pack('<12fH',*(x/m for x in n),*p,*q,*r,0))


# Overall footprint: 126 x 88 mm; height: 128 mm. Fits a P1S easily.
white=[]
add(white,box(-63,63,-42,46,0,7))

# Rounded-looking onigiri outline, thick enough to support a phone.
outline=[(-52,8),(-56,20),(-51,52),(-40,82),(-20,108),(0,128),
         (20,108),(40,82),(51,52),(56,20),(52,8)]
add(white,prism_xz(outline,18,30))

# Rear brace wedge.
brace=[(-42,7),(-36,7),(-16,98),(16,98),(36,7),(42,7)]
add(white,prism_xz(brace,30,45))

# Phone shelf, 18 mm usable depth, with 16 mm-wide centered charging notch.
add(white,box(-56,-9,-8,18,7,15))
add(white,box(9,56,-8,18,7,15))
add(white,box(-56,-9,-16,-8,7,27))
add(white,box(9,56,-16,-8,7,27))

black=[]
# Nori patch and kawaii face, as separate raised black pieces sharing coordinates.
nori=[(-38,8),(-42,18),(-40,48),(40,48),(42,18),(38,8)]
add(black,prism_xz(nori,16.2,18))
add(black,prism_xz(ellipse(-18,72,4.5,7),16.2,18))
add(black,prism_xz(ellipse(18,72,4.5,7),16.2,18))
# Simple smiling mouth.
mouth=[(-12,58),(-7,53),(0,50),(7,53),(12,58),(9,59),(0,55),(-9,59)]
add(black,prism_xz(mouth,16.2,18))

write_stl(OUT/'anime_onigiri_phone_stand_white.stl',white,'Anifinity onigiri phone stand white body')
write_stl(OUT/'anime_onigiri_phone_stand_black.stl',black,'Anifinity onigiri phone stand black accents')
write_stl(OUT/'anime_onigiri_phone_stand_combined_preview.stl',white+black,'Anifinity onigiri phone stand combined')
print('Created onigiri phone stand STLs')
