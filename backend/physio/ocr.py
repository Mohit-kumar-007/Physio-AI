"""Medical report text extraction.

PDFs work with no system dependencies (pypdf reads the embedded text layer).
Scanned images need the Tesseract binary installed; when it is missing we say
so plainly rather than inventing findings -- fabricated medical text is worse
than no text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# Patterns for findings a physio actually acts on.
FINDING_PATTERNS = [
    (r"\b([CTL]\s?\d{1,2})\s*[-/]\s*([CTLS]\s?\d{1,2})\b", "spinal_level"),
    (r"\b(disc\s+(?:bulge|herniation|protrusion|desiccation|degeneration))\b", "disc"),
    (r"\b(spondylosis|spondylolisthesis|stenosis|scoliosis|kyphosis|lordosis)\b",
     "spinal_condition"),
    (r"\b(osteoarthritis|arthritis|osteophyte|chondromalacia)\b", "degenerative"),
    (r"\b((?:supraspinatus|infraspinatus|rotator\s+cuff)\s+\w*\s*tear)\b", "shoulder"),
    (r"\b((?:acl|pcl|mcl|lcl|meniscal|meniscus)\s+\w*\s*tear)\b", "knee_ligament"),
    (r"\b(tendinitis|tendinopathy|bursitis|capsulitis|effusion)\b", "soft_tissue"),
    (r"\b(fracture|fissure)\b", "fracture"),
    (r"\b(mild|moderate|severe)\s+(\w+)", "severity"),
]

SEVERITY_ORDER = {"mild": 1, "moderate": 2, "severe": 3}


@dataclass
class ExtractedReport:
    text: str
    findings: list[dict]
    engine: str
    ok: bool
    message: str = ""

    def summary(self, lang: str = "en") -> str:
        if not self.ok:
            return self.message
        if not self.findings:
            return ("Report read, but no standard physiotherapy findings were "
                    "recognised. Please describe your symptoms in your own words."
                    if lang == "en" else
                    "रिपोर्ट पढ़ी गई, पर कोई मानक निष्कर्ष नहीं मिला। कृपया अपने "
                    "लक्षण अपने शब्दों में बताएँ।")
        labels = ", ".join(f["text"] for f in self.findings[:4])
        return (f"Extracted findings: {labels}" if lang == "en"
                else f"निकाले गए निष्कर्ष: {labels}")


def extract_findings(text: str) -> list[dict]:
    """Pull recognisable clinical findings out of free report text."""
    found, seen = [], set()
    lowered = text.lower()
    for pattern, kind in FINDING_PATTERNS:
        for match in re.finditer(pattern, lowered, re.IGNORECASE):
            phrase = " ".join(match.group(0).split())
            key = (kind, phrase)
            if key in seen:
                continue
            seen.add(key)
            found.append({
                "type": kind,
                "text": phrase,
                "severity": next(
                    (s for s in SEVERITY_ORDER if s in phrase), None
                ),
            })
    return found


def _read_pdf(path: Path) -> tuple[str, str, bool, str]:
    try:
        from pypdf import PdfReader
    except ImportError:
        return "", "none", False, "PDF support is not installed on the server."
    try:
        reader = PdfReader(str(path))
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
    except Exception as exc:
        return "", "pypdf", False, f"Could not read the PDF: {exc}"
    if not text.strip():
        return "", "pypdf", False, (
            "This PDF has no text layer - it is likely a scan. Upload it as an "
            "image instead, or type the findings manually."
        )
    return text, "pypdf", True, ""


def _read_image(path: Path) -> tuple[str, str, bool, str]:
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        return "", "none", False, "OCR libraries are not installed on the server."
    try:
        text = pytesseract.image_to_string(Image.open(path))
    except Exception:
        # Almost always the Tesseract binary missing from PATH.
        return "", "tesseract", False, (
            "OCR engine not available. Install Tesseract "
            "(https://github.com/UB-Mannheim/tesseract/wiki) and restart the "
            "server, or type your report findings into the chat instead."
        )
    if not text.strip():
        return "", "tesseract", False, (
            "No readable text found in that image. Try a sharper, well-lit photo."
        )
    return text, "tesseract", True, ""


def extract(path: str | Path) -> ExtractedReport:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        text, engine, ok, message = _read_pdf(path)
    elif suffix in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}:
        text, engine, ok, message = _read_image(path)
    else:
        return ExtractedReport("", [], "none", False,
                               f"Unsupported file type: {suffix}")
    return ExtractedReport(
        text=text.strip()[:20000],
        findings=extract_findings(text) if ok else [],
        engine=engine,
        ok=ok,
        message=message,
    )
