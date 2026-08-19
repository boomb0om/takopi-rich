"""Telegram Bot API rich-message helpers."""

from __future__ import annotations

import re
from typing import Any, Literal

RichMessagesMode = Literal["off", "auto", "always"]

MAX_RICH_CHARS = 32768
MAX_RICH_BLOCKS = 500
MAX_RICH_COLUMNS = 20
_MIN_HEADING_ANSWER_CHARS = 400

_GFM_TABLE_SEP_RE = re.compile(r"^\|[\s:\-|]+\|$")
_HEADING_RE = re.compile(r"^ {0,3}#{2,6} \S")


def _prose_lines(text: str) -> list[str]:
    """Return lines outside fenced code blocks."""
    lines: list[str] = []
    fence: str | None = None
    for line in text.splitlines():
        stripped = line.lstrip()
        if fence is not None:
            if stripped.startswith(fence):
                fence = None
            continue
        if stripped.startswith("```"):
            fence = "```"
            continue
        if stripped.startswith("~~~"):
            fence = "~~~"
            continue
        lines.append(line)
    return lines


def _is_table_row(line: str) -> bool:
    stripped = line.strip()
    return len(stripped) > 1 and stripped.startswith("|") and stripped.endswith("|")


def _row_columns(line: str) -> int:
    return len(line.strip().strip("|").split("|"))


def markdown_has_gfm_table(text: str) -> bool:
    lines = _prose_lines(text)
    for header, separator in zip(lines, lines[1:], strict=False):
        if not _is_table_row(header):
            continue
        stripped_separator = separator.strip()
        if "---" in stripped_separator and _GFM_TABLE_SEP_RE.match(
            stripped_separator
        ):
            return True
    return False


def should_use_rich_message(text: str, mode: RichMessagesMode) -> bool:
    if mode == "off":
        return False
    stripped = text.strip()
    if not stripped:
        return False
    if mode == "always":
        return True
    if markdown_has_gfm_table(stripped):
        return True
    if len(stripped) <= _MIN_HEADING_ANSWER_CHARS:
        return False
    return any(_HEADING_RE.match(line) for line in _prose_lines(stripped))


def rich_limit_exceeded(markdown: str) -> str | None:
    if len(markdown.encode("utf-8")) > MAX_RICH_CHARS:
        return "chars"
    blocks = 0
    for line in _prose_lines(markdown):
        if _is_table_row(line) and _row_columns(line) > MAX_RICH_COLUMNS:
            return "columns"
        if line.strip():
            blocks += 1
    if blocks > MAX_RICH_BLOCKS:
        return "blocks"
    return None


def escape_raw_html(markdown: str) -> str:
    """Escape HTML openers outside fenced and inline code."""
    output: list[str] = []
    fence: str | None = None
    for line in markdown.splitlines(keepends=True):
        stripped = line.lstrip()
        if fence is not None:
            output.append(line)
            if stripped.startswith(fence):
                fence = None
            continue
        if stripped.startswith("```") or stripped.startswith("~~~"):
            fence = "```" if stripped.startswith("```") else "~~~"
            output.append(line)
            continue
        segments = line.split("`")
        output.append(
            "`".join(
                segment if index % 2 else segment.replace("<", "&lt;")
                for index, segment in enumerate(segments)
            )
        )
    return "".join(output)


def build_input_rich_message(markdown: str) -> dict[str, Any]:
    return {"markdown": escape_raw_html(markdown)}
