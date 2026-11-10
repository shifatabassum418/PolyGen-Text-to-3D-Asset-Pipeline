"""UV unwrapping with xatlas.

trimesh does NOT provide a UV unwrapper; it is used only for mesh IO, cleanup and statistics.
"""
from __future__ import annotations

import numpy as np


def uv_unwrap(mesh):
    """Return a new trimesh with a seam-minimizing UV atlas in `visual.uv` (values in [0, 1]).

    xatlas splits vertices along chart seams, so the output has the same surface but possibly more
    vertices, and every vertex has exactly one UV coordinate.
    """
    import trimesh
    import xatlas

    vmapping, indices, uvs = xatlas.parametrize(
        np.ascontiguousarray(mesh.vertices, dtype=np.float32),
        np.ascontiguousarray(mesh.faces, dtype=np.uint32),
    )
    uvs = np.asarray(uvs, dtype=np.float64)
    top = uvs.max(axis=0)
    if (top > 1.0 + 1e-6).any():  # defensive: some xatlas builds return pixel units
        uvs = uvs / np.maximum(top, 1.0)
    out = trimesh.Trimesh(vertices=mesh.vertices[vmapping], faces=indices.astype(np.int64), process=False)
    out.visual = trimesh.visual.TextureVisuals(uv=uvs)
    return out
