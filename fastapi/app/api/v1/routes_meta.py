import os
from pathlib import Path

from fastapi import APIRouter

router = APIRouter()


def _git_sha() -> str:
    # Prefer env override (useful in restricted sandboxes)
    sha_env = os.environ.get("GIT_SHA")
    if sha_env:
        return sha_env[:7]

    try:
        git_dir = Path(".git")
        head_text = (git_dir / "HEAD").read_text().strip()
        sha: str | None = None
        if head_text.startswith("ref:"):
            ref = head_text.split(" ", 1)[1].strip()
            ref_path = git_dir / ref
            if ref_path.exists():
                sha = ref_path.read_text().strip()
            else:
                packed = git_dir / "packed-refs"
                if packed.exists():
                    for line in packed.read_text().splitlines():
                        if not line or line.startswith("#"):
                            continue
                        if " " in line:
                            cand, refname = line.split(" ", 1)
                            if refname.strip() == ref:
                                sha = cand.strip()
                                break
        else:
            # Detached HEAD with direct SHA
            sha = head_text
        if sha and len(sha) >= 7:
            return sha[:7]
    except Exception:
        pass
    return "unknown"


@router.get("/health")
def health():
    return {"status": "ok", "version": _git_sha()}
