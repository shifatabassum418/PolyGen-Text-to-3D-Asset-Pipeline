"""Generate a raw mesh from a prompt, one route at a time.

    python scripts/generate_mesh.py "a wooden chair" --generator shape      # Route A: Shap-E, text -> 3D
    python scripts/generate_mesh.py "a wooden chair" --generator triposr    # Route B: SD-Turbo image -> TripoSR
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.generators import get_generator  # noqa: E402
from app.mesh_processing import load_mesh, mesh_stats  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt")
    ap.add_argument("--generator", default="shape", choices=["shape", "triposr"])
    ap.add_argument("--out", default="backend/outputs/cli/raw.obj")
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args()

    t0 = time.time()
    gen = get_generator(args.generator)
    print(f"model loaded in {time.time() - t0:.1f}s")
    t0 = time.time()
    path = gen.generate(args.prompt, Path(args.out), seed=args.seed)
    print(f"mesh generated in {time.time() - t0:.1f}s -> {path}")
    print(mesh_stats(load_mesh(path)))


if __name__ == "__main__":
    main()
