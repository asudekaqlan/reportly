"""Retrieve similar past ITSM solution records. Keyword overlap, no live CMDB."""

from __future__ import annotations

import json
from pathlib import Path

from text_norm import fold_tr

ROOT = Path(__file__).resolve().parent.parent
SOLUTIONS_PATH = ROOT / "data" / "solutions.jsonl"


def load_solutions() -> list[dict]:
    if not SOLUTIONS_PATH.exists():
        return []
    rows: list[dict] = []
    for line in SOLUTIONS_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _score(text: str, row: dict) -> int:
    lowered = fold_tr(text)
    keywords = [fold_tr(str(k)) for k in (row.get("keywords") or [])]
    title = fold_tr(str(row.get("title") or ""))
    score = sum(1 for kw in keywords if kw and kw in lowered)
    if title and title in lowered:
        score += 2
    unit = fold_tr(str(row.get("birim_label") or row.get("birim") or ""))
    if unit and unit in lowered:
        score += 1
    return score


def find_solutions(text: str, *, birim: str = "", limit: int = 2) -> list[dict]:
    ranked: list[tuple[int, dict]] = []
    for row in load_solutions():
        score = _score(text, row)
        if birim and str(row.get("birim") or "") == birim:
            score += 1
        if score <= 0:
            continue
        ranked.append((score, row))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return [row for _, row in ranked[:limit]]


def format_solution(row: dict) -> str:
    steps = row.get("steps") or []
    if isinstance(steps, str):
        body = steps
    else:
        body = "\n".join(f"{i}. {step}" for i, step in enumerate(steps, start=1))
    title = row.get("title") or "Çözüm kaydı"
    sid = row.get("id") or ""
    return f"**{title}** ({sid})\n{body}"
