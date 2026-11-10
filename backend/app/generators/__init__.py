from .base import MeshGenerator

_CACHE: dict[str, MeshGenerator] = {}


def get_generator(name: str) -> MeshGenerator:
    """Lazy singleton so heavy models load once per process."""
    if name not in _CACHE:
        if name == "shape":
            from .shape import ShapEGenerator
            _CACHE[name] = ShapEGenerator()
        elif name == "triposr":
            from .triposr import TripoSRGenerator
            _CACHE[name] = TripoSRGenerator()
        else:
            raise ValueError(f"Unknown generator '{name}'")
    return _CACHE[name]
