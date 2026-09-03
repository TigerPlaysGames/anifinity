from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import vtk


ROOT = Path(__file__).resolve().parents[1]
STL = ROOT / "models" / "historical" / "cosplay_kunai_single_piece.stl"
OUT = ROOT / "renders" / "previews" / "cosplay_kunai_single_piece_preview.png"

reader = vtk.vtkSTLReader()
reader.SetFileName(str(STL))

normals = vtk.vtkPolyDataNormals()
normals.SetInputConnection(reader.GetOutputPort())
normals.SplittingOn()
normals.SetFeatureAngle(35)

mapper = vtk.vtkPolyDataMapper()
mapper.SetInputConnection(normals.GetOutputPort())

actor = vtk.vtkActor()
actor.SetMapper(mapper)
actor.GetProperty().SetColor(0.075, 0.08, 0.09)
actor.GetProperty().SetRoughness(0.75)
actor.GetProperty().SetInterpolationToPBR()

renderer = vtk.vtkRenderer()
renderer.SetBackground(0.035, 0.04, 0.055)
renderer.SetBackground2(0.18, 0.19, 0.22)
renderer.GradientBackgroundOn()
renderer.AddActor(actor)

for position, intensity in [((-180, -220, 250), 1.0), ((220, -80, 120), 0.55), ((0, 220, 180), 0.65)]:
    light = vtk.vtkLight()
    light.SetPosition(*position)
    light.SetFocalPoint(0, 0, 0)
    light.SetIntensity(intensity)
    renderer.AddLight(light)

camera = renderer.GetActiveCamera()
camera.SetPosition(0, -430, 330)
camera.SetFocalPoint(0, 0, 0)
camera.SetViewUp(0, 0, 1)

window = vtk.vtkRenderWindow()
window.SetOffScreenRendering(1)
window.SetSize(1600, 900)
window.SetMultiSamples(8)
window.AddRenderer(renderer)
renderer.ResetCamera()
renderer.ResetCameraClippingRange()
window.Render()

capture = vtk.vtkWindowToImageFilter()
capture.SetInput(window)
capture.ReadFrontBufferOff()
capture.Update()

writer = vtk.vtkPNGWriter()
writer.SetFileName(str(OUT))
writer.SetInputConnection(capture.GetOutputPort())
writer.Write()

image = Image.open(OUT).convert("RGB")
draw = ImageDraw.Draw(image)
try:
    title = ImageFont.truetype("arialbd.ttf", 46)
    body = ImageFont.truetype("arial.ttf", 29)
except OSError:
    title = body = ImageFont.load_default()
draw.rounded_rectangle((32, 748, 1568, 868), radius=22, fill=(12, 13, 16))
draw.text((60, 766), "ONE-PIECE COSPLAY KUNAI — EXACT CAD", font=title, fill="white")
draw.text((60, 823), "Round grip + torus ring • one fused solid • 280 × 45 × 19 mm", font=body, fill=(205, 212, 222))
image.save(OUT)
print(OUT)
