"""Bootstrap sys.path so FastAPI app can import the repo's `backend` package.

This mirrors the pytest conftest behavior for runtime.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent  # repo root
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

