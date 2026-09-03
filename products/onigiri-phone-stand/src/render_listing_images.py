from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

from PIL import Image, ImageDraw, ImageFont
import vtk

PRINTS = ROOT / "models"
IMAGES = ROOT / "renders"
IMAGES.mkdir(parents=True, exist_ok=True)

BLACK_STL = PRINTS / "black_core.stl"
WHITE_STL = PRINTS / "white_shell.stl"


def stl_actor(path, color, translation=(0, 0, 0)):
    reader = vtk.vtkSTLReader(); reader.SetFileName(str(path)); reader.Update()
    normals = vtk.vtkPolyDataNormals(); normals.SetInputConnection(reader.GetOutputPort())
    # STL facets around cutouts can create radial smoothing artifacts. Preserve
    # crisp manufactured edges with split normals instead of smoothing across
    # unrelated triangles.
    normals.ComputePointNormalsOn(); normals.SplittingOn(); normals.SetFeatureAngle(32); normals.ConsistencyOn(); normals.Update()
    mapper = vtk.vtkPolyDataMapper(); mapper.SetInputConnection(normals.GetOutputPort())
    actor = vtk.vtkActor(); actor.SetMapper(mapper); actor.SetPosition(*translation)
    actor.GetProperty().SetColor(*color); actor.GetProperty().SetRoughness(0.82)
    actor.GetProperty().SetMetallic(0.0); actor.GetProperty().SetInterpolationToPhong()
    return actor


def cube_actor(center, size, color, rotate_x=0):
    src = vtk.vtkCubeSource(); src.SetXLength(size[0]); src.SetYLength(size[1]); src.SetZLength(size[2]); src.Update()
    mapper = vtk.vtkPolyDataMapper(); mapper.SetInputConnection(src.GetOutputPort())
    actor = vtk.vtkActor(); actor.SetMapper(mapper); actor.SetPosition(*center); actor.RotateX(rotate_x)
    actor.GetProperty().SetColor(*color); actor.GetProperty().SetInterpolationToPBR(); actor.GetProperty().SetRoughness(0.35)
    return actor


def add_floor(renderer):
    floor = cube_actor((0, 0, -4), (360, 320, 8), (0.11, 0.115, 0.125))
    floor.GetProperty().SetRoughness(0.92); renderer.AddActor(floor)


def label(path, title, subtitle):
    img = Image.open(path).convert("RGB")
    draw = ImageDraw.Draw(img)
    try:
        font1 = ImageFont.truetype("arialbd.ttf", 44)
        font2 = ImageFont.truetype("arial.ttf", 28)
    except OSError:
        font1 = font2 = ImageFont.load_default()
    pad = 34
    box_h = 122
    draw.rounded_rectangle((pad, img.height-box_h-pad, img.width-pad, img.height-pad), radius=22, fill=(12,13,16,225))
    draw.text((pad+28, img.height-box_h-pad+20), title, font=font1, fill=(255,255,255))
    draw.text((pad+28, img.height-box_h-pad+72), subtitle, font=font2, fill=(205,210,220))
    img.save(path, quality=95)


def render(name, camera, focal, with_phone=False, exploded=False, straight=False):
    renderer = vtk.vtkRenderer(); renderer.SetBackground(0.035, 0.04, 0.055)
    renderer.SetBackground2(0.16, 0.17, 0.20); renderer.GradientBackgroundOn(); renderer.UseImageBasedLightingOff()
    window = vtk.vtkRenderWindow(); window.SetOffScreenRendering(1); window.SetSize(1600,1600); window.AddRenderer(renderer)
    window.SetMultiSamples(8)

    renderer.AddActor(stl_actor(BLACK_STL, (0.025,0.028,0.032)))
    white_offset = (0,-30,0) if exploded else (0,0,0)
    renderer.AddActor(stl_actor(WHITE_STL, (0.94,0.945,0.92), white_offset))
    add_floor(renderer)

    if with_phone:
        # Generic phone proxy at the verified 70-degree support angle.
        phone = cube_actor((0,-7,92), (76,8,154), (0.055,0.06,0.07), rotate_x=-20)
        renderer.AddActor(phone)

    key = vtk.vtkLight(); key.SetPosition(-180,-220,300); key.SetFocalPoint(0,0,60); key.SetIntensity(1.05)
    fill = vtk.vtkLight(); fill.SetPosition(220,-80,150); fill.SetFocalPoint(0,0,60); fill.SetIntensity(0.55)
    rim = vtk.vtkLight(); rim.SetPosition(0,220,220); rim.SetFocalPoint(0,20,70); rim.SetIntensity(0.75)
    renderer.AddLight(key); renderer.AddLight(fill); renderer.AddLight(rim)

    cam = renderer.GetActiveCamera(); cam.SetPosition(*camera); cam.SetFocalPoint(*focal); cam.SetViewUp(0,0,1)
    if straight: cam.SetParallelProjection(True); cam.SetParallelScale(93)
    else: cam.SetViewAngle(35)
    renderer.ResetCameraClippingRange(); window.Render()

    w2i = vtk.vtkWindowToImageFilter(); w2i.SetInput(window); w2i.SetScale(1); w2i.ReadFrontBufferOff(); w2i.Update()
    writer = vtk.vtkPNGWriter(); out = IMAGES / name; writer.SetFileName(str(out)); writer.SetInputConnection(w2i.GetOutputPort()); writer.Write()
    return out


hero = render("01_hero.png", (225,-275,185), (0,5,62))
label(hero, "ONIGIRI PHONE STAND — EXACT CAD", "Two-part snap-fit assembly • CAD render")

function = render("02_phone_angle.png", (205,-265,150), (0,0,62), with_phone=True)
label(function, "70° PHONE SUPPORT", "23 mm shelf • 18 mm charging opening • CAD render")

exploded = render("03_exploded.png", (230,-300,190), (0,-4,62), exploded=True)
label(exploded, "TWO-PART SNAP-FIT DESIGN", "Black structural core + white rice shell • CAD render")

front = render("04_front.png", (0,-360,72), (0,8,63), straight=True)
label(front, "CONSISTENT FRONT VIEW", "132 × 96 mm base • 125 mm overall height • CAD render")

print([str(hero), str(function), str(exploded), str(front)])
