"""Static checks that a textured export will map correctly in Three.js / game engines."""
from __future__ import annotations

from pathlib import Path


def validate_textured_export(job_dir: Path, name: str = "model") -> list[str]:
    """Return a list of problems (empty list = export looks valid)."""
    job_dir = Path(job_dir)
    problems: list[str] = []
    obj, mtl = job_dir / f"{name}.obj", job_dir / f"{name}.mtl"
    if not obj.exists():
        return [f"{obj.name} is missing"]
    if not mtl.exists():
        problems.append(f"{mtl.name} is missing")

    lines = obj.read_text().splitlines()
    if not any(l.startswith("mtllib") and mtl.name in l for l in lines):
        problems.append("OBJ does not reference its MTL via mtllib")
    uvs = [l.split()[1:3] for l in lines if l.startswith("vt ")]
    if not uvs:
        problems.append("OBJ has no texture coordinates (vt)")
    else:
        vals = [float(x) for pair in uvs for x in pair]
        if min(vals) < -1e-4 or max(vals) > 1 + 1e-4:
            problems.append(f"UVs outside [0,1]: range {min(vals):.3f}..{max(vals):.3f}")
    faces = [l for l in lines if l.startswith("f ")]
    if not faces:
        problems.append("OBJ has no faces")
    elif "/" not in faces[0]:
        problems.append("faces do not index texture coordinates (expected v/vt)")

    if mtl.exists():
        maps = [l.split(maxsplit=1)[1].strip() for l in mtl.read_text().splitlines() if l.strip().startswith("map_Kd")]
        if not maps:
            problems.append("MTL has no map_Kd (diffuse texture)")
        for m in maps:
            if not (job_dir / m).exists():
                problems.append(f"texture file '{m}' referenced by MTL does not exist")
    return problems
