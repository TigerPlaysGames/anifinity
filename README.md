# Anifinity Creations

Anifinity Creations is an organized working repository for the shop brand, listing material, and original 3D-print product development. It consolidates the useful source and deliverables from the original projectless workspace without including downloaded reference media, dependency caches, or temporary inspection files.

> **Prototype before sale:** No product should be offered for sale from renders or mesh checks alone. Physically print the exact final files, confirm fit, strength, stability, surface quality, slicer settings, packaging dimensions, and real product photography first. Mockups must remain disclosed as digital mockups until replaced with photographs.

## Project index

| Area | Status | Canonical deliverable |
|---|---|---|
| `brand/` | Ready for internal use | Logo and Etsy banner |
| `shop/` | Draft launch material | Shop video and Etsy launch pack; verify fees, account requirements, claims, and rights before publishing |
| `products/cosplay-kunai/` | CAD and digital listing assets complete; physical prototype required | `models/final/cosplay_kunai_v3_one_piece.stl` |
| `products/onigiri-phone-stand/` | CAD, mesh validation, renders, and slicer fit complete; physical fit/stability test required | `models/black_core.stl`, `models/white_shell.stl`, and `models/assembly.step` |
| `products/cyber-shinobi/` | Concept/prototype only | No sale-ready final; models and concept renders are retained for development |
| `archive/` | Rejected historical work | Failed onigiri V1 only; never treat these files as final |

## Repository layout

- `brand/` — Anifinity identity assets.
- `shop/` — launch copy and shop video.
- `products/<product>/src/` — reproducible original CAD/render scripts.
- `products/<product>/models/` — printable and editable model deliverables.
- `products/<product>/renders/` — previews, concepts, and listing mockups.
- `products/<product>/docs/` — print, validation, and prototype notes.
- `archive/` — failed prototypes retained for traceability.

The kunai `models/historical/` directory preserves earlier and reference-proportion iterations. The exact fused V3 under `models/final/` is the current canonical kunai mesh. The cyber-shinobi files are design exploration, not a validated product.

## Reproducing CAD and renders

Use Python 3.12 or newer from the repository root:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Scripts write into their own product directories. Run them from the repository root, for example:

```powershell
python products/cosplay-kunai/src/generate_cosplay_kunai.py
python products/cosplay-kunai/src/fuse_kunai_v3_exact.py
python products/cosplay-kunai/src/render_kunai_v3_one_piece.py
python products/onigiri-phone-stand/src/build_model.py
python products/onigiri-phone-stand/src/render_listing_images.py
python products/cyber-shinobi/src/make_cyber_shinobi_insert.py
```

Rendering uses VTK and may require a working graphics/OpenGL environment. The listing-label script currently expects Arial at the standard Windows font paths. Product-specific print and validation details are in each product's documentation.

## Rights and publishing

Only original Anifinity-created assets are collected here. Downloaded third-party reference images and inspection media were intentionally excluded. Before commercial use, review the final product, naming, imagery, and listing copy for intellectual-property and marketplace compliance. Nothing in this repository indicates that an Etsy listing has been published or that any model has been sent to a printer.
