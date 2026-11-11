
import threading
import traceback
import uuid
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from .config import settings
from .pipeline import run_pipeline

app = FastAPI(title="PolyGen")
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_methods=["*"],
    allow_headers=["*"]
)

settings.output_dir.mkdir(parents=True, exist_ok=True)
app.mount("/files", StaticFiles(directory=settings.output_dir), name="files")

JOBS: dict[str, dict] = {}
GPU_LOCK = threading.Lock()  # one generation at a time on a single GPU


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=300)
    generator: str = Field(default=settings.default_generator, pattern="^(shape|triposr)$")
    seed: int | None = None
    texture: str = Field(default="controlnet", pattern="^(none|flat|controlnet)$")

    @field_validator("prompt", mode="before")
    @classmethod
    def clean_prompt(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value


def _run(job_id: str, req: GenerateRequest):
    job = JOBS[job_id]

    def progress(stage: str):
        job["stage"] = stage

    try:
        with GPU_LOCK:
            result = run_pipeline(
                req.prompt,
                settings.output_dir / job_id,
                req.generator,
                req.seed,
                req.texture,
                progress
            )

        base = f"/files/{job_id}/"
        job["result"] = {
            "obj_url": base + result["obj"],
            "mtl_url": base + result["mtl"] if result["mtl"] else None,
            "stats": result["stats"],
        }
        job["status"], job["stage"] = "done", "done"

    except Exception as e:
        traceback.print_exc()
        job["status"], job["error"] = "error", f"{type(e).__name__}: {e}"


@app.get("/api/health")
def health():
    try:
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        device = "torch-not-installed"

    return {
        "ok": True,
        "device": device,
        "triposr_installed": settings.triposr_dir.exists()
    }


@app.post("/api/generate")
def generate(req: GenerateRequest, bg: BackgroundTasks):
    if req.generator == "triposr" and not settings.triposr_dir.exists():
        raise HTTPException(
            400,
            "TripoSR is not installed. Run scripts/setup_triposr.sh first."
        )

    job_id = uuid.uuid4().hex[:12]
    JOBS[job_id] = {
        "id": job_id,
        "status": "running",
        "stage": "queued",
        "prompt": req.prompt
    }

    bg.add_task(_run, job_id, req)
    return JOBS[job_id]


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(404, "job not found")
    return JOBS[job_id]
