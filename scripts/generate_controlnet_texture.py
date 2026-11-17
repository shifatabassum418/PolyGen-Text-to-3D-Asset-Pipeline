"""Generate and bake a depth-guided ControlNet texture onto a UV-unwrapped OBJ.

Example:
python scripts/generate_controlnet_texture.py outputs/week2/chair_uv.obj `
    --prompt "A worn wooden tavern chair, aged oak wood, natural grain" `
    --out backend/outputs/week2 --name chair
"""

import argparse
import sys
from pathlib import Path

import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.depth import render_depth
from app.texture import get_texture_engine
from app.texturing import bake_projected_texture, write_textured_obj


def main():
    parser = argparse.ArgumentParser(description="Generate a ControlNet-textured OBJ.")
    parser.add_argument("mesh", help="Input UV-unwrapped OBJ file")
    parser.add_argument("--prompt", required=True, help="Surface appearance prompt")
    parser.add_argument("--out", default="backend/outputs/controlnet")
    parser.add_argument("--name", default="textured_model")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--size", type=int, default=512)
    parser.add_argument("--atlas-size", type=int, default=1024)
    parser.add_argument("--azimuth", type=float, default=0.0)
    parser.add_argument("--conditioning-scale", type=float, default=0.8)
    args = parser.parse_args()

    mesh_path = Path(args.mesh)
    if not mesh_path.is_file():
        parser.error(f"Input mesh does not exist: {mesh_path}")

    mesh = trimesh.load(mesh_path, force="mesh", process=False)
    if not isinstance(mesh, trimesh.Trimesh) or len(mesh.faces) == 0:
        parser.error("Input file did not contain a valid triangle mesh.")

    uv = getattr(mesh.visual, "uv", None)
    if uv is None or len(uv) != len(mesh.vertices):
        parser.error("Input mesh must have one UV coordinate per vertex.")

    print(f"Loaded mesh: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")
    print("Rendering depth map...")
    depth_image = render_depth(
        mesh.vertices,
        mesh.faces,
        azimuth_deg=args.azimuth,
        resolution=args.size,
    )

    print("Generating ControlNet texture...")
    engine = get_texture_engine()
    if engine.controlnet_pipe is not None:
        engine.controlnet_pipe.enable_attention_slicing()

    texture = engine.generate_from_depth(
        prompt=args.prompt,
        depth_image=depth_image,
        size=args.size,
        seed=args.seed,
        steps=args.steps,
        conditioning_scale=args.conditioning_scale,
    )

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    depth_path = out_dir / f"{args.name}_depth.png"
    texture_path = out_dir / f"{args.name}_controlnet.png"
    depth_image.save(depth_path)
    texture.save(texture_path)

    print("Baking texture into UV atlas...")
    atlas = bake_projected_texture(
        mesh.vertices,
        mesh.faces,
        uv,
        texture,
        atlas_size=args.atlas_size,
    )

    print("Exporting textured OBJ, MTL, and atlas...")
    result = write_textured_obj(
        out_dir=out_dir,
        vertices=mesh.vertices,
        faces=mesh.faces,
        uv=uv,
        image=atlas,
        name=args.name,
    )

    print("Export complete:")
    print(f"  Depth map: {depth_path}")
    print(f"  Generated texture: {texture_path}")
    for key, value in result.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
