"""
Pytest configuration for FastAPI project.

Ensures repository root is on sys.path so tests can import `backend.*`.
"""
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent  # repo root
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

