from abc import ABC, abstractmethod
from pathlib import Path


class MeshGenerator(ABC):
    """Turns a text prompt into a raw mesh file on disk."""

    name: str = "base"

    @abstractmethod
    def generate(self, prompt: str, out_path: Path, seed: int | None = None) -> Path:
        """Write a mesh to `out_path` (.obj) and return the path."""
