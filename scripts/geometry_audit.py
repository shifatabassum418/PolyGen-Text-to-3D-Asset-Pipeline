"""Mid-project Geometry Audit.

Generates meshes for recognizable object prompts and reports objective shape metrics plus a
multi-view depth contact sheet for a human to confirm each result is a structure, not a blob.

    python scripts/geometry_audit.py --generator shape   # needs a GPU and downloaded models
"""
import argparse
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.depth import render_depth  # noqa: E402
from app.generators import get_generator  # noqa: E402
from app.mesh_processing import clean_mesh, load_mesh, mesh_stats, normalize_mesh  # noqa: E402

# Each prompt carries a cheap, objective sanity check on its shape.
PROMPTS = [
    ("a medieval broadsword", "elongated", lambda s: s["aspect_ratio"] >= 2.5),
    ("a wooden chair", "concave (legs, back)", lambda s: s["convexity"] is None or s["convexity"] <= 0.75),
    ("a table lamp", "taller than wide", lambda s: s["aspect_ratio"] >= 1.3),
    ("a clay pot", "single connected part", lambda s: s["components"] == 1),
    ("a wooden barrel", "single connected part", lambda s: s["components"] == 1),
]


def contact_sheet(mesh, size=256) -> Image.Image:
    sheet = Image.new("RGB", (size * 4, size))
    for i, az in enumerate((0, 90, 180, 270)):
        sheet.paste(render_depth(mesh.vertices, mesh.faces, azimuth_deg=az, resolution=size), (i * size, 0))
    return sheet


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--generator", default="shape", choices=["shape", "triposr"])
    ap.add_argument("--out", default="backend/outputs/audit")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    gen = get_generator(args.generator)

    rows = ["| Prompt | Check | Faces | Parts | Aspect | Convexity | Auto-check |", "|---|---|---|---|---|---|---|"]
    for prompt, check_name, check in PROMPTS:
        slug = prompt.replace(" ", "_")
        mesh = normalize_mesh(clean_mesh(load_mesh(gen.generate(prompt, out / f"{slug}.obj", seed=args.seed))))
        s = mesh_stats(mesh)
        contact_sheet(mesh).save(out / f"{slug}_views.png")
        rows.append(f"| {prompt} | {check_name} | {s['faces']} | {s['components']} | {s['aspect_ratio']} | {s['convexity']} | {'PASS' if check(s) else 'FAIL'} |")
        print(rows[-1])

    report = out / "report.md"
    report.write_text(
        f"# Geometry audit ({args.generator})\n\n" + "\n".join(rows)
        + "\n\nOpen each `*_views.png` (front/right/back/left depth views) and confirm the object is recognizable.\n"
    )
    print(f"report -> {report}")


if __name__ == "__main__":
    main()
