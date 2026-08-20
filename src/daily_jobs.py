"""Run queued chatbot report jobs (daily JOB stand-in).

    python src/daily_jobs.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reports import load_jobs, run_queued_jobs


def main() -> int:
    ran = run_queued_jobs()
    if not ran:
        queued = [j for j in load_jobs() if j.get("status") == "queued"]
        print(f"Çalışacak iş yok. Kuyrukta {len(queued)} kayıt.")
        return 0
    for job in ran:
        print(f"{job['id']} → {job['status']}")
        print(job.get("result") or "")
        print("---")
    print(f"{len(ran)} rapor ilgili birim kaydına işlendi.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
