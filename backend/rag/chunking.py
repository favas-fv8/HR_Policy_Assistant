"""Structure-aware recursive chunking for RAG documents.

Tokenizer: tiktoken cl100k_base when available (consistent approximation for
Gemini embedding tokenization); fallback to a deterministic regex/word heuristic.
Token counts are estimates unless an exact model tokenizer is integrated.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Iterable, List

try:
    import tiktoken  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    tiktoken = None

HEADING_RE = re.compile(
    r"^(?:[A-Z][A-Z0-9\s/&()\-]{2,}|(?:summary|profile|skills?|technical skills?|work experience|professional experience|experience|projects?|education|certifications?|certificates?|languages?|achievements?|publications?|objective|responsibilities|qualifications|eligibility|policy|procedure|procedures|exceptions?|definitions?|scope|purpose|overview|guidelines?))\s*:?\s*$",
    re.IGNORECASE,
)


@dataclass
class PageText:
    page_number: int
    text: str


@dataclass
class ChunkSpec:
    chunk_index: int
    chunk_text: str
    page_start: int
    page_end: int
    page_number: int
    character_count: int
    token_count: int
    section_heading: str


class TokenCounter:
    def __init__(self):
        self.name = "approx-word"
        self._enc = None
        if tiktoken is not None:
            try:
                self._enc = tiktoken.get_encoding("cl100k_base")
                self.name = "tiktoken:cl100k_base"
            except Exception:
                self._enc = None

    def count(self, text: str) -> int:
        if not text:
            return 0
        if self._enc is not None:
            try:
                return len(self._enc.encode(text))
            except Exception:
                pass
        return len(re.findall(r"\S+", text))

    def split_to_token_limit(self, text: str, max_tokens: int) -> List[str]:
        if not text.strip():
            return []
        if self.count(text) <= max_tokens:
            return [text.strip()]
        if self._enc is not None:
            try:
                ids = self._enc.encode(text)
                parts = []
                for i in range(0, len(ids), max_tokens):
                    part = self._enc.decode(ids[i:i + max_tokens]).strip()
                    if part:
                        parts.append(part)
                return parts
            except Exception:
                pass
        words = re.findall(r"\S+", text)
        parts, cur, cur_n = [], [], 0
        for w in words:
            wn = self.count(w)
            add = wn + (1 if cur else 0)
            if cur and cur_n + add > max_tokens:
                parts.append(" ".join(cur).strip())
                cur, cur_n = [w], wn
            else:
                cur.append(w)
                cur_n += add
        if cur:
            parts.append(" ".join(cur).strip())
        final = []
        for p in parts:
            if self.count(p) <= max_tokens:
                final.append(p)
            else:
                step = max(200, max_tokens * 4)
                for i in range(0, len(p), step):
                    seg = p[i:i + step].strip()
                    if seg:
                        final.append(seg)
        return final


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = [ln.strip() for ln in text.split("\n")]
    return "\n".join(lines).strip()


def _is_heading(line: str) -> bool:
    s = (line or "").strip()
    if not s or len(s) > 90:
        return False
    if s.endswith(".") and len(s.split()) > 8:
        return False
    return bool(HEADING_RE.match(s))


def _split_sentences(text: str) -> List[str]:
    text = normalize_text(text)
    if not text:
        return []
    text = re.sub(r"\n+", "\n", text)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])|\n+", text)
    out = [p.strip() for p in parts if p and p.strip()]
    return out or [text]


@dataclass
class Segment:
    text: str
    page_start: int
    page_end: int
    section_heading: str


def build_segments(pages: Iterable[PageText]) -> List[Segment]:
    segments: List[Segment] = []
    current_heading = ""
    for page in pages:
        text = normalize_text(page.text)
        if not text:
            continue
        blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
        for block in blocks:
            lines = [ln.strip() for ln in block.split("\n") if ln.strip()]
            if not lines:
                continue
            if len(lines) == 1 and _is_heading(lines[0]):
                current_heading = lines[0].strip().strip(":")
                continue
            if _is_heading(lines[0]) and len(lines) > 1:
                current_heading = lines[0].strip().strip(":")
                body = "\n".join(lines[1:]).strip()
            else:
                body = "\n".join(lines).strip()
            if not body:
                continue
            segments.append(Segment(body, page.page_number, page.page_number, current_heading))
    return segments


def _segment_units(segment: Segment, counter: TokenCounter, max_tokens: int) -> List[Segment]:
    text = normalize_text(segment.text)
    if not text:
        return []
    if counter.count(text) <= max_tokens:
        return [Segment(text, segment.page_start, segment.page_end, segment.section_heading)]
    sentences = _split_sentences(text)
    if len(sentences) > 1:
        units = []
        for s in sentences:
            units.extend(_segment_units(Segment(s, segment.page_start, segment.page_end, segment.section_heading), counter, max_tokens))
        return units
    return [Segment(p, segment.page_start, segment.page_end, segment.section_heading) for p in counter.split_to_token_limit(text, max_tokens)]


def chunk_pages(pages: List[PageText], target_tokens: int = 450, max_tokens: int = 600, overlap_tokens: int = 60, min_tokens: int = 100):
    counter = TokenCounter()
    target_tokens = max(100, int(target_tokens))
    max_tokens = max(target_tokens, int(max_tokens))
    overlap_tokens = max(0, min(int(overlap_tokens), target_tokens - 1))
    min_tokens = max(1, min(int(min_tokens), target_tokens))

    segments = build_segments(pages)
    units: List[Segment] = []
    for seg in segments:
        units.extend(_segment_units(seg, counter, max_tokens))

    chunks: List[ChunkSpec] = []
    current: List[Segment] = []
    current_tokens = 0

    def flush(force=False):
        nonlocal current, current_tokens
        if not current:
            return
        text = normalize_text("\n\n".join(s.text for s in current))
        tok = counter.count(text)
        if not force and tok < min_tokens and chunks:
            return
        pages_in = [p for s in current for p in (s.page_start, s.page_end)]
        chunk = ChunkSpec(
            chunk_index=len(chunks),
            chunk_text=text,
            page_start=min(pages_in),
            page_end=max(pages_in),
            page_number=min(pages_in),
            character_count=len(text),
            token_count=tok,
            section_heading=next((s.section_heading for s in reversed(current) if s.section_heading), ""),
        )
        chunks.append(chunk)
        if overlap_tokens <= 0:
            current, current_tokens = [], 0
            return
        tail, tail_tokens = [], 0
        for s in reversed(current):
            st = counter.count(s.text)
            if tail and tail_tokens + st > overlap_tokens:
                break
            tail.insert(0, s)
            tail_tokens += st
            if tail_tokens >= overlap_tokens:
                break
        # Avoid duplicate full-chunk carryover when overlap consumes entire chunk.
        if len(tail) >= len(current):
            current, current_tokens = [], 0
            return
        current = tail
        current_tokens = sum(counter.count(s.text) for s in current)

    for unit in units:
        utok = counter.count(unit.text)
        if not unit.text:
            continue
        if current and current_tokens + utok > max_tokens:
            before = len(chunks)
            flush(force=False)
            if len(chunks) == before:
                flush(force=True)
        if utok > max_tokens:
            for part in counter.split_to_token_limit(unit.text, max_tokens):
                part_unit = Segment(part, unit.page_start, unit.page_end, unit.section_heading)
                ptok = counter.count(part)
                if current and current_tokens + ptok > max_tokens:
                    flush(force=True)
                current.append(part_unit)
                current_tokens += ptok
                if current_tokens >= target_tokens:
                    flush(force=current_tokens >= min_tokens)
            continue
        current.append(unit)
        current_tokens += utok
        if current_tokens >= target_tokens:
            flush(force=current_tokens >= min_tokens)

    if current:
        tail_text = normalize_text("\n\n".join(s.text for s in current))
        tail_tokens = counter.count(tail_text)
        if chunks and tail_tokens < min_tokens:
            prev = chunks[-1]
            merged = normalize_text(prev.chunk_text + "\n\n" + tail_text)
            merged_tok = counter.count(merged)
            if merged_tok <= max_tokens + overlap_tokens:
                prev.chunk_text = merged
                prev.character_count = len(merged)
                prev.token_count = merged_tok
                prev.page_start = min(prev.page_start, min(s.page_start for s in current))
                prev.page_end = max(prev.page_end, max(s.page_end for s in current))
                prev.page_number = prev.page_start
                if not prev.section_heading:
                    prev.section_heading = next((s.section_heading for s in reversed(current) if s.section_heading), "")
                current = []
        if current:
            flush(force=True)

    for i, c in enumerate(chunks):
        c.chunk_index = i

    total_chars = sum(len(normalize_text(p.text)) for p in pages)
    total_tokens = sum(counter.count(normalize_text(p.text)) for p in pages if p.text)
    stats = {
        "tokenizer": counter.name,
        "total_extracted_characters": total_chars,
        "total_extracted_tokens": total_tokens,
        "total_chunks": len(chunks),
    }
    return chunks, stats


def get_chunking_config():
    return {
        "target_tokens": int(os.getenv("RAG_CHUNK_TARGET_TOKENS", "450")),
        "max_tokens": int(os.getenv("RAG_CHUNK_MAX_TOKENS", "600")),
        "overlap_tokens": int(os.getenv("RAG_CHUNK_OVERLAP_TOKENS", "60")),
        "min_tokens": int(os.getenv("RAG_CHUNK_MIN_TOKENS", "100")),
    }
