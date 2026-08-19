"""Template manager brief and record notes. LLM is optional copy only."""

import os
from typing import Iterable


def _trim(text: str, limit: int = 220) -> str:
    cleaned = " ".join((text or "").split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1] + "…"


def conversation_excerpt(history: Iterable[dict], latest_user: str, limit: int = 8) -> str:
    lines = []
    for message in list(history)[-limit:]:
        role = "Customer" if message.get("role") == "user" else "Assistant"
        lines.append(f"{role}: {_trim(str(message.get('content', '')), 320)}")
    lines.append(f"Customer: {_trim(latest_user, 320)}")
    return "\n".join(lines)


def llm_enabled() -> bool:
    return os.environ.get("ASSISTANT_USE_LLM", "").strip() == "1"


def build_summary(
    *,
    category: str,
    sentiment: str,
    customer_ask: str,
    tried_rules: list[str],
    why_unresolved: str,
    high_risk: bool,
) -> dict:
    bullets = [
        f"{category} · tone {sentiment}.",
        _trim(customer_ask, 160) or "No extra detail.",
    ]
    if high_risk:
        bullets.append("High-risk (fraud / ID theft / legal / foreclosure). " + why_unresolved)
    elif tried_rules:
        bullets.append("Self-serve already tried: " + ", ".join(tried_rules) + ". " + why_unresolved)
    else:
        bullets.append("No rule matched. " + why_unresolved)

    if high_risk:
        next_step = "Same-day verify and call the customer."
    elif tried_rules:
        next_step = "See why self-serve failed; fix the account; call back."
    else:
        next_step = "Triage, ask for missing docs, send one clear next action."

    return {
        "summary_bullets": bullets[:3],
        "recommended_next_step": next_step,
    }


def build_handoff_notes(
    *,
    category: str,
    sentiment: str,
    why_unresolved: str,
    history: Iterable[dict],
    latest_user: str,
) -> str:
    excerpt = conversation_excerpt(history, latest_user)
    return (
        f"Record notes. Category: {category}. Sentiment: {sentiment}. "
        f"Reason: {why_unresolved}\n\nRecent thread:\n{excerpt}"
    )


def build_manager_copy(
    *,
    category: str,
    sentiment: str,
    customer_ask: str,
    tried_rules: list[str],
    why_unresolved: str,
    high_risk: bool,
    history: Iterable[dict],
    latest_user: str,
) -> dict:
    """Brief + notes. Optional LLM rewrites copy; next step stays templated."""
    brief = build_summary(
        category=category,
        sentiment=sentiment,
        customer_ask=customer_ask,
        tried_rules=tried_rules,
        why_unresolved=why_unresolved,
        high_risk=high_risk,
    )
    notes = build_handoff_notes(
        category=category,
        sentiment=sentiment,
        why_unresolved=why_unresolved,
        history=history,
        latest_user=latest_user,
    )
    if llm_enabled():
        from llm_analyze import generate_record_copy

        llm = generate_record_copy(
            category=category,
            sentiment=sentiment,
            customer_ask=customer_ask,
            tried_rules=tried_rules,
            why_unresolved=why_unresolved,
            high_risk=high_risk,
            thread_excerpt=conversation_excerpt(history, latest_user),
        )
        if llm:
            brief["summary_bullets"] = llm["summary_bullets"]
            notes = llm["handoff_notes"]
    return {
        "summary_bullets": brief["summary_bullets"],
        "recommended_next_step": brief["recommended_next_step"],
        "handoff_notes": notes,
    }
