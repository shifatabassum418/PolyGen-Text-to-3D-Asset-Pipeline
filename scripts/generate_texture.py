"""CLI: python scripts/generate_texture.py "rusted iron sword" --out backend/outputs/cli/flat.png"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.texture import get_texture_engine  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt")
    ap.add_argument("--out", default="backend/outputs/cli/flat.png")
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    get_texture_engine().generate_flat(args.prompt, seed=args.seed).save(out)
    print(f"saved {out}")


if __name__ == "__main__":
    main()
