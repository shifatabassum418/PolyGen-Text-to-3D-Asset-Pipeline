"""Route B - TripoSR: IMAGE -> 3D mesh.

TripoSR needs an input image, so this route first makes one from the prompt with SD-Turbo
(text -> image), removes the background, then runs TripoSR (image -> mesh). The Shap-E route does not
use any of this.

Status: written against the public TripoSR API but NOT verified end-to-end in this project's tests.
"""
import sys
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from ..config import get_device, settings
from .base import MeshGenerator

PROMPT_SUFFIX = ", single object, centered, plain white background, product render, neutral lighting"


class TripoSRGenerator(MeshGenerator):
    name = "triposr"

    def __init__(self, mc_resolution: int = 256):
        tsr_dir = Path(settings.triposr_dir)
        if not tsr_dir.exists():
            raise RuntimeError(f"TripoSR not found at {tsr_dir}. Run: bash scripts/setup_triposr.sh")
        sys.path.insert(0, str(tsr_dir))
        import rembg
        from diffusers import AutoPipelineForText2Image
        from tsr.system import TSR

        self.device = get_device()
        cuda = self.device == "cuda"
        self.t2i = AutoPipelineForText2Image.from_pretrained(
            "stabilityai/sd-turbo",
            torch_dtype=torch.float16 if cuda else torch.float32,
            variant="fp16" if cuda else None,
        ).to(self.device)
        self.tsr = TSR.from_pretrained("stabilityai/TripoSR", config_name="config.yaml", weight_name="model.ckpt")
        self.tsr.renderer.set_chunk_size(8192)
        self.tsr.to(self.device)
        self.rembg_session = rembg.new_session()  # created once, reused for every request
        self.mc_resolution = mc_resolution

    def _text_to_image(self, prompt: str, seed: int | None) -> Image.Image:
        gen = torch.Generator(device=self.device).manual_seed(seed) if seed is not None else None
        return self.t2i(prompt + PROMPT_SUFFIX, num_inference_steps=2, guidance_scale=0.0, generator=gen).images[0]

    def _prepare(self, image: Image.Image) -> Image.Image:
        from tsr.utils import remove_background, resize_foreground

        image = resize_foreground(remove_background(image, self.rembg_session), 0.85)
        arr = np.array(image).astype(np.float32) / 255.0
        arr = arr[:, :, :3] * arr[:, :, 3:4] + (1 - arr[:, :, 3:4]) * 0.5  # grey background, as TripoSR expects
        return Image.fromarray((arr * 255).astype(np.uint8))

    @torch.inference_mode()
    def generate(self, prompt: str, out_path: Path, seed: int | None = None) -> Path:
        import trimesh

        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        reference = self._text_to_image(prompt, seed)
        reference.save(out_path.with_name("reference.png"))
        codes = self.tsr([self._prepare(reference)], device=self.device)
        mesh = self.tsr.extract_mesh(codes, True, resolution=self.mc_resolution)[0]
        # Same re-orientation TripoSR's own viewer applies (-90 deg about X, then +90 deg about Y).
        mesh.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0]))
        mesh.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
        mesh.export(str(out_path))
        return out_path
