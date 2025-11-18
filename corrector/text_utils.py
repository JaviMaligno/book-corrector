from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass
class Token:
    id: int
    text: str
    start: int
    end: int
    kind: str  # 'word' | 'number' | 'punct' | 'space' | 'newline'
    line: int  # 1-based logical line number computed from newlines


def tokenize(text: str) -> list[Token]:
    tokens: list[Token] = []
    i = 0
    tid = 0
    line = 1
    # Order matters: newline, whitespace, word, number, single non-space char
    pattern = re.compile(r"(\r\n|\n)|([\t\x0b\x0c\r ]+)|([A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)|([0-9]+)|(\S)")
    for m in pattern.finditer(text):
        if m.start() > i:
            # Unexpected gap; treat as raw text (fallback)
            gap = text[i : m.start()]
            tokens.append(Token(tid, gap, i, m.start(), "space", line))
            tid += 1
        if m.group(1):
            val = m.group(1)
            tokens.append(Token(tid, val, m.start(), m.end(), "newline", line))
            tid += 1
            line += 1
        elif m.group(2):
            val = m.group(2)
            tokens.append(Token(tid, val, m.start(), m.end(), "space", line))
            tid += 1
        elif m.group(3):
            val = m.group(3)
            tokens.append(Token(tid, val, m.start(), m.end(), "word", line))
            tid += 1
        elif m.group(4):
            val = m.group(4)
            tokens.append(Token(tid, val, m.start(), m.end(), "number", line))
            tid += 1
        elif m.group(5):
            val = m.group(5)
            tokens.append(Token(tid, val, m.start(), m.end(), "punct", line))
            tid += 1
        i = m.end()
    if i < len(text):
        gap = text[i:]
        tokens.append(Token(tid, gap, i, len(text), "space", line))
    return tokens


def detokenize(tokens: Sequence[Token]) -> StringErrorOrStr:
    return "".join(t.text for t in tokens)


@dataclass
class Correction:
    token_id: int
    replacement: str
    reason: str
    original: str | None = None


StringErrorOrStr = str


def apply_token_corrections(tokens: list[Token], corrections: Sequence[Correction]) -> list[Token]:
    # Apply in order of token_id ascending, but replacing text only
    corrected = list(tokens)
    for corr in sorted(corrections, key=lambda c: c.token_id):
        if 0 <= corr.token_id < len(corrected):
            tok = corrected[corr.token_id]
            # Only replace words/numbers/punct; spaces/newlines are not replaced
            if tok.kind in ("word", "number", "punct"):
                # Optional check original
                if corr.original is None or tok.text == corr.original:
                    corrected[corr.token_id] = Token(
                        tok.id, corr.replacement, tok.start, tok.end, tok.kind, tok.line
                    )
                else:
                    # Replace anyway to keep deterministic behavior
                    corrected[corr.token_id] = Token(
                        tok.id, corr.replacement, tok.start, tok.end, tok.kind, tok.line
                    )
    return corrected


def count_word_tokens(tokens: Sequence[Token]) -> int:
    return sum(1 for t in tokens if t.kind == "word")


def split_tokens_in_chunks(
    tokens: Sequence[Token], max_words: int, overlap_words: int
) -> list[tuple[int, int]]:
    """Return list of (start_idx, end_idx) token ranges for chunks.

    Chunks are contiguous slices of tokens with at most `max_words` word tokens. Adjacent
    chunks overlap by up to `overlap_words` word tokens. Boundaries align on token indices.

    Additionally, the splitter prefers natural boundaries (end of sentence punctuation or
    newlines) near the target limit to preserve coherence across chunks.
    """
    if max_words <= 0:
        return [(0, len(tokens))]
    ranges: list[tuple[int, int]] = []
    n = len(tokens)
    i = 0
    while i < n:
        # find end index covering max_words word tokens
        words = 0
        j = i
        while j < n and words < max_words:
            if tokens[j].kind == "word":
                words += 1
            j += 1
        # extend to include trailing spaces/newlines following last word
        while j < n and tokens[j].kind in ("space", "newline"):
            j += 1
        # Prefer natural boundary before j if close
        # Look back up to this many word tokens to find a sentence boundary
        lookback_words = 50
        j_adj = j

        # Helpers for boundaries/closers
        def _is_eos_punct(tok: Token) -> bool:
            return tok.kind == "punct" and tok.text in (".", "!", "?", "…")

        def _is_closer(tok: Token) -> bool:
            return tok.kind == "punct" and tok.text in (
                ")",
                "]",
                "}",
                '"',
                "'",
                "»",
                "«",
                "“",
                "”",
                "’",
            )

        # Step back skipping trailing spaces/newlines
        k = j_adj - 1
        while k > i and tokens[k].kind in ("space", "newline"):
            k -= 1
        back_words = 0
        while k > i and back_words <= lookback_words:
            # Newline is a hard boundary
            if tokens[k].kind == "newline":
                j_adj = k + 1
                while j_adj < n and tokens[j_adj].kind in ("space", "newline"):
                    j_adj += 1
                break
            # If at EOS punct or at a run of closing punctuation after EOS punct
            if _is_eos_punct(tokens[k]) or _is_closer(tokens[k]):
                m = k
                # Skip any closers backwards to find potential EOS punct
                while m > i and _is_closer(tokens[m]):
                    m -= 1
                if m >= i and _is_eos_punct(tokens[m]):
                    j_adj = m + 1
                    # extend forward to include closers and any following spaces/newlines
                    while j_adj < n and (
                        _is_closer(tokens[j_adj]) or tokens[j_adj].kind in ("space", "newline")
                    ):
                        j_adj += 1
                    break
            if tokens[k].kind == "word":
                back_words += 1
            k -= 1
        # Only use adjusted boundary if it makes progress and keeps some content
        if j_adj > i + 1:
            ranges.append((i, j_adj))
            j = j_adj
        else:
            ranges.append((i, j))
        if j >= n:
            break
        # move i forward but keep overlap_words word tokens overlapping
        if overlap_words > 0:
            back_words = 0
            k = j - 1
            # step back over trailing spaces
            while k > i and tokens[k].kind in ("space", "newline"):
                k -= 1
            # now count back overlap_words words
            while k > i and back_words < overlap_words:
                if tokens[k].kind == "word":
                    back_words += 1
                k -= 1
            # position next start at the token after k
            i = max(k + 1, 0)
        else:
            i = j
    return ranges


