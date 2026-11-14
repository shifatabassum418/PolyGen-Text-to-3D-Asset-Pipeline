# PolyGen — Week 2 Progress

## Milestone: UV Unwrapping

**Status:** Completed and locally verified

The Week 1 generated chair mesh was successfully processed using the project's existing xatlas UV-unwrapping implementation.

### Implementation

- UV unwrapping module: `backend/app/uv.py`
- Command-line script: `scripts/uv_unwrap.py`
- Mesh processing uses Trimesh.
- UV atlas generation uses xatlas.

### Verification Results

| Metric | Result |
|---|---:|
| Faces | 53,744 |
| Vertices after unwrapping | 39,039 |
| UV coordinate dimensions | 39,039 × 2 |
| Minimum UV coordinate | 0.0 |
| Maximum UV coordinate | 0.99965107 |

All UV coordinates are within the expected 0–1 range.

### Generated Files

Located in `outputs/week2/`:

- `chair_uv.obj` — UV-unwrapped chair mesh
- `chair_uv.uv.png` — UV layout preview
- `material.mtl` — OBJ material definition
- `material_0.png` — Exported 2×2 placeholder material image

The OBJ correctly references its MTL file, and the MTL references the placeholder image.

### Remaining Week 2 Work

- Verify Stable Diffusion ControlNet depth-based texture generation.
- Generate a texture from the same chair prompt.
- Bake the generated texture into the UV atlas.
- Verify the textured mesh in the Three.js viewer.

**Note:** UV unwrapping has been verified. ControlNet texturing and texture baking are not yet confirmed complete.
