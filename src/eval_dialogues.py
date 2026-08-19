"""Expected-action checks. From the repo root:

    python src/eval_dialogues.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tickets as tickets_mod

tickets_mod.TICKETS_PATH = Path(tempfile.mkdtemp()) / "tickets_eval.jsonl"

from orchestrator import handle_turn


def play(turns: list[dict]) -> list:
    tickets_mod.TICKETS_PATH.parent.mkdir(parents=True, exist_ok=True)
    tickets_mod.TICKETS_PATH.write_text("", encoding="utf-8")
    history: list[dict] = []
    phase = "open"
    last_rule = None
    last_ticket = None
    results = []
    for turn in turns:
        result = handle_turn(
            turn["text"],
            history=history,
            phase=phase,
            last_rule_id=last_rule,
            last_ticket_id=last_ticket,
        )
        results.append(result)
        history.append({"role": "user", "content": turn["text"]})
        history.append({"role": "assistant", "content": result.reply})
        phase = result.phase
        last_rule = result.last_rule_id
        if result.ticket:
            last_ticket = result.ticket["id"]
    return results


def _record_blob() -> str:
    parts = []
    for ticket in tickets_mod.load_tickets():
        parts.append(str(ticket.get("customer_ask", "")))
        parts.append(str(ticket.get("handoff_notes", "")))
        for item in ticket.get("followups") or []:
            if isinstance(item, dict):
                parts.append(str(item.get("text", "")))
            else:
                parts.append(str(item))
    return "\n".join(parts)


DIALOGUES = [
    {
        "name": "1_payment_rule",
        "turns": [
            {
                "text": (
                    "My student loan servicer never applied my payments correctly "
                    "and now they say I am late even though I paid on time."
                ),
                "action": "rule_reply",
                "rule": "payment_not_posted",
            }
        ],
    },
    {
        "name": "2_unresolved_ticket",
        "ticket_count": 1,
        "ask_contains": "student loan",
        "turns": [
            {
                "text": (
                    "My student loan servicer never applied my payments correctly "
                    "and now they say I am late even though I paid on time."
                ),
                "action": "rule_reply",
            },
            {
                "text": "That did not help, still the same.",
                "action": "ticket_from_request",
            },
        ],
    },
    {
        "name": "3_ticket_followup",
        "ticket_count": 1,
        "notes_contains": "8821",
        "turns": [
            {
                "text": (
                    "My student loan servicer never applied my payments correctly "
                    "and now they say I am late even though I paid on time."
                ),
                "action": "rule_reply",
            },
            {"text": "That did not help, still the same.", "action": "ticket_from_request"},
            {
                "text": "The last payment was on March 3, confirmation 8821.",
                "action": "ticket_followup",
                "same_ticket": True,
            },
        ],
    },
    {
        "name": "4_angry_file_complaint",
        "turns": [
            {
                "text": (
                    "I am furious about harassing collection calls every night. "
                    "This is ridiculous. File a complaint."
                ),
                "action": "ticket_from_request",
                "urgency": "high",
            }
        ],
    },
    {
        "name": "5_bank_fee_rule",
        "turns": [
            {
                "text": "The bank deducted an unexpected fee from my checking account.",
                "action": "rule_reply",
                "rule": "overdraft_fee",
            }
        ],
    },
    {
        "name": "6_unauthorized_forced",
        "turns": [
            {
                "text": (
                    "This charge is unauthorized fraud, I did not make this purchase "
                    "on my credit card."
                ),
                "action": "ticket_forced",
                "rule": "unauthorized_charge",
            }
        ],
    },
    {
        "name": "7_debt_not_mine",
        "turns": [
            {
                "text": "This is not my debt. I never owed this collector anything.",
                "action": "rule_reply",
                "rule": "debt_not_mine",
            }
        ],
    },
    {
        "name": "8_resolved_thanks",
        "turns": [
            {
                "text": (
                    "My student loan servicer never applied my payments correctly "
                    "and now they say I am late even though I paid on time."
                ),
                "action": "rule_reply",
            },
            {"text": "Thank you, that helped.", "action": "resolved"},
        ],
    },
    {
        "name": "9_vehicle_forced",
        "turns": [
            {
                "text": (
                    "I bought the car from the dealer and the transmission failed. "
                    "The vehicle loan company will not help."
                ),
                "action": "ticket_forced",
                "rule": "vehicle_dealer_vs_lender",
            }
        ],
    },
    {
        "name": "10_credit_report_rule",
        "turns": [
            {
                "text": (
                    "There is an incorrect account on my credit report that is not mine."
                ),
                "action": "rule_reply",
                "rule": "credit_report_error",
            }
        ],
    },
    {
        "name": "11_no_duplicate_ticket",
        "ticket_count": 1,
        "notes_contains": "still happening",
        "turns": [
            {
                "text": (
                    "I am furious about harassing collection calls every night. "
                    "This is ridiculous. File a complaint."
                ),
                "action": "ticket_from_request",
            },
            {
                "text": "Please file a complaint, this is still happening.",
                "action": "ticket_followup",
                "same_ticket": True,
            },
        ],
    },
]


def main() -> int:
    failed = 0
    for case in DIALOGUES:
        results = play(case["turns"])
        ticket_ids = []
        case_failed = False
        for turn, result in zip(case["turns"], results):
            action = result.debug.get("action")
            rule = result.debug.get("rule_id")
            ok = action == turn["action"]
            if turn.get("rule"):
                ok = ok and rule == turn["rule"]
            if turn.get("urgency") and result.ticket:
                ok = ok and result.ticket.get("urgency") == turn["urgency"]
            if result.ticket:
                ticket_ids.append(result.ticket["id"])
            if turn.get("same_ticket") and len(ticket_ids) >= 2:
                ok = ok and ticket_ids[-1] == ticket_ids[0]
            status = "OK" if ok else "FAIL"
            if not ok:
                case_failed = True
            print(
                f"{status:4} {case['name']:28} got={action} rule={rule} "
                f"expected={turn['action']}"
            )

        stored = tickets_mod.load_tickets()
        blob = _record_blob()
        extras = []
        if case.get("ticket_count") is not None:
            extras.append(len(stored) == case["ticket_count"])
        if case.get("notes_contains"):
            extras.append(case["notes_contains"] in blob)
        if case.get("ask_contains"):
            extras.append(any(case["ask_contains"] in str(t.get("customer_ask", "")) for t in stored))
        if extras and not all(extras):
            case_failed = True
            print(f"FAIL {case['name']:28} record checks failed")
        elif extras:
            print(f"OK   {case['name']:28} record checks")

        if case_failed:
            failed += 1

    print()
    if failed:
        print(f"{failed} dialogue(s) failed.")
        return 1
    print(f"All {len(DIALOGUES)} dialogues passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
