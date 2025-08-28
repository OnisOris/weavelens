from __future__ import annotations
import re
from typing import List

def split_into_chunks(text: str, max_tokens: int = 800, overlap: int = 80) -> List[str]:
    sents = re.split(r"(?<=[.!?\n])\s+", text.strip())
    chunks, cur, toks = [], [], 0
    for s in sents:
        t = len(s.split())
        if toks + t > max_tokens and cur:
            joined = " ".join(cur).strip()
            chunks.append(joined)
            back = " ".join(joined.split()[-overlap:]) if overlap else ""
            cur, toks = ([back] if back else [], len(back.split()))
        cur.append(s)
        toks += t
    if cur:
        chunks.append(" ".join(cur).strip())
    return [c for c in chunks if c]
