"""Mesh cleanup, normalization and statistics (trimesh)."""
from __future__ import annotations

import numpy as np
import trimesh


def load_mesh(path) -> trimesh.Trimesh:
    mesh = trimesh.load(str(path), force="mesh", process=False)
    if not isinstance(mesh, trimesh.Trimesh) or len(mesh.faces) == 0:
        raise ValueError(f"{path} did not contain a triangle mesh")
    return mesh


def clean_mesh(mesh: trimesh.Trimesh, min_component_ratio: float = 0.02) -> trimesh.Trimesh:
    """Merge duplicate vertices, drop degenerate/duplicate faces and tiny floating debris."""
    m = mesh.copy()
    m.merge_vertices()
    m.update_faces(m.nondegenerate_faces())
    m.update_faces(m.unique_faces())
    m.remove_unreferenced_vertices()
    parts = m.split(only_watertight=False)
    if len(parts) > 1:
        biggest = max(len(p.faces) for p in parts)
        keep = [p for p in parts if len(p.faces) >= biggest * min_component_ratio]
        m = trimesh.util.concatenate(keep)
    try:  # consistent, outward-facing winding (needed later to tell front faces from back faces)
        trimesh.repair.fix_normals(m)
    except Exception:
        pass
    return m


def normalize_mesh(mesh: trimesh.Trimesh, target_extent: float = 1.0) -> trimesh.Trimesh:
    """Center at the origin and scale so the largest dimension equals `target_extent`."""
    m = mesh.copy()
    lo, hi = m.bounds
    m.apply_translation(-(lo + hi) / 2.0)
    size = float(np.max(hi - lo))
    if size > 0:
        m.apply_scale(target_extent / size)
    return m


def mesh_stats(mesh: trimesh.Trimesh) -> dict:
    ext = mesh.extents
    convexity = None
    try:
        if mesh.is_watertight and mesh.volume > 0:
            convexity = float(mesh.volume / mesh.convex_hull.volume)
    except Exception:
        pass
    return {
        "vertices": int(len(mesh.vertices)),
        "faces": int(len(mesh.faces)),
        "watertight": bool(mesh.is_watertight),
        "components": int(len(mesh.split(only_watertight=False))),
        "extents": [round(float(e), 4) for e in ext],
        "aspect_ratio": round(float(ext.max() / max(ext.min(), 1e-9)), 3),
        "convexity": None if convexity is None else round(convexity, 3),
    }
