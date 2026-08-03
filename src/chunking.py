from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text)]
        sentences = [s for s in sentences if s]
        if not sentences:
            return []

        limit = self.max_sentences_per_chunk
        return [
            " ".join(sentences[start : start + limit])
            for start in range(0, len(sentences), limit)
        ]


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        current_text = current_text.strip()
        if not current_text:
            return []
        if len(current_text) <= self.chunk_size:
            return [current_text]

        # Hết separator để thử: cắt cứng theo chunk_size để đệ quy luôn kết thúc.
        if not remaining_separators:
            return [
                current_text[start : start + self.chunk_size]
                for start in range(0, len(current_text), self.chunk_size)
            ]

        separator = remaining_separators[0]
        rest = remaining_separators[1:]

        # Separator rỗng nghĩa là cắt theo ký tự -> xử lý như khi hết separator.
        if separator == "":
            return self._split(current_text, [])

        pieces = current_text.split(separator)
        if len(pieces) == 1:
            # Separator này không cắt được gì: hạ xuống separator ưu tiên thấp hơn.
            return self._split(current_text, rest)

        chunks: list[str] = []
        buffer = ""
        for piece in pieces:
            candidate = piece if not buffer else buffer + separator + piece
            if len(candidate) <= self.chunk_size:
                buffer = candidate
                continue
            if buffer:
                chunks.append(buffer)
                buffer = ""
            # Mảnh đơn lẻ vẫn quá dài -> đệ quy với danh sách separator đã ngắn đi.
            if len(piece) > self.chunk_size:
                chunks.extend(self._split(piece, rest))
            else:
                buffer = piece
        if buffer:
            chunks.append(buffer)
        return [c for c in (chunk.strip() for chunk in chunks) if c]


class MarkdownHeadingChunker:
    """
    Chia tài liệu theo tiêu đề Markdown (## / ###) — chiến lược TV4 của bài.

    Mỗi mục (heading + phần thân của nó) là một chunk, nhờ vậy điều kiện và ngoại lệ
    trong cùng một mục không bị cắt rời nhau. Hai tinh chỉnh so với bản ngây thơ:

        - Mục quá ngắn (< min_chunk_size) được gộp vào mục kế tiếp, tránh sinh ra các
          chunk chỉ có một dòng tiêu đề.
        - Mục quá dài (> chunk_size) được cắt tiếp bằng RecursiveChunker, nhưng mỗi
          mảnh vẫn được gắn lại dòng tiêu đề để không mất ngữ cảnh "đây là mục nào".
    """

    HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)

    def __init__(self, chunk_size: int = 1000, min_chunk_size: int = 120, max_heading_level: int = 3) -> None:
        self.chunk_size = chunk_size
        self.min_chunk_size = min_chunk_size
        self.max_heading_level = max_heading_level

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        sections = self._split_sections(text)
        if not sections:
            return []

        merged = self._merge_short_sections(sections)

        chunks: list[str] = []
        for heading, body in merged:
            block = f"{heading}\n{body}".strip() if heading else body.strip()
            if not block:
                continue
            if len(block) <= self.chunk_size:
                chunks.append(block)
                continue
            # Mục dài hơn chunk_size: cắt tiếp nhưng giữ tiêu đề trên từng mảnh.
            for index, piece in enumerate(RecursiveChunker(chunk_size=self.chunk_size).chunk(body)):
                chunks.append(f"{heading}\n{piece}".strip() if heading and index else piece.strip())
        return [c for c in chunks if c]

    def _split_sections(self, text: str) -> list[tuple[str, str]]:
        """Cắt text thành [(dòng heading, phần thân)], phần mở đầu có heading rỗng."""
        matches = [
            m for m in self.HEADING_PATTERN.finditer(text)
            if len(m.group(1)) <= self.max_heading_level
        ]
        if not matches:
            return [("", text)]

        sections: list[tuple[str, str]] = []
        preamble = text[: matches[0].start()].strip()
        if preamble:
            sections.append(("", preamble))

        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            sections.append((match.group(0).strip(), text[match.end() : end].strip()))
        return sections

    def _merge_short_sections(self, sections: list[tuple[str, str]]) -> list[tuple[str, str]]:
        """Gộp mục quá ngắn vào mục ngay sau nó (thường là heading cha không có nội dung)."""
        merged: list[tuple[str, str]] = []
        pending: list[str] = []
        for heading, body in sections:
            block = f"{heading}\n{body}".strip()
            if len(block) < self.min_chunk_size:
                pending.append(block)
                continue
            if pending:
                heading_with_parents = "\n".join([*pending, heading]).strip()
                merged.append((heading_with_parents, body))
                pending = []
            else:
                merged.append((heading, body))
        if pending:                                   # phần thừa ở cuối
            if merged:
                last_heading, last_body = merged[-1]
                merged[-1] = (last_heading, f"{last_body}\n{chr(10).join(pending)}".strip())
            else:
                merged.append(("", "\n".join(pending)))
        return merged


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    norm_a = math.sqrt(_dot(vec_a, vec_a))
    norm_b = math.sqrt(_dot(vec_b, vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return _dot(vec_a, vec_b) / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=chunk_size // 10),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=3),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }

        comparison: dict = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            total = sum(len(chunk) for chunk in chunks)
            comparison[name] = {
                "count": len(chunks),
                "avg_length": total / len(chunks) if chunks else 0.0,
                "chunks": chunks,
            }
        return comparison
