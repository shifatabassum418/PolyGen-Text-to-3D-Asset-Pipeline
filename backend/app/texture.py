"""Stable Diffusion texture generation."""
from __future__ import annotations

import torch
from PIL import Image

from .config import get_device, settings

NEGATIVE = "shadows, highlights, text, watermark, logo, blurry, low quality, frame, border"


class TextureEngine:
    """Lazy-loaded SD 1.5 pipeline that makes flat, evenly lit albedo textures."""

    def __init__(self):
        self.device = get_device()
        self.dtype = torch.float16 if self.device == "cuda" else torch.float32
        self._sd = None
        self._cn = None

    @property
    def sd(self):
        if self._sd is None:
            from diffusers import StableDiffusionPipeline

            self._sd = StableDiffusionPipeline.from_pretrained(
                settings.sd_model, torch_dtype=self.dtype, safety_checker=None, requires_safety_checker=False
            ).to(self.device)
        return self._sd

    @property
    def controlnet_pipe(self):
        """ControlNet-depth pipeline that reuses the SD weights already in memory."""
        if self._cn is None:
            from diffusers import ControlNetModel, StableDiffusionControlNetPipeline, UniPCMultistepScheduler

            sd = self.sd
            controlnet = ControlNetModel.from_pretrained(settings.controlnet_model, torch_dtype=self.dtype)
            self._cn = StableDiffusionControlNetPipeline(
                vae=sd.vae, text_encoder=sd.text_encoder, tokenizer=sd.tokenizer, unet=sd.unet,
                scheduler=UniPCMultistepScheduler.from_config(sd.scheduler.config),
                safety_checker=None, feature_extractor=None, controlnet=controlnet, requires_safety_checker=False,
            ).to(self.device)
        return self._cn

    @torch.inference_mode()
    def generate_flat(self, prompt: str, size: int = 512, seed: int | None = None, steps: int = 25) -> Image.Image:
        """A flat surface texture (material look only, no object silhouette)."""
        gen = torch.Generator(device=self.device).manual_seed(seed) if seed is not None else None
        text = f"seamless tileable texture of the surface material of {prompt}, top-down, flat even lighting, albedo map, high detail"
        return self.sd(text, negative_prompt=NEGATIVE, num_inference_steps=steps, height=size, width=size, generator=gen).images[0]


    @torch.inference_mode()
    def generate_from_depth(self, prompt: str, depth_image: Image.Image, size: int = 512, seed: int | None = None,
                            steps: int = 25, conditioning_scale: float = 1.0) -> Image.Image:
        """Object-shaped albedo image whose silhouette and relief follow the mesh depth map."""
        gen = torch.Generator(device=self.device).manual_seed(seed) if seed is not None else None
        text = f"{prompt}, albedo texture, flat even lighting, no cast shadows, no specular highlights, high detail"
        return self.controlnet_pipe(
            text, image=depth_image.resize((size, size)), negative_prompt=NEGATIVE,
            num_inference_steps=steps, controlnet_conditioning_scale=conditioning_scale, generator=gen,
        ).images[0]


_engine: TextureEngine | None = None


def get_texture_engine() -> TextureEngine:
    global _engine
    if _engine is None:
        _engine = TextureEngine()
    return _engine
