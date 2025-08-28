from __future__ import annotations
from typing import Optional
from pathlib import Path

def read_txt(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")

def read_md(p: Path) -> str:
    return read_txt(p)

def read_pdf(p: Path) -> str:
    try:
        from pypdf import PdfReader
        r = PdfReader(str(p))
        return "\n".join([pg.extract_text() or "" for pg in r.pages])
    except Exception as e:
        return f""

def read_docx(p: Path) -> str:
    try:
        import docx
        d = docx.Document(str(p))
        return "\n".join([para.text for para in d.paragraphs])
    except Exception:
        return ""

def read_any(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".txt": return read_txt(path)
    if ext == ".md": return read_md(path)
    if ext == ".pdf": return read_pdf(path)
    if ext == ".docx": return read_docx(path)
    return ""
