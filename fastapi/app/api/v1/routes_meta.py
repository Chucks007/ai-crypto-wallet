from fastapi import APIRouter
import subprocess

router = APIRouter()

def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True
        ).strip()
    except Exception:
        return "unknown"

@router.get("/health")
def health():
    return {"status": "ok", "version": _git_sha()}
