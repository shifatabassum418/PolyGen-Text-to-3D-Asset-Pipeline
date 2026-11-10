# PolyGen: Generative Text-to-3D Asset Pipeline

Type a prompt such as *"A rusted, medieval broadsword with a glowing blue sapphire in the hilt"*, get a 3D mesh,
UV-unwrap it, texture it with Stable Diffusion + ControlNet, and inspect the result in a browser 3D viewer.

This repository covers **Week 1 (mesh generation + 3D canvas)** and **Week 2 (texture generation + UV unwrapping)**
of the Infotact Solutions Second-Month Project. Week 3 (decimation, PBR) and Week 4 (GLB export, HDRI polish) are **not started**.

> **Read the [Implementation and testing status](#implementation-and-testing-status) first.** The code was written and
> unit-tested for its non-AI logic, but the model-based stages have **not** been run end-to-end yet. They need a GPU;
> use the Google Colab notebook for that.

## Architecture and workflow

Two independent mesh-generation routes feed one shared processing and texturing pipeline:

```
 Route A (Week 1)   prompt ─► Shap-E (text -> 3D) ───────────────────────────────┐
 Route B (Week 1)   prompt ─► SD-Turbo (text -> image) ─► background removal      │
                              ─► TripoSR (image -> 3D) ───────────────────────────┤
                                                                                  ▼
                       raw.obj ─► clean + normalize (trimesh) ─► clean.obj   ── texture = none ──► viewer
                                                    │
                                                    ▼  (Week 2)
                              UV unwrap (xatlas) ─► depth map (NumPy z-buffer)
                                                    ─► Stable Diffusion + ControlNet-depth
                                                    ─► bake into UV atlas ─► model.obj + model.mtl + model_texture.png
                                                                                  │
 React + react-three-fiber viewer  ◄─────  FastAPI jobs (/api/generate, /api/jobs/{id}, /files/...)
```

- **Shap-E** generates a mesh *directly from text*.
- **TripoSR** turns an *image* into a mesh, so Route B first generates an image from the prompt with SD-Turbo.
- **trimesh** is used for mesh IO, cleanup and statistics. It is **not** the UV unwrapper; **xatlas** does the unwrapping.
- Meshes are Y-up, centered, max extent 1.0, front facing +Z.

## Features

- Two selectable generation routes (Shap-E, TripoSR) behind one `MeshGenerator` interface
- Mesh cleanup: duplicate-vertex merge, degenerate-face removal, floating-debris removal, consistent normals, normalization
- xatlas UV atlas, depth-map rendering, ControlNet-depth texture generation, projection baking with edge padding
- Textured OBJ + MTL + PNG export and an export validator
- FastAPI job API with background execution, progress stages and error reporting
- React viewer (OBJ and textured OBJ/MTL), orbit controls, lighting, readable error messages, and `?obj=/files/<job>/model.obj&mtl=...` to open an existing export
- CLI scripts for each stage, a geometry-audit script, a unit-test suite, and a Colab notebook

## Technologies

Python 3.10-3.12, PyTorch, diffusers (Shap-E, Stable Diffusion, ControlNet), TripoSR, trimesh, xatlas, NumPy, Pillow,
FastAPI, Uvicorn, React 18, Vite, three.js, @react-three/fiber, @react-three/drei.

## Project structure

```
backend/        FastAPI app (app/), requirements.txt, requirements-triposr.txt, .env.example
frontend/       React + Vite viewer
tests/          unittest suite (also runs under pytest)
scripts/        CLI tools: check_gpu, generate_mesh, generate_texture, uv_unwrap, validate_export, geometry_audit, setup_triposr
docs/           TEST_REPORT.md (what was and was not tested)
PolyGen_Colab.ipynb
```

## Installation

Requirements: Python 3.10-3.12, Node.js 18+, and for real generation an **NVIDIA GPU with ~8 GB+ VRAM** and
**~20 GB free disk** (PyTorch ~5 GB, model weights ~8-10 GB). No NVIDIA GPU or little disk space? Use [Google Colab](#google-colab).

**Windows (PowerShell), from the repository root:**

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1          # if blocked: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121   # install PyTorch FIRST
pip install -r requirements.txt
python ..\scripts\check_gpu.py      # should print cuda: True
```

**Linux / macOS:** same steps with `source .venv/bin/activate` and `python ../scripts/check_gpu.py`.

Optional configuration: copy `backend/.env.example` to `backend/.env` (never commit `.env`).

**Optional, Route B (TripoSR):** `bash scripts/setup_triposr.sh` (Linux/Colab). It compiles `torchmcubes`; on Windows this
needs MSVC build tools and the CUDA toolkit, so Colab is easier.

## Run the backend

```powershell
cd backend
.venv\Scripts\Activate.ps1
uvicorn app.main:app --port 8000
```

Check it: open http://localhost:8000/api/health or http://localhost:8000/docs.
The first generation downloads model weights, which takes several minutes.

## Run the frontend

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Enter a prompt, choose the mesh model and texture mode, press **Generate model**.
Texture modes: *Depth-guided (ControlNet)*, *Flat material*, *None (geometry only)*. Start with **None** to test Week 1 alone.

**No GPU on this machine?** Generate on Colab, download `polygen_results.zip`, unzip it into `backend/outputs/`, start the
backend (`uvicorn app.main:app --port 8000`; only `fastapi` and `uvicorn` are needed to serve files) and open an existing export directly:

```
http://localhost:5173/?obj=/files/colab_textured/model.obj&mtl=/files/colab_textured/model.mtl
```

## Command-line usage

```powershell
python scripts\generate_mesh.py "a wooden chair" --generator shape      # Route A
python scripts\generate_mesh.py "a wooden chair" --generator triposr    # Route B
python scripts\generate_texture.py "rusted iron sword"                  # flat SD texture
python scripts\uv_unwrap.py in.obj out.obj                              # xatlas + UV preview PNG
python scripts\validate_export.py backend\outputs\<job_id>              # check a textured export
python scripts\geometry_audit.py --generator shape                      # 5-prompt geometry audit (GPU)
```

Outputs are written to `backend/outputs/<job_id>/` (`raw.obj`, `clean.obj`, `depth.png`, `front_view.png`,
`model.obj`, `model.mtl`, `model_texture.png`).

## Google Colab

1. Zip this repository (or download it) as `PolyGen-Text-to-3D-Asset-Pipeline.zip`.
2. Open https://colab.research.google.com, **File > Upload notebook**, choose `PolyGen_Colab.ipynb`.
3. **Runtime > Change runtime type > T4 GPU**, then run the cells in order.
4. Upload the ZIP when prompted. The notebook installs dependencies, runs the unit tests, generates a Shap-E mesh,
   textures it, validates the export and previews the 3D model.

The TripoSR cell is optional and not verified in Colab. See the notebook's introduction for details.

## Testing

From the repository root:

```powershell
python -m unittest discover -s tests -t . -v      # no extra tools needed
# or
pytest
```

Tests whose dependencies are missing are **skipped** with a reason, never silently passed. The full list and the actual
results are in [`docs/TEST_REPORT.md`](docs/TEST_REPORT.md).

## Implementation and testing status

Honest summary as of the last verification (Linux sandbox, Python 3.12, no GPU, no network):

| Area | Implemented | Verified |
|------|:-----------:|----------|
| Depth-map renderer, texture baking, textured OBJ/MTL writer, export validator | yes | **Yes**, unit tests pass (incl. mutation checks) |
| Config, generator registry | yes | **Yes**, unit tests pass |
| Mesh cleanup / stats (trimesh) | yes | No: tests written, skipped (trimesh not installed here) |
| xatlas UV unwrap | yes | No: test written, skipped (xatlas not installed here) |
| Shap-E route (Route A) | yes | **No**: needs GPU + model download |
| TripoSR route (Route B) | yes | **No**: needs GPU + TripoSR install |
| SD + ControlNet texturing | yes | **No**: needs GPU + model download |
| FastAPI endpoints | yes | No: tests written, skipped (fastapi not installed here) |
| React viewer / frontend | yes | Syntax only (esbuild). `npm install`, build and rendering **not tested** |
| Colab notebook | yes | JSON and cell syntax only. **Not executed** |

## Week 1 checklist (mesh generation + 3D canvas)

- [x] Shap-E direct text-to-3D generator (implemented; not yet run end-to-end)
- [x] TripoSR image-to-3D generator with SD-Turbo text-to-image step (implemented; not yet run end-to-end)
- [x] FastAPI integration with background jobs, progress and error reporting
- [x] React frontend with prompt submission and generation workflow
- [x] react-three-fiber viewer with lighting and orbit controls
- [x] Frontend-backend communication (Vite proxy, CORS, polling, readable errors)
- [x] Dependency configuration (requirements split for core vs. TripoSR)
- [ ] Verified end-to-end on a GPU (**pending**; use Colab)

## Week 2 checklist (texture generation + UV unwrapping)

- [x] Stable Diffusion flat texture and ControlNet-depth texture generation (implemented; not yet run end-to-end)
- [x] xatlas UV unwrapping (trimesh is *not* used for this)
- [x] trimesh cleanup and normalization
- [x] Texture-to-mesh integration: projection baking into the UV atlas, OBJ/MTL/PNG export, export validator
- [x] Texture rendering in the React viewer (MTLLoader)
- [x] Geometry-audit script (implemented; not yet run)
- [ ] Verified end-to-end on a GPU, including visual check of the textured viewer (**pending**)

## Known limitations

- **Texture quality:** the texture comes from a *single front view*. Faces turned away from +Z receive a *mirrored copy* of the
  front image, so backs and sides can look wrong. Occlusion is ignored (a hidden front-facing part gets the pixel in front of it).
  Multi-view baking is future work and out of scope for Weeks 1-2.
- **Flat mode** applies the same material image to every UV chart; it does not follow object parts.
- **Winding / orientation:** baking assumes outward-facing triangles (`fix_normals` is applied during cleanup). The TripoSR
  re-orientation copies TripoSR's own viewer transform but has not been verified here.
- **Shap-E** meshes are low-resolution and sometimes blobby. TripoSR output is typically cleaner but can exceed 100k faces
  (decimation is Week 3).
- **Textures are albedo only.** No PBR maps (Week 3).
- One job runs at a time (GPU lock); jobs are kept in memory and lost on server restart.
- Dependency version bounds in `requirements.txt` are conservative but unverified on every platform.
- No `package-lock.json` is included (it could not be generated offline); `npm install` will create one.
- Not started by design: mesh decimation, PBR materials, GLB export, HDRI environment (Weeks 3-4).
