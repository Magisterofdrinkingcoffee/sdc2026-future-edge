"""Vercel entry point: serves the FastAPI backend as a Python serverless function.
The React frontend is built to static files (see vercel.json)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.backend.main import app  # noqa: E402,F401
