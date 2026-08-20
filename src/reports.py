"""Store chatbot reporting commands; daily_jobs.py executes them."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from text_norm import fold_tr
from tickets import load_tickets

ROOT = Path(__file__).resolve().parent.parent
REPORT_JOBS_PATH = ROOT / "data" / "report_jobs.jsonl"

REPORT_PHRASES = (
    "rapor",
    "günlük özet",
    "gunluk ozet",
    "açık talepler",
    "acik talepler",
    "ticket raporu",
    "birim özeti",
    "birim ozeti",
)


def looks_report_command(text: str) -> bool:
    lowered = fold_tr(text)
    return any(p in lowered for p in REPORT_PHRASES)


def load_jobs() -> list[dict]:
    if not REPORT_JOBS_PATH.exists():
        return []
    jobs: list[dict] = []
    for line in REPORT_JOBS_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        jobs.append(json.loads(line))
    return jobs


def _next_id(existing: list[dict]) -> str:
    day = datetime.now().strftime("%Y%m%d")
    prefix = f"R-{day}-"
    seq = 0
    for job in existing:
        jid = str(job.get("id", ""))
        if jid.startswith(prefix):
            try:
                seq = max(seq, int(jid.split("-")[-1]))
            except ValueError:
                pass
    return f"{prefix}{seq + 1:04d}"


def queue_report_job(
    *,
    command: str,
    birim: str = "",
    requested_by: str = "",
) -> dict:
    existing = load_jobs()
    job = {
        "id": _next_id(existing),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "command": (command or "").strip(),
        "birim": birim,
        "requested_by": (requested_by or "").strip().lower(),
        "status": "queued",
        "result": "",
        "run_at": "",
    }
    REPORT_JOBS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_JOBS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(job, ensure_ascii=False) + "\n")
    return job


def _rewrite(jobs: list[dict]) -> None:
    REPORT_JOBS_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JOBS_PATH.write_text(
        "".join(json.dumps(j, ensure_ascii=False) + "\n" for j in jobs),
        encoding="utf-8",
    )


def build_unit_summary(birim: str = "") -> str:
    tickets = load_tickets()
    if birim:
        tickets = [t for t in tickets if str(t.get("birim") or "") == birim]
    open_n = sum(1 for t in tickets if t.get("status") in {"open", "in_progress", ""})
    resolved_n = sum(1 for t in tickets if t.get("status") == "resolved")
    by_unit: dict[str, int] = {}
    for ticket in tickets:
        label = str(ticket.get("birim_label") or ticket.get("birim") or "—")
        by_unit[label] = by_unit.get(label, 0) + 1
    lines = [
        f"ITSM özet ({datetime.now().strftime('%Y-%m-%d %H:%M')})",
        f"Toplam kayıt: {len(tickets)} · açık/işlenen: {open_n} · kapanan: {resolved_n}",
    ]
    if by_unit:
        lines.append("Birim kırılımı: " + ", ".join(f"{k}={v}" for k, v in sorted(by_unit.items())))
    else:
        lines.append("Henüz ticket yok.")
    lines.append("İlgili birim kuyruğuna iletildi (prototip: kayıt dosyasına yazıldı).")
    return "\n".join(lines)


def run_queued_jobs() -> list[dict]:
    jobs = load_jobs()
    ran: list[dict] = []
    stamp = datetime.now().isoformat(timespec="seconds")
    for job in jobs:
        if job.get("status") != "queued":
            continue
        job["result"] = build_unit_summary(str(job.get("birim") or ""))
        job["status"] = "sent"
        job["run_at"] = stamp
        ran.append(job)
    if ran:
        _rewrite(jobs)
    return ran
