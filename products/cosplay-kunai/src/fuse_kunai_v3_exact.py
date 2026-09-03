from pathlib import Path

import networkx as nx
import numpy as np
import trimesh


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "models" / "historical" / "cosplay_kunai_v3_reference_proportions.stl"
OUTPUT = ROOT / "models" / "final" / "cosplay_kunai_v3_one_piece.stl"


def cap_boundary_loops(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """Close polygonal tube ends without changing any existing surface."""
    edge_groups = trimesh.grouping.group_rows(mesh.edges_sorted, require_count=1)
    boundary_edges = mesh.edges_sorted[edge_groups]
    graph = nx.Graph()
    graph.add_edges_from(boundary_edges.tolist())
    loops = nx.cycle_basis(graph)

    vertices = mesh.vertices.tolist()
    faces = mesh.faces.tolist()
    for loop in loops:
        center = np.mean(mesh.vertices[np.asarray(loop)], axis=0)
        center_index = len(vertices)
        vertices.append(center.tolist())
        for i, a in enumerate(loop):
            b = loop[(i + 1) % len(loop)]
            faces.append([a, b, center_index])

    capped = trimesh.Trimesh(vertices=np.asarray(vertices), faces=np.asarray(faces), process=True)
    trimesh.repair.fix_normals(capped, multibody=True)
    if capped.volume < 0:
        capped.invert()
    return capped


source = trimesh.load_mesh(SOURCE, process=True)
parts = list(source.split(only_watertight=False))

prepared = []
for part in parts:
    part.process(validate=True)
    if not part.is_watertight:
        part = cap_boundary_loops(part)
    if part.volume < 0:
        part.invert()
    if not part.is_watertight:
        raise RuntimeError("A source component could not be closed for union")
    prepared.append(part)

fused = trimesh.boolean.union(prepared, engine="manifold", check_volume=True)
fused.process(validate=True)
trimesh.repair.fix_normals(fused, multibody=True)

if not fused.is_watertight or fused.body_count != 1:
    raise RuntimeError(
        f"Expected one watertight body; got watertight={fused.is_watertight}, bodies={fused.body_count}"
    )

fused.export(OUTPUT)
print({
    "source_components": len(parts),
    "output_body_count": fused.body_count,
    "watertight": fused.is_watertight,
    "winding_consistent": fused.is_winding_consistent,
    "dimensions_mm": np.round(fused.extents, 3).tolist(),
    "faces": int(len(fused.faces)),
    "output": str(OUTPUT),
})
