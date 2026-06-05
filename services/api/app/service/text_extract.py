import io
import logging

logger = logging.getLogger(__name__)

# Cap how much text we feed the LLM per source so a huge PDF can't blow the
# context window (and cost). Generous enough for typical articles/notes.
MAX_CHARS_PER_SOURCE = 40_000


def _extract_pdf_text(data: bytes) -> str:
    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(io.BytesIO(data))
        parts = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(parts)
    except Exception:
        logger.warning("PDF text extraction failed", exc_info=True)
        return ""


def extract_text(data: bytes, content_type: str) -> str:
    """Extract plain text from a source document.

    Supports PDF (PyPDF2) and plain-text / markdown (decoded directly).
    Returns an empty string when nothing usable can be extracted; the
    generation service treats an all-empty source set as a failure.
    """
    if content_type == "application/pdf":
        text = _extract_pdf_text(data)
    elif content_type in ("text/plain", "text/markdown"):
        text = data.decode("utf-8", errors="replace")
    else:
        logger.warning("Unsupported source content type: %s", content_type)
        text = ""
    return text.strip()[:MAX_CHARS_PER_SOURCE]
