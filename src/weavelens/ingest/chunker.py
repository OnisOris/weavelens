from __future__ import annotations
from typing import Iterable, List

def iter_chunks(text: str, max_chars: int = 1200, overlap: int = 120) -> Iterable[str]:
    """Split text into overlapping chunks by characters.

    Keeps words intact where possible.

    """
    if not text:
        return []
    words = text.split()
    chunks: List[str] = []
    cur: List[str] = []
    cur_len = 0
    for w in words:
        lw = len(w) + (1 if cur else 0)
        if cur_len + lw > max_chars and cur:
            chunk = " ".join(cur)
            chunks.append(chunk)
            # start new with overlap
            if overlap > 0 and chunks:
                tail = chunk[-overlap:]
                cur = [tail]
                cur_len = len(tail)
            else:
                cur = []
                cur_len = 0
        if not cur:
            cur = [w]
            cur_len = len(w)
        else:
            cur.append(w)
            cur_len += lw
    if cur:
        chunks.append(" ".join(cur))
    return chunks