"""Persist structured manager tickets as JSONL."""

import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TICKETS_PATH = ROOT / "data" / "tickets.jsonl"


def _next_id(existing: list[dict]) -> str:
    day = datetime.now().strftime("%Y%m%d")
    prefix = f"T-{day}-"
    seq = 0
    for ticket in existing:
        tid = str(ticket.get("id", ""))
        if tid.startswith(prefix):
            try:
                seq = max(seq, int(tid.split("-")[-1]))
            except ValueError:
                pass
    return f"{prefix}{seq + 1:04d}"


def load_tickets() -> list[dict]:
    if not TICKETS_PATH.exists():
        return []
    tickets = []
    for line in TICKETS_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        tickets.append(json.loads(line))
    return tickets


def save_ticket(ticket: dict) -> dict:
    TICKETS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with TICKETS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(ticket, ensure_ascii=False) + "\n")
    return ticket


def _rewrite(tickets: list[dict]) -> None:
    TICKETS_PATH.parent.mkdir(parents=True, exist_ok=True)
    TICKETS_PATH.write_text(
        "".join(json.dumps(t, ensure_ascii=False) + "\n" for t in tickets),
        encoding="utf-8",
    )


def create_ticket(
    *,
    urgency: str,
    category: str,
    category_confidence: float,
    sentiment: str,
    customer_ask: str,
    tried_rules: list[str],
    why_unresolved: str,
    summary_bullets: list[str],
    recommended_next_step: str,
    handoff_notes: str,
) -> dict:
    existing = load_tickets()
    ticket = {
        "id": _next_id(existing),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "urgency": urgency,
        "category": category,
        "category_confidence": round(float(category_confidence), 3),
        "sentiment": sentiment,
        "customer_ask": customer_ask.strip(),
        "tried_rules": tried_rules,
        "why_unresolved": why_unresolved,
        "summary_bullets": summary_bullets,
        "recommended_next_step": recommended_next_step,
        "handoff_notes": handoff_notes,
        "followups": [],
        "status": "open",
    }
    return save_ticket(ticket)


def append_followup(ticket_id: str, text: str) -> dict | None:
    """Keep extra customer detail on the same record. Never opens a second ticket."""
    note = (text or "").strip()
    if not ticket_id or not note:
        return None
    tickets = load_tickets()
    updated = None
    stamp = datetime.now().isoformat(timespec="seconds")
    for ticket in tickets:
        if ticket.get("id") != ticket_id:
            continue
        followups = list(ticket.get("followups") or [])
        followups.append({"at": stamp, "text": note})
        ticket["followups"] = followups
        existing = str(ticket.get("handoff_notes") or "").rstrip()
        ticket["handoff_notes"] = existing + f"\n\nFollow-up ({stamp}): {note}"
        updated = ticket
        break
    if updated is None:
        return None
    _rewrite(tickets)
    return updated


def update_status(ticket_id: str, status: str) -> dict | None:
    allowed = {"open", "in_progress", "resolved"}
    if status not in allowed:
        raise ValueError(f"Unknown status: {status}")
    tickets = load_tickets()
    updated = None
    for ticket in tickets:
        if ticket.get("id") == ticket_id:
            ticket["status"] = status
            updated = ticket
            break
    if updated is None:
        return None
    _rewrite(tickets)
    return updated
