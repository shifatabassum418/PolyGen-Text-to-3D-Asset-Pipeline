"""Central configuration. Values come from environment variables or an optional backend/.env file."""
import os
from dataclasses import dataclass, field
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]

try:  # python-dotenv ships with uvicorn[standard]; optional otherwise
    from dotenv import load_dotenv

    load_dotenv(BACKEND_DIR / ".env")
except ImportError:
    pass


def _path(env: str, default: str) -> Path:
    """Resolve relative paths against backend/ so results never depend on the current directory."""
    p = Path(os.getenv(env, default))
    return p if p.is_absolute() else BACKEND_DIR / p


@dataclass(frozen=True)
class Settings:
    output_dir: Path = field(default_factory=lambda: _path("POLYGEN_OUTPUT_DIR", "outputs"))
    triposr_dir: Path = field(default_factory=lambda: _path("POLYGEN_TRIPOSR_DIR", "third_party/TripoSR"))
    default_generator: str = os.getenv("POLYGEN_GENERATOR", "shape")
    sd_model: str = os.getenv("POLYGEN_SD_MODEL", "stable-diffusion-v1-5/stable-diffusion-v1-5")
    controlnet_model: str = os.getenv("POLYGEN_CONTROLNET", "lllyasviel/sd-controlnet-depth")
    cors_origins: tuple = ("http://localhost:5173", "http://127.0.0.1:5173")


settings = Settings()


def get_device() -> str:
    import torch

    return "cuda" if torch.cuda.is_available() else "cpu"
