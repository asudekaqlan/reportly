"""Decide each turn: rule reply, ticket."""

from dataclasses import dataclass, field

from intents import detect_intents
from nlu_engine import predict_category
from rules import match_rule
from sentiment import analyze_sentiment, looks_positive_resolution
from summaries import build_manager_copy, llm_enabled
from tickets import append_followup, create_ticket

LOW_CONFIDENCE = 0.35


@dataclass
class TurnResult:
    reply: str
    phase: str
    last_rule_id: str | None
    ticket: dict | None = None
    debug: dict = field(default_factory=dict)


def _urgency(sentiment: str, high_risk: bool) -> str:
    if high_risk or sentiment == "angry":
        return "high"
    return "medium"


def _primary_customer_ask(history: list[dict], text: str) -> str:
    for message in history:
        if message.get("role") == "user":
            ask = str(message.get("content") or "").strip()
            if ask:
                return ask
    return (text or "").strip()


def _open_ticket(
    *,
    nlu: dict,
    sentiment: dict,
    text: str,
    tried_rules: list[str],
    why: str,
    history: list[dict],
) -> dict:
    customer_ask = _primary_customer_ask(history, text)
    copy = build_manager_copy(
        category=nlu["category"],
        sentiment=sentiment["label"],
        customer_ask=customer_ask,
        tried_rules=tried_rules,
        why_unresolved=why,
        high_risk=sentiment["high_risk"],
        history=history,
        latest_user=text,
    )
    return create_ticket(
        urgency=_urgency(sentiment["label"], sentiment["high_risk"]),
        category=nlu["category"],
        category_confidence=nlu["confidence"],
        sentiment=sentiment["label"],
        customer_ask=customer_ask,
        tried_rules=tried_rules,
        why_unresolved=why,
        summary_bullets=copy["summary_bullets"],
        recommended_next_step=copy["recommended_next_step"],
        handoff_notes=copy["handoff_notes"],
    )


def _ticket_reply(ticket: dict, extra: str = "") -> str:
    body = (
        f"I could not finish this with self-serve steps, so I opened an urgent specialist record "
        f"in the background: {ticket['id']} (urgency: {ticket['urgency']}). "
        "A supervisor brief is attached to that record."
    )
    if extra:
        body = extra.rstrip() + "\n\n" + body
    return body + "\n\nIf you have more detail, write it here."


def _followup_reply(
    *,
    last_ticket_id: str | None,
    rule,
    wants_complaint: bool,
) -> str:
    opened = "Your specialist record is already open"
    if last_ticket_id:
        opened += f" ({last_ticket_id})"
    opened += "."
    if wants_complaint:
        return opened + " I logged this on that same record instead of opening a second one."
    if rule:
        return rule.reply + "\n\n" + opened + " I added this detail to the supervisor notes."
    return (
        opened
        + " I added this detail to the supervisor notes. "
        "Add any missing dates, amounts, or confirmation numbers here if needed."
    )


def _with_llm_reply(result: TurnResult, customer_text: str) -> TurnResult:
    """Rewrite customer-facing text only. Decision stays in handle_turn."""
    if not llm_enabled():
        return result
    if len((customer_text or "").strip()) < 12:
        return result
    from llm_analyze import rewrite_customer_reply

    rewritten = rewrite_customer_reply(
        canned_reply=result.reply,
    )
    if rewritten:
        result.reply = rewritten
    return result


