# Test Report: Weeks 1 and 2

**Status vocabulary:** PASS = executed and succeeded · FAIL = executed and failed · SKIPPED = test exists but its dependency is missing,
so it did not run · NOT TESTED = no test could be run in this environment.

**Environment of this report:** Linux sandbox, Python 3.12.3, NumPy 2.5.4, Pillow 13.0.0, Node 22. **No GPU, no network.**
Not installed: torch, diffusers, trimesh, xatlas, fastapi, httpx, pytest. Nothing below was run on the author's Windows laptop
(NVIDIA GPU absent, C: drive full) or in Google Colab.

## Results

| # | Check | Result | Notes |
|---|-------|--------|-------|
| 1 | Python syntax (`py_compile`, all `.py` files) | **PASS** | Syntax only, not behaviour |
| 2 | Depth renderer (3 unit tests) | **PASS** | Near/far values, silhouette changes with azimuth, output size/mode |
| 3 | Texture baking (2 unit tests) | **PASS** | Solid colour fills atlas; back faces sample the mirrored image |
| 4 | Textured OBJ/MTL export + export validator (5 unit tests) | **PASS** | Record counts, UV-count mismatch rejected, missing texture / out-of-range UV / missing OBJ detected |
| 5 | Config + generator registry (3 unit tests) | **PASS** | Absolute paths; unknown generator raises `ValueError` |
| 6 | Mutation check of the tests | **PASS** | Breaking back-face mirroring and depth normalization made the matching tests FAIL; code restored, tests pass again |
| 7 | Synthetic end-to-end of the non-AI texture steps (3,072-face UV sphere: depth, bake, write, validate) | **PASS** | Used a per-triangle stand-in for xatlas and a synthetic gradient in place of a ControlNet image. Depth 0.13 s, bake 1.29 s. Depth image inspected visually |
| 8 | Mesh cleanup / normalize / stats (3 tests) | **SKIPPED** | `trimesh` not installed |
| 9 | xatlas UV unwrap + unwrap-bake-export (2 tests) | **SKIPPED** | `trimesh` and `xatlas` not installed |
| 10 | API endpoints (7 tests: health, validation errors, 404, job success, job failure, TripoSR-missing 400) | **SKIPPED** | `fastapi` / `httpx` not installed |
| 11 | TripoSR "not installed" error message (1 test) | **SKIPPED** | `torch` not installed |
| 12 | Backend startup (`uvicorn app.main:app`) | **NOT TESTED** | fastapi unavailable, no network to install |
| 13 | Shap-E pipeline (Route A) | **NOT TESTED** | Needs GPU, torch, diffusers, model download |
| 14 | TripoSR pipeline (Route B) | **NOT TESTED** | Needs GPU, TripoSR clone, `torchmcubes` build, model download |
| 15 | Stable Diffusion / ControlNet texture generation | **NOT TESTED** | Needs GPU and model download |
| 16 | xatlas UV unwrapping on a real mesh | **NOT TESTED** | xatlas unavailable |
| 17 | Geometry audit script | **NOT TESTED** | Needs generated meshes; script syntax only (see #1) |
| 18 | Export validation on a real pipeline export | **NOT TESTED** | Validator itself passes on synthetic exports (#4, #7) |
| 19 | Frontend syntax (`esbuild` on 6 JS/JSX files) | **PASS** | Syntax only. Does not prove the app builds or renders |
| 20 | `npm install`, `npm run dev`, `npm run build` | **NOT TESTED** | No network |
| 21 | React 3D viewer rendering (OBJ and textured OBJ/MTL) | **NOT TESTED** | Needs browser and installed packages |
| 22 | Frontend-backend communication | **NOT TESTED** | Neither side could be run |
| 23 | Colab notebook | **NOT TESTED** | JSON valid, 0 syntax errors in 27 cells (`ast.parse`); never executed in Colab |
| 24 | `scripts/setup_triposr.sh` | **NOT TESTED** | `bash -n` syntax check passes; never executed |

Totals for the automated suite: **26 tests, 13 PASS, 13 SKIPPED, 0 FAIL.**

## How to run the full suite yourself
```powershell
python -m unittest discover -s tests -t . -v
```
After installing `backend/requirements.txt` (for example on Colab), the 13 skipped tests should run. Record your results below
and update the README status table.

## Your verification log (fill in as you verify each stage)

| Date | Check | Result | Notes |
|------|-------|--------|-------|
|      | Colab: GPU check | | |
|      | Colab: unit tests | | |
|      | Colab: Shap-E mesh (texture = none) | | |
|      | Colab: ControlNet texturing | | |
|      | Colab: export validation | | |
|      | Local: viewer with `?obj=...&mtl=...` | | |
|      | Local: full prompt-to-viewer flow (if a GPU machine is available) | | |
|      | TripoSR (optional) | | |
