"""Route A - Shap-E: direct TEXT -> 3D mesh (no intermediate image)."""
from pathlib import Path

import numpy as np
import torch

from ..config import get_device
from .base import MeshGenerator


class ShapEGenerator(MeshGenerator):
    name = "shape"

    def __init__(self, guidance_scale: float = 15.0, steps: int = 64):
        from diffusers import ShapEPipeline

        self.device = get_device()
        dtype = torch.float16 if self.device == "cuda" else torch.float32
        self.pipe = ShapEPipeline.from_pretrained("openai/shap-e", torch_dtype=dtype).to(self.device)
        self.guidance_scale = guidance_scale
        self.steps = steps

    @torch.inference_mode()
    def generate(self, prompt: str, out_path: Path, seed: int | None = None) -> Path:
        import trimesh

        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        gen = torch.Generator(device=self.device).manual_seed(seed) if seed is not None else None
        result = self.pipe(
            prompt,
            guidance_scale=self.guidance_scale,
            num_inference_steps=self.steps,
            frame_size=256,
            output_type="mesh",
            generator=gen,
        )
        decoded = result.images[0]  # MeshDecoderOutput: verts, faces, vertex_channels
        verts = decoded.verts.detach().float().cpu().numpy()
        faces = decoded.faces.detach().cpu().numpy()
        colors = None
        channels = getattr(decoded, "vertex_channels", None)
        if channels and all(k in channels for k in "RGB"):
            rgb = np.stack([channels[k].detach().float().cpu().numpy() for k in "RGB"], axis=1)
            colors = (np.clip(rgb, 0, 1) * 255).astype(np.uint8)

        mesh = trimesh.Trimesh(vertices=verts, faces=faces, vertex_colors=colors, process=False)
        # Shap-E meshes are Z-up; rotate to Y-up for Three.js and game engines.
        mesh.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0]))
        mesh.export(str(out_path))
        return out_path