def handle_turn(
    text: str,
    *,
    history: list[dict],
    phase: str,
    last_rule_id: str | None,
    last_ticket_id: str | None = None,
) -> TurnResult:
    text = (text or "").strip()
    nlu = predict_category(text)
    sentiment = analyze_sentiment(text)
    intents = detect_intents(text)
    matched = match_rule(text, nlu["category"])
    rule = matched["rule"] if matched else None

    debug = {
        "category": nlu["category"],
        "confidence": nlu["confidence"],
        "sentiment": sentiment["label"],
        "high_risk": sentiment["high_risk"],
        "intents": {
            "file_complaint": intents["file_complaint"],
            "still_unresolved": intents["still_unresolved"],
        },
        "rule_id": rule.id if rule else None,
        "rule_score": matched["score"] if matched else 0,
        "action": None,
    }

    tried = [last_rule_id] if last_rule_id else []
    if rule and rule.id not in tried:
        tried.append(rule.id)

    if phase == "waiting_if_resolved" and looks_positive_resolution(text) and not intents["still_unresolved"]:
        debug["action"] = "resolved"
        return _with_llm_reply(
            TurnResult(
                reply="Glad that helped. If something else goes wrong with the account, write it here.",
                phase="open",
                last_rule_id=None,
                debug=debug,
            ),
            text,
        )

    wants_complaint = intents["file_complaint"] or (
        phase == "waiting_if_resolved" and intents["still_unresolved"]
    )
    force_ticket = bool(rule and not rule.usually_resolves) or sentiment["high_risk"]
    low_conf = nlu["confidence"] < LOW_CONFIDENCE and nlu["category"] != "Unknown"

    if phase == "ticket_open":
        debug["action"] = "ticket_followup"
        ticket = append_followup(last_ticket_id or "", text)
        return _with_llm_reply(
            TurnResult(
                reply=_followup_reply(
                    last_ticket_id=last_ticket_id,
                    rule=rule,
                    wants_complaint=wants_complaint,
                ),
                phase="ticket_open",
                last_rule_id=rule.id if rule else last_rule_id,
                ticket=ticket,
                debug=debug,
            ),
            text,
        )

    if phase == "waiting_if_resolved" and not wants_complaint:
        debug["action"] = "waiting_followup"
        if rule:
            return _with_llm_reply(
                TurnResult(
                    reply=rule.reply + "\n\nTell me if that resolved it, or if I should file a complaint.",
                    phase="waiting_if_resolved",
                    last_rule_id=rule.id,
                    debug=debug,
                ),
                text,
            )
        return _with_llm_reply(
            TurnResult(
                reply=(
                    "I noted that extra detail. Did the steps above resolve it? "
                    "If not, I can file a complaint."
                ),
                phase="waiting_if_resolved",
                last_rule_id=last_rule_id,
                debug=debug,
            ),
            text,
        )

    if wants_complaint:
        why = (
            "Customer asked to file a complaint."
            if intents["file_complaint"]
            else "Self-serve steps did not resolve the issue."
        )
        ticket = _open_ticket(
            nlu=nlu,
            sentiment=sentiment,
            text=text,
            tried_rules=tried,
            why=why,
            history=history,
        )
        debug["action"] = "ticket_from_request"
        extra = rule.reply if rule else ""
        return _with_llm_reply(
            TurnResult(
                reply=_ticket_reply(ticket, extra=extra),
                phase="ticket_open",
                last_rule_id=rule.id if rule else last_rule_id,
                ticket=ticket,
                debug=debug,
            ),
            text,
        )

    if force_ticket:
        why = (
            "High-risk issue (fraud, identity theft, legal, or foreclosure)."
            if sentiment["high_risk"]
            else f"Rule {rule.id} rarely finishes without a specialist."
        )
        ticket = _open_ticket(
            nlu=nlu,
            sentiment=sentiment,
            text=text,
            tried_rules=tried,
            why=why,
            history=history,
        )
        debug["action"] = "ticket_forced"
        extra = rule.reply if rule else (
            "This looks urgent, so I am not leaving it on self-serve steps only."
        )
        return _with_llm_reply(
            TurnResult(
                reply=_ticket_reply(ticket, extra=extra),
                phase="ticket_open",
                last_rule_id=rule.id if rule else last_rule_id,
                ticket=ticket,
                debug=debug,
            ),
            text,
        )

    if rule:
        debug["action"] = "rule_reply"
        angry_note = ""
        if sentiment["label"] == "angry":
            angry_note = (
                "\n\nYou sound very frustrated. "
                'Say "file a complaint" if you want a formal record.'
            )
        return _with_llm_reply(
            TurnResult(
                reply=rule.reply + angry_note,
                phase="waiting_if_resolved",
                last_rule_id=rule.id,
                debug=debug,
            ),
            text,
        )

    unclear = nlu["category"] == "Unknown" or low_conf
    if unclear and phase != "needs_clarify":
        debug["action"] = "clarify"
        return _with_llm_reply(
            TurnResult(
                reply=(
                    "I didn't catch the issue clearly. Please describe what went wrong "
                    "in a bit more detail — for example a payment that did not post, "
                    "an unexpected fee, or a transfer that has not arrived."
                ),
                phase="needs_clarify",
                last_rule_id=last_rule_id,
                debug=debug,
            ),
            text,
        )

    why = (
        "No self-serve rule matched, and category confidence is low."
        if low_conf or nlu["category"] == "Unknown"
        else "No self-serve rule matched for this category."
    )
    ticket = _open_ticket(
        nlu=nlu,
        sentiment=sentiment,
        text=text,
        tried_rules=tried,
        why=why,
        history=history,
    )
    debug["action"] = "ticket_no_rule"
    return _with_llm_reply(
        TurnResult(
            reply=_ticket_reply(
                ticket,
                extra=(
                    "I read this as a complaint I cannot close with a standard procedure."
                ),
            ),
            phase="ticket_open",
            last_rule_id=last_rule_id,
            ticket=ticket,
            debug=debug,
        ),
        text,
    )
