"""Orchestrates the stages for one job.

Heavy dependencies (trimesh, xatlas, Stable Diffusion) are imported lazily so the API starts fast and the
mesh-only route works even if the texture stack is not installed.
"""
from __future__ import annotations

from pathlib import Path

from .generators import get_generator

TEXTURE_MODES = ("none", "flat", "controlnet")


def run_pipeline(prompt: str, job_dir: Path, generator: str = "shape", seed: int | None = None,
                 texture: str = "controlnet", progress=lambda stage: None) -> dict:
    if texture not in TEXTURE_MODES:
        raise ValueError(f"texture must be one of {TEXTURE_MODES}")
    from .mesh_processing import clean_mesh, load_mesh, mesh_stats, normalize_mesh

    job_dir = Path(job_dir)
    job_dir.mkdir(parents=True, exist_ok=True)

    progress("generating mesh")
    raw = get_generator(generator).generate(prompt, job_dir / "raw.obj", seed=seed)

    progress("cleaning mesh")
    mesh = normalize_mesh(clean_mesh(load_mesh(raw)))
    mesh.export(str(job_dir / "clean.obj"))
    stats = mesh_stats(mesh)

    if texture == "none":
        return {"obj": "clean.obj", "mtl": None, "stats": stats}

    from .depth import render_depth
    from .texture import get_texture_engine
    from .texturing import bake_projected_texture, write_textured_obj
    from .uv import uv_unwrap

    progress("unwrapping UVs (xatlas)")
    mesh = uv_unwrap(mesh)
    uv = mesh.visual.uv
    engine = get_texture_engine()

    if texture == "flat":
        progress("generating flat texture")
        atlas = engine.generate_flat(prompt, seed=seed)
    else:
        progress("rendering depth map")
        depth = render_depth(mesh.vertices, mesh.faces, resolution=256).resize((512, 512))
        depth.save(job_dir / "depth.png")
        progress("generating texture (ControlNet depth)")
        front = engine.generate_from_depth(prompt, depth, seed=seed)
        front.save(job_dir / "front_view.png")
        progress("baking texture into UV atlas")
        atlas = bake_projected_texture(mesh.vertices, mesh.faces, uv, front)

    progress("writing textured OBJ")
    files = write_textured_obj(job_dir, mesh.vertices, mesh.faces, uv, atlas, name="model")
    return {"obj": files["obj"], "mtl": files["mtl"], "stats": stats}
