"""Verify the GPU-accelerated environment before loading any models."""
import importlib
import sys

import torch


def main() -> int:
    print(f"python  : {sys.version.split()[0]}")
    print(f"torch   : {torch.__version__}")
    ok = torch.cuda.is_available()
    print(f"cuda    : {ok}")
    if ok:
        p = torch.cuda.get_device_properties(0)
        print(f"gpu     : {p.name}  ({p.total_memory / 1e9:.1f} GB VRAM)")
        if p.total_memory / 1e9 < 8:
            print("warning : <8 GB VRAM. Use fp16 and run one model at a time.")
    else:
        print("warning : no CUDA GPU. Generation will be very slow on CPU.")
    for mod, required in [("diffusers", True), ("transformers", True), ("trimesh", True), ("xatlas", True),
                          ("fastapi", True), ("rembg", False)]:
        try:
            m = importlib.import_module(mod)
            print(f"{mod:<12}: {getattr(m, '__version__', 'ok')}")
        except ImportError:
            print(f"{mod:<12}: MISSING" + ("" if required else " (only needed for the TripoSR route)"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
