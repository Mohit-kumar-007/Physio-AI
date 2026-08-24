"""Medical report upload and text extraction."""

from __future__ import annotations

import secrets
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlmodel import Session, desc, select

from ..auth import optional_user
from ..config import ALLOWED_UPLOAD_TYPES, MAX_UPLOAD_BYTES, UPLOAD_DIR
from ..db import get_session
from ..models import Report, User
from ..physio import ocr
from ..schemas import ReportOut

router = APIRouter(prefix="/api/reports", tags=["reports"])

CHUNK = 64 * 1024
SAFE_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


def _store(upload: UploadFile) -> tuple[Path, int]:
    """Stream to disk under a generated name, enforcing the size cap as we go.

    The client filename is never used as a path -- only the extension is kept,
    and only from an allowlist, so a crafted name cannot escape UPLOAD_DIR.
    """
    suffix = Path(upload.filename or "").suffix.lower()
    if suffix not in SAFE_SUFFIXES:
        raise HTTPException(415, f"Unsupported file type: {suffix or 'unknown'}")

    stored_name = f"{secrets.token_hex(16)}{suffix}"
    destination = UPLOAD_DIR / stored_name
    size = 0
    try:
        with destination.open("wb") as out:
            while chunk := upload.file.read(CHUNK):
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        413,
                        f"File is larger than {MAX_UPLOAD_BYTES // (1024 * 1024)} MB",
                    )
                out.write(chunk)
    except HTTPException:
        destination.unlink(missing_ok=True)
        raise
    return destination, size


@router.post("", response_model=ReportOut)
def upload_report(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    user: User | None = Depends(optional_user),
) -> ReportOut:
    if file.content_type not in ALLOWED_UPLOAD_TYPES:
        raise HTTPException(415, f"Unsupported content type: {file.content_type}")

    path, size = _store(file)
    result = ocr.extract(path)

    # Feed the extracted findings back into the chat box so the user can send
    # them to the assessment endpoint.
    suggested = ""
    if result.ok and result.findings:
        suggested = " ".join(f["text"] for f in result.findings[:6])

    record_id = None
    if user:
        record = Report(
            user_id=user.id,
            filename=Path(file.filename or "report").name,
            stored_name=path.name,
            content_type=file.content_type,
            size_bytes=size,
            extracted_text=result.text,
            findings=result.findings,
            engine=result.engine,
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        record_id = record.id
    else:
        # Nothing to attach it to; do not keep a stranger's medical document.
        path.unlink(missing_ok=True)

    return ReportOut(
        id=record_id,
        filename=Path(file.filename or "report").name,
        ok=result.ok,
        engine=result.engine,
        summary=result.summary(),
        findings=result.findings,
        suggested_text=suggested,
        message=result.message,
    )


@router.get("")
def list_reports(
    session: Session = Depends(get_session),
    user: User | None = Depends(optional_user),
) -> dict:
    if not user:
        return {"items": []}
    rows = session.exec(
        select(Report)
        .where(Report.user_id == user.id)
        .order_by(desc(Report.created_at))
        .limit(50)
    ).all()
    return {
        "items": [
            {"id": r.id, "filename": r.filename, "findings": r.findings,
             "engine": r.engine, "created_at": r.created_at}
            for r in rows
        ]
    }
