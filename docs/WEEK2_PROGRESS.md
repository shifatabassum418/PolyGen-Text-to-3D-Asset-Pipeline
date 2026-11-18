# PolyGen — Week 2 Progress

## Milestone: UV Unwrapping and ControlNet Texturing

**Status:** Core Week 2 pipeline implemented and verified.

### 1. UV Unwrapping

The Week 1 chair mesh was processed using the existing xatlas UV-unwrapping implementation.

- Module: `backend/app/uv.py`
- CLI script: `scripts/uv_unwrap.py`
- Mesh processing: Trimesh
- UV generation: xatlas

**Verification results:**

| Metric | Result |
|---|---:|
| Faces | 53,744 |
| Vertices after unwrapping | 39,039 |
| UV coordinate dimensions | 39,039 × 2 |
| Minimum UV coordinate | 0.0 |
| Maximum UV coordinate | 0.99965107 |

All UV coordinates are within the expected 0–1 range.

### 2. ControlNet Texture Generation

Implemented an automated pipeline:

`scripts/generate_controlnet_texture.py`

The pipeline:
1. Loads a UV-unwrapped OBJ mesh.
2. Renders a depth map.
3. Generates a depth-guided texture using Stable Diffusion ControlNet.
4. Bakes the generated image into the UV atlas.
5. Exports the textured OBJ, MTL, and texture image.

**Successful Colab T4 test configuration:**
- Resolution: 512 × 512
- Inference steps: 20
- Seed: 42
- Conditioning scale: 0.8
- UV atlas resolution: 1024 × 1024

### 3. Generated Example Assets

Located in `outputs/week2_automated/`:

- `chair_automated.obj`
- `chair_automated.mtl`
- `chair_automated_texture.png`
- `chair_automated_depth.png`
- `chair_automated_controlnet.png`

The automated generation, baking, and export completed successfully.

### 4. Three.js Viewer

The previously exported textured chair was successfully loaded in the React Three.js viewer using its OBJ and MTL files.

The viewer supports textured mesh rendering, lighting, and orbit controls.

### 5. Automated Tests

Targeted tests passed locally:

- `tests/test_depth_texturing.py`
- `tests/test_mesh_uv.py`

**Result: 15 tests passed locally.**

### 6. Known Limitations

- Texture projection is a first-pass approach based on a rendered depth view.
- Occlusion and back-facing surface coverage are approximate.
- Full multi-view texturing is not implemented.
- PBR roughness, metallic, and normal maps remain future improvements.

### Week 2 Summary

UV unwrapping, depth-guided ControlNet generation, UV atlas baking, textured OBJ export, and viewer integration have been implemented and tested.

Week 2 is ready for final review and completion.
