"""Tiny NumPy-only mesh helpers so core logic can be tested without trimesh/xatlas/GPU."""
import importlib.util

import numpy as np


def has(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


def make_box(extents=(1.0, 1.0, 1.0)):
    """Closed box with outward-facing (CCW) triangles. Returns (vertices, faces)."""
    half = np.array(extents, dtype=float) / 2
    v = np.array([[x, y, z] for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)], dtype=float) * half
    quads = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    faces = []
    for a, b, c, d in quads:
        faces += [(a, b, c), (a, c, d)]
    faces = np.array(faces)
    tri = v[faces]
    normals = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    flip = (normals * tri.mean(axis=1)).sum(axis=1) < 0
    faces[flip] = faces[flip][:, [0, 2, 1]]
    return v, faces


def trivial_unwrap(vertices, faces):
    """One chart per triangle laid out on a grid (stand-in for xatlas). Returns (vertices, faces, uv)."""
    f_count = len(faces)
    new_v = vertices[faces].reshape(-1, 3)
    new_f = np.arange(3 * f_count).reshape(-1, 3)
    n = int(np.ceil(np.sqrt(f_count)))
    s = 1.0 / n
    uv = np.zeros((3 * f_count, 2))
    for i in range(f_count):
        cx, cy = (i % n) * s, (i // n) * s
        uv[3 * i:3 * i + 3] = [(cx + 0.1 * s, cy + 0.1 * s), (cx + 0.9 * s, cy + 0.1 * s), (cx + 0.1 * s, cy + 0.9 * s)]
    return new_v, new_f, uv
