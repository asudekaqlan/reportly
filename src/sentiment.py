"""Lexicon sentiment: angry vs everyday complaint tone vs calm."""

import re

ANGRY_PHRASES = (
    "furious",
    "lawsuit",
    "attorney",
    "lawyer",
    "stolen",
    "identity theft",
    "harassing",
    "harassment",
    "fed up",
    "ridiculous",
    "worst company",
    "worst experience",
    "disgusting",
    "never again",
    "scam",
    "criminal",
    "sue you",
    "going to sue",
)

CALM_PHRASES = (
    "thank you",
    "thanks",
    "that helps",
    "that helped",
    "appreciate it",
    "understood",
    "sounds good",
    "it's fixed",
    "its fixed",
    "resolved",
    "problem solved",
)

HIGH_RISK_PHRASES = (
    "fraud",
    "identity theft",
    "stolen",
    "lawsuit",
    "attorney",
    "foreclosure",
    "unauthorized",
)


def _contains_phrase(text: str, phrases: tuple[str, ...]) -> list[str]:
    lowered = f" {text.lower()} "
    hits = []
    for phrase in phrases:
        if phrase in lowered:
            hits.append(phrase)
    return hits


def analyze_sentiment(text: str) -> dict:
    raw = text or ""
    angry_hits = _contains_phrase(raw, ANGRY_PHRASES)
    calm_hits = _contains_phrase(raw, CALM_PHRASES)
    risk_hits = _contains_phrase(raw, HIGH_RISK_PHRASES)

    if angry_hits and not calm_hits:
        label = "angry"
    elif calm_hits and not angry_hits:
        label = "calm"
    else:
        label = "negative"

    return {
        "label": label,
        "angry_hits": angry_hits,
        "calm_hits": calm_hits,
        "high_risk": bool(risk_hits),
        "risk_hits": risk_hits,
    }


def looks_positive_resolution(text: str) -> bool:
    return bool(_contains_phrase(text or "", CALM_PHRASES)) or bool(
        re.search(r"\b(ok|okay|got it|all good)\b", (text or "").lower())
    )
