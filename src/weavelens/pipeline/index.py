
from __future__ import annotations
import os, hashlib
from typing import List, Tuple, Dict, Any
from weavelens.settings import get_settings
from weavelens.db import weaviate_client as wv
from pypdf import PdfReader
from docx import Document as DocxDocument
settings = get_settings()


SUPPORTED = {".txt", ".md", ".pdf", ".docx", ".png", ".jpg", ".jpeg"}

def sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()

def read_text_from_path(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext in (".txt", ".md"):
        with open(path, "rb") as f:
            return f.read().decode("utf-8", errors="ignore")
    if ext == ".pdf":
        # Перестраховываемся: гибридно по страницам. Сначала извлекаем текст из слоя PDF.
        # Для страниц, где текста нет/очень мало, делаем OCR этой страницы.
        page_texts: List[str] = []
        num_pages = 0
        try:
            reader = PdfReader(path)
            num_pages = len(reader.pages)
            for page in reader.pages:
                t = (page.extract_text() or "").strip()
                page_texts.append(t)
        except Exception:
            page_texts = []
            num_pages = 0

        needs_ocr_indices: List[int] = []
        # Минимальная длина текста страницы, ниже которой считаем, что нужен OCR
        min_len = int(getattr(settings, "ocr_min_page_text_len", 20) or 20)
        if page_texts and any(not t or len(t) < min_len for t in page_texts):
            needs_ocr_indices = [i for i, t in enumerate(page_texts) if not t or len(t) < min_len]
        elif not page_texts:
            # Если вообще не удалось прочитать текст — OCR для всех страниц
            needs_ocr_indices = list(range(num_pages)) if num_pages > 0 else []

        if needs_ocr_indices:
            try:
                import fitz  # PyMuPDF
                from PIL import Image
                import pytesseract
            except Exception:
                # Нет OCR-зависимостей — вернём только то, что смогли достать (если что-то есть)
                return "\n\n".join([t for t in page_texts if t])
            try:
                doc = fitz.open(path)
                zoom = float(getattr(settings, "ocr_pdf_zoom", 2.0) or 2.0)
                mat = fitz.Matrix(zoom, zoom)
                # Если num_pages не был установлен, возьмём из doc
                if num_pages == 0:
                    num_pages = doc.page_count
                    page_texts = [""] * num_pages
                    needs_ocr_indices = list(range(num_pages))
                for i in needs_ocr_indices:
                    try:
                        page = doc.load_page(i)
                        pix = page.get_pixmap(matrix=mat)
                        mode = "RGB" if pix.alpha == 0 else "RGBA"
                        img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
                        if getattr(settings, "ocr_enabled", True):
                            lang = (getattr(settings, "ocr_langs", "rus+eng") or "eng").strip()
                            try:
                                t = pytesseract.image_to_string(img, lang=lang)
                            except Exception:
                                t = pytesseract.image_to_string(img, lang="eng")
                        else:
                            t = ""
                        t = (t or "").strip()
                        if t:
                            # Если ранее был какой-то текст, добавим OCR с разделителем, чтобы не дублировать вплотную
                            if i < len(page_texts) and page_texts[i]:
                                page_texts[i] = (page_texts[i].rstrip() + "\n\n" + t)
                            elif i < len(page_texts):
                                page_texts[i] = t
                            else:
                                # Защита на случай рассинхрона длин
                                page_texts.append(t)
                    except Exception:
                        continue
            except Exception:
                # Любая ошибка OCR — вернём то, что было
                return "\n\n".join([t for t in page_texts if t])

        # Если вообще ничего не извлекли — вернуть пусто
        joined = "\n\n".join([t for t in page_texts if t]).strip()
        return joined
    if ext == ".docx":
        doc = DocxDocument(path)
        return "\n".join(p.text for p in doc.paragraphs)
    if ext in (".png", ".jpg", ".jpeg"):
        # Lazy import to keep optional dependency
        try:
            from PIL import Image, ImageOps
            import pytesseract
        except Exception:
            return ""
        try:
            img = Image.open(path)
            # Respect EXIF orientation
            img = ImageOps.exif_transpose(img)
            # Simple normalization can help OCR on screenshots
            if img.mode not in ("L", "RGB"):
                img = img.convert("RGB")
            # Try Russian+English first, then fallback to English
            if getattr(settings, "ocr_enabled", True):
                lang = (getattr(settings, "ocr_langs", "rus+eng") or "eng").strip()
                try:
                    text = pytesseract.image_to_string(img, lang=lang)
                except Exception:
                    text = pytesseract.image_to_string(img, lang="eng")
            else:
                text = ""
            return (text or "").strip()
        except Exception:
            return ""
    return ""

def chunk_text(text: str, chunk_chars: int = 1200, overlap: int = 200) -> List[str]:
    text = text.strip()
    if not text:
        return []
    chunks = []
    i = 0
    n = len(text)
    while i < n:
        end = min(n, i + chunk_chars)
        chunks.append(text[i:end])
        if end == n:
            break
        i = end - overlap
        if i < 0:
            i = 0
    return chunks

def scan_and_index(paths: List[str]) -> Dict[str, Any]:
    files_processed = 0
    chunks_total = 0
    skipped = 0

    seen = set()
    for p in paths:
        if not p:
            continue
        p = os.path.abspath(p)
        if not os.path.exists(p):
            continue
        if os.path.isdir(p):
            for root, _, files in os.walk(p):
                for fn in files:
                    full = os.path.join(root, fn)
                    if os.path.splitext(full)[1].lower() in SUPPORTED:
                        seen.add(full)
        else:
            if os.path.splitext(p)[1].lower() in SUPPORTED:
                seen.add(p)

    for fp in sorted(seen):
        try:
            with open(fp, "rb") as f:
                data = f.read()
            sha = sha256_bytes(data)
            if wv.find_document_by_sha256(sha):
                skipped += 1
                continue
            title = os.path.basename(fp)
            size = os.path.getsize(fp)
            text = read_text_from_path(fp)
            ch = chunk_text(text)
            if not ch:
                skipped += 1
                continue
            doc_uuid = wv.upsert_document(fp, sha, title, size)
            cnt = wv.add_chunks(doc_uuid, fp, title, ch)
            files_processed += 1
            chunks_total += cnt
        except Exception:
            skipped += 1

    return {
        "files_indexed": files_processed,
        "chunks_indexed": chunks_total,
        "skipped": skipped,
        # legacy keys for bot
        "files": files_processed,
        "chunks": chunks_total,
    }
