"""Validate a textured export folder: python scripts/validate_export.py backend/outputs/<job_id>"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.validation import validate_textured_export  # noqa: E402

problems = validate_textured_export(Path(sys.argv[1]))
print("OK: export is valid" if not problems else "\n".join(f"- {p}" for p in problems))
raise SystemExit(1 if problems else 0)
