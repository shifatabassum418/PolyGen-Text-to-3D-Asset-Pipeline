"""UV-unwrap an OBJ with xatlas and write a UV layout preview PNG.

    python scripts/uv_unwrap.py in.obj out.obj
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.mesh_processing import clean_mesh, load_mesh, normalize_mesh  # noqa: E402
from app.uv import uv_unwrap  # noqa: E402


def uv_preview(mesh, size=1024) -> Image.Image:
    img = Image.new("RGB", (size, size), "white")
    d = ImageDraw.Draw(img)
    uv = mesh.visual.uv * (size - 1)
    for f in mesh.faces:
        pts = [(float(uv[i][0]), float(size - 1 - uv[i][1])) for i in f]
        d.polygon(pts, outline=(40, 40, 40))
    return img


def main():
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    mesh = uv_unwrap(normalize_mesh(clean_mesh(load_mesh(src))))
    mesh.export(str(dst))
    uv_preview(mesh).save(dst.with_suffix(".uv.png"))
    print(f"{len(mesh.faces)} faces, {len(mesh.vertices)} verts, uv range "
          f"[{np.min(mesh.visual.uv):.2f}, {np.max(mesh.visual.uv):.2f}] -> {dst}")


if __name__ == "__main__":
    main()
