"""Bake a generated image into a UV atlas and write a textured OBJ + MTL + PNG (NumPy/PIL only)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from .depth import EXTENT


def _dilate(atlas: np.ndarray, filled: np.ndarray, iterations: int):
    """Bleed colors outward so bilinear filtering never samples empty texels at chart borders."""
    for _ in range(iterations):
        new, nf = atlas.copy(), filled.copy()
        for shift in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            src = np.roll(atlas, shift, (0, 1))
            src_f = np.roll(filled, shift, (0, 1))
            take = (~nf) & src_f
            new[take] = src[take]
            nf |= take
        atlas, filled = new, nf
    return atlas, filled


def bake_projected_texture(vertices, faces, uv, image: Image.Image, atlas_size: int = 1024,
                           extent: float = EXTENT, padding: int = 6) -> Image.Image:
    """Bake a front-view image (made from the depth map) into the UV atlas.

    Every atlas texel is mapped to its 3D point, then to a pixel of the front view (the same orthographic
    window used by depth.render_depth). LIMITATIONS: faces turned away from +Z sample a mirrored copy of the
    front image, and occlusion is ignored (a hidden front-facing face still gets the pixel in front of it).
    Winding must be consistent/outward (clean_mesh calls trimesh fix_normals for this).
    """
    img = np.asarray(image.convert("RGB"))
    H, W, _ = img.shape
    S = atlas_size
    v = np.asarray(vertices, dtype=np.float64)
    f = np.asarray(faces, dtype=np.int64)
    uv = np.asarray(uv, dtype=np.float64)
    tri = v[f]
    normals_z = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])[:, 2]

    atlas = np.zeros((S, S, 3), np.uint8)
    filled = np.zeros((S, S), bool)
    for fi in range(len(f)):
        a, b, c = f[fi]
        px = uv[[a, b, c], 0] * (S - 1)
        py = (1.0 - uv[[a, b, c], 1]) * (S - 1)
        x0, x1 = int(max(np.floor(px.min()), 0)), int(min(np.ceil(px.max()), S - 1))
        y0, y1 = int(max(np.floor(py.min()), 0)), int(min(np.ceil(py.max()), S - 1))
        den = (py[1] - py[2]) * (px[0] - px[2]) + (px[2] - px[1]) * (py[0] - py[2])
        if abs(den) < 1e-12:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        gx, gy = gx.ravel(), gy.ravel()
        w0 = ((py[1] - py[2]) * (gx - px[2]) + (px[2] - px[1]) * (gy - py[2])) / den
        w1 = ((py[2] - py[0]) * (gx - px[2]) + (px[0] - px[2]) * (gy - py[2])) / den
        w2 = 1.0 - w0 - w1
        inside = (w0 >= -1e-3) & (w1 >= -1e-3) & (w2 >= -1e-3)
        if not inside.any():
            continue
        w0, w1, w2, gx, gy = w0[inside], w1[inside], w2[inside], gx[inside], gy[inside]
        pos = w0[:, None] * v[a] + w1[:, None] * v[b] + w2[:, None] * v[c]
        x3d = pos[:, 0] if normals_z[fi] >= 0 else -pos[:, 0]
        cols = np.clip(((x3d + extent) / (2 * extent) * (W - 1)).round(), 0, W - 1).astype(int)
        rows = np.clip(((extent - pos[:, 1]) / (2 * extent) * (H - 1)).round(), 0, H - 1).astype(int)
        atlas[gy, gx] = img[rows, cols]
        filled[gy, gx] = True

    atlas, filled = _dilate(atlas, filled, padding)
    if (~filled).any():
        atlas[~filled] = atlas[filled].mean(axis=0) if filled.any() else 128
    return Image.fromarray(atlas)


def write_textured_obj(out_dir, vertices, faces, uv, image: Image.Image, name: str = "model") -> dict:
    """Write name.obj, name.mtl and name_texture.png. Requires one UV per vertex (xatlas output)."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    v = np.asarray(vertices, dtype=np.float64)
    f = np.asarray(faces, dtype=np.int64) + 1
    uv = np.asarray(uv, dtype=np.float64)
    if len(uv) != len(v):
        raise ValueError("expected one UV coordinate per vertex")

    tex, mtl, obj = f"{name}_texture.png", f"{name}.mtl", f"{name}.obj"
    image.convert("RGB").save(out / tex)
    (out / mtl).write_text(
        f"newmtl {name}_material\nKa 1.0 1.0 1.0\nKd 1.0 1.0 1.0\nKs 0.0 0.0 0.0\nd 1.0\nillum 1\nmap_Kd {tex}\n"
    )
    lines = [f"mtllib {mtl}"]
    lines += [f"v {x:.6f} {y:.6f} {z:.6f}" for x, y, z in v]
    lines += [f"vt {u:.6f} {w:.6f}" for u, w in uv]
    lines.append(f"usemtl {name}_material")
    lines += [f"f {a}/{a} {b}/{b} {c}/{c}" for a, b, c in f]
    (out / obj).write_text("\n".join(lines) + "\n")
    return {"obj": obj, "mtl": mtl, "texture": tex}
