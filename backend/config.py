"""Runtime settings. Secrets come from the environment, never the source."""

from __future__ import annotations

import os
import secrets
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

DATABASE_URL = os.getenv("PHYSIO_DATABASE_URL", f"sqlite:///{BASE_DIR / 'physio.db'}")

UPLOAD_DIR = Path(os.getenv("PHYSIO_UPLOAD_DIR", PROJECT_ROOT / "uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_UPLOAD_BYTES = 10 * 1024 * 1024        # 10 MB
ALLOWED_UPLOAD_TYPES = {
    "application/pdf", "image/png", "image/jpeg", "image/webp", "image/bmp",
    "image/tiff",
}

JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = int(os.getenv("PHYSIO_JWT_EXPIRE_HOURS", "168"))   # 7 days

# Max keypoint frames accepted per session: ~10 min at 30fps. Bounds the
# request body and the analysis cost.
MAX_SESSION_FRAMES = 18000

DEV_MODE = os.getenv("PHYSIO_ENV", "dev") != "production"

CORS_ORIGINS = [
    o.strip() for o in os.getenv("PHYSIO_CORS_ORIGINS", "").split(",") if o.strip()
]


def _load_secret() -> str:
    """Require a real secret in production; generate a throwaway one in dev.

    A random dev secret means restarting the server invalidates old tokens,
    which is the correct trade: it is never a hardcoded value that could ship.
    """
    secret = os.getenv("PHYSIO_SECRET_KEY")
    if secret:
        return secret
    if not DEV_MODE:
        sys.exit(
            "PHYSIO_SECRET_KEY must be set when PHYSIO_ENV=production. "
            "Generate one with: python -c \"import secrets; "
            "print(secrets.token_urlsafe(32))\""
        )
    return secrets.token_urlsafe(32)


SECRET_KEY = _load_secret()
