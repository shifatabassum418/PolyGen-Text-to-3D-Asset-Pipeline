"""Orthographic depth rendering with a NumPy z-buffer (no GL context, GPU, trimesh or rtree needed)."""
from __future__ import annotations

import numpy as np
from PIL import Image

EXTENT = 0.6  # half-width of the view window; normalized meshes fit in [-0.5, 0.5]


def rotate_y(vertices: np.ndarray, degrees: float) -> np.ndarray:
    t = np.radians(degrees)
    c, s = np.cos(t), np.sin(t)
    x, y, z = vertices[:, 0], vertices[:, 1], vertices[:, 2]
    return np.column_stack([x * c + z * s, y, -x * s + z * c])


def render_depth(vertices, faces, azimuth_deg: float = 0.0, resolution: int = 256, extent: float = EXTENT) -> Image.Image:
    """Depth image in ControlNet convention: near = bright, far = dark, background = black.

    The camera sits on +Z looking toward -Z (the mesh front). Depth is scaled by the mesh's full Z range
    (not just the visible part) so flat-fronted objects still get a meaningful value.
    """
    v = rotate_y(np.asarray(vertices, dtype=np.float64), -azimuth_deg)
    f = np.asarray(faces, dtype=np.int64)
    R = resolution
    px = (v[:, 0] + extent) / (2 * extent) * (R - 1)
    py = (extent - v[:, 1]) / (2 * extent) * (R - 1)
    z = v[:, 2]
    zmin, zmax = float(z.min()), float(z.max())
    span = max(zmax - zmin, 1e-6)

    zbuf = np.full((R, R), -np.inf)
    for a, b, c in f:
        xs, ys = px[[a, b, c]], py[[a, b, c]]
        x0, x1 = max(int(np.floor(xs.min())), 0), min(int(np.ceil(xs.max())), R - 1)
        y0, y1 = max(int(np.floor(ys.min())), 0), min(int(np.ceil(ys.max())), R - 1)
        if x0 > x1 or y0 > y1:
            continue
        den = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
        if abs(den) < 1e-12:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        w0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / den
        w1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / den
        w2 = 1.0 - w0 - w1
        inside = (w0 >= -1e-3) & (w1 >= -1e-3) & (w2 >= -1e-3)
        if not inside.any():
            continue
        zz = w0 * z[a] + w1 * z[b] + w2 * z[c]
        region = zbuf[y0:y1 + 1, x0:x1 + 1]
        update = inside & (zz > region)
        region[update] = zz[update]

    hit = np.isfinite(zbuf)
    img = np.zeros((R, R), dtype=np.float32)
    img[hit] = 0.15 + 0.85 * np.clip((zbuf[hit] - zmin) / span, 0, 1)
    return Image.fromarray((img * 255).astype(np.uint8)).convert("RGB")
