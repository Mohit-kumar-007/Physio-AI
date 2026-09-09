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

# Max keypoint frames accepted per session: 3 minutes at 30fps. Every exercise
# in the catalogue targets 60 seconds or less, so this is already generous.
#
# It is a memory bound, not a policy. Measured cost of one request:
#     900 frames (30s)  -> 0.7 MB body,   9 MB peak
#    5400 frames (3min) -> 4.3 MB body,   65 MB peak
#   18000 frames (10min)-> 14.2 MB body, 190 MB peak, 5.3s of CPU
# Parsing dominates: 2.4M JSON numbers become millions of Python float and
# list objects before Pydantic has even validated them. At the old 18000 the
# numpy analysis on top brought a single request near 430 MB, so two at once
# would OOM a 1 GB box. Raise this only alongside more RAM.
MAX_SESSION_FRAMES = 5400

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
