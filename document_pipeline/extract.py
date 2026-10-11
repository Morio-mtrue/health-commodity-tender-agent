from __future__ import annotations

import json
from pathlib import Path
import pdfplumber
from pypdf import PdfReader


def extract(path: Path, max_pages=250):
    """Native text only; unavailable OCR is an explicit page-level failure."""
    suffix = path.suffix.lower()
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Structured document must be an object")
        return {"pages": [{"page": 1, "text": json.dumps(payload, ensure_ascii=False, indent=2),
                            "method": "structured_json", "tables": []}], "structured": payload, "warnings": []}
    if suffix in {".txt", ".md"}:
        text = path.read_text(encoding="utf-8")
        pages = text.split("\f")
        if len(pages) > max_pages:
            raise ValueError("Document page limit exceeded")
        return {"pages": [{"page": i+1, "text": p, "method": "native_text", "tables": []}
                          for i,p in enumerate(pages)], "warnings": []}
    if suffix != ".pdf" or not path.read_bytes().startswith(b"%PDF-"):
        raise ValueError("Unsupported type or invalid PDF signature")
    reader = PdfReader(path)
    if reader.is_encrypted:
        raise ValueError("Encrypted PDF is not supported")
    if len(reader.pages) > max_pages:
        raise ValueError("Document page limit exceeded")
    # Do not execute PDF actions or open attachments. No rendering/OCR of unsanitized PDFs.
    warnings, pages = [], []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            method = "native_pdf"
            if not text.strip():
                method = "OCR_FAILED"
                warnings.append(f"OCR_FAILED: page {i+1} has no native text; OCR is not configured")
            tables = []
            for table in page.find_tables():
                tables.append({"bbox": list(table.bbox), "rows": table.extract()})
            pages.append({"page": i+1, "text": text, "method": method, "tables": tables})
    if not pages:
        raise ValueError("PDF has no pages")
    return {"pages": pages, "warnings": warnings}


def verify_citation(citation, documents):
    document = next((d for d in documents if d["id"] == citation.document_id), None)
    if not document or document["sha256"] != citation.sha256:
        raise ValueError("Citation references an unknown document hash")
    page = next((p for p in document["extraction"]["pages"] if p["page"] == citation.page), None)
    if not page or citation.quote not in page["text"]:
        raise ValueError("Citation quotation is absent from the cited page")
    return document