def build_context(tokens: Sequence[Token], center_index: int, radius: int = 3) -> str:
    left = max(0, center_index - radius)
    right = min(len(tokens), center_index + radius + 1)
    # Compact context: include text directly
    return "".join(t.text for t in tokens[left:right]).strip()


def _is_sentence_end_or_closer_seq(tokens: Sequence[Token], idx: int, min_idx: int = 0) -> bool:
    """Return True if there is an end-of-sentence (.,!,?,…) possibly followed by closers ending at or before idx.

    Accepts patterns like ".", ".)" , ".”" , "…" and treats a newline as a boundary too.
    """
    t = tokens[idx]
    if t.kind == "newline":
        return True

    def _is_eos(tok: Token) -> bool:
        return tok.kind == "punct" and tok.text in (".", "!", "?", "…")

    def _is_closer(tok: Token) -> bool:
        return tok.kind == "punct" and tok.text in (
            ")",
            "]",
            "}",
            '"',
            "'",
            "»",
            "«",
            "“",
            "”",
            "’",
        )

    # If current is EOS
    if _is_eos(t):
        return True
    # If current is a closer, look back to find EOS before closers
    if _is_closer(t):
        k = idx
        while k - 1 >= min_idx and _is_closer(tokens[k]):
            k -= 1
        if k - 1 >= min_idx and _is_eos(tokens[k - 1]):
            return True
    return False


def sentence_bounds(tokens: Sequence[Token], center_index: int) -> tuple[int, int]:
    """Return (start, end) token indices for the sentence surrounding center_index.

    The end index is exclusive. Newlines and .,!,?,… are treated as sentence boundaries.
    """
    n = len(tokens)
    # Find start: look back to previous EOS or newline; skip closer sequences
    s = center_index
    while s > 0:
        if _is_sentence_end_or_closer_seq(tokens, s - 1):
            break
        s -= 1
    # Skip leading spaces/newlines
    while s < n and tokens[s].kind in ("space", "newline"):
        s += 1
    # Find end: advance to next EOS; then include closers and trailing space/newline
    e = center_index
    while e < n:
        if _is_sentence_end_or_closer_seq(tokens, e, min_idx=s):
            e += 1
            # include any immediate closers following the EOS
            while (
                e < n
                and tokens[e].kind == "punct"
                and tokens[e].text in (")", "]", "}", '"', "'", "»", "«", "“", "”", "’")
            ):
                e += 1
            break
        e += 1
    # Extend to include trailing spaces/newlines
    while e < n and tokens[e].kind in ("space", "newline"):
        e += 1
    return max(0, s), min(n, e)


def build_sentence_context(
    tokens: Sequence[Token], center_index: int, max_chars: int | None = None
) -> str:
    s, e = sentence_bounds(tokens, center_index)
    text = "".join(t.text for t in tokens[s:e]).strip()
    if max_chars is not None and len(text) > max_chars:
        return text[: max_chars - 1] + "…"
    return text


def split_tokens_by_char_budget(
    tokens: Sequence[Token], *, char_budget: int, overlap_chars: int
) -> list[tuple[int, int]]:
    """Return list of (start_idx, end_idx) ranges such that each chunk has <= char_budget.

    Char count is computed as the sum of token.text lengths for tokens inside the range.
    Overlap between chunks is by characters (overlap_chars), attempting to align on token boundaries.
    """
    if char_budget <= 0:
        return [(0, len(tokens))]
    ranges: list[tuple[int, int]] = []
    n = len(tokens)
    i = 0
    while i < n:
        current_chars = 0
        j = i
        # grow chunk up to budget
        while j < n and current_chars + len(tokens[j].text) <= char_budget:
            current_chars += len(tokens[j].text)
            j += 1
        # include trailing spaces/newlines to avoid splitting mid-whitespace
        while j < n and tokens[j].kind in ("space", "newline"):
            current_chars += len(tokens[j].text)
            j += 1
        ranges.append((i, j))
        if j >= n:
            break
        # compute new start with overlap_chars from the end
        if overlap_chars > 0:
            back_chars = 0
            k = j - 1
            while k > i and back_chars < overlap_chars:
                back_chars += len(tokens[k].text)
                k -= 1
            i = max(k + 1, 0)
        else:
            i = j
    return ranges
