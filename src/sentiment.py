"""Lexicon sentiment: angry vs everyday complaint tone vs calm."""

import re

from text_norm import fold_tr

ANGRY_PHRASES = (
    "bıktım",
    "biktım",
    "bıktim",
    "rezalet",
    "yazıklar olsun",
    "yaziklar olsun",
    "dava açacağım",
    "dava acacagim",
    "avukat",
    "dolandırıcılık",
    "dolandiricilik",
    "sahtekâr",
    "sahtekar",
    "tehdit",
    "asla bir daha",
    "en kötü",
    "en kotu",
    "skandal",
    "i̇ğrenç",
    "iğrenç",
    "igrenc",
    "suç",
    "suc",
)

CALM_PHRASES = (
    "teşekkür",
    "tesekkur",
    "sağ ol",
    "sag ol",
    "işe yaradı",
    "ise yaradi",
    "düzeldi",
    "duzeldi",
    "çözüldü",
    "cozuldu",
    "anladım",
    "anladim",
    "tamamdır",
)

HIGH_RISK_PHRASES = (
    "dolandırıcılık",
    "dolandiricilik",
    "sahtekarlık",
    "sahtekarlik",
    "izinsiz çekim",
    "izinsiz cekim",
    "dava",
    "avukat",
    "icra",
    "tehdit",
    "kimlik hırsız",
    "kimlik hirsiz",
)


def _contains_phrase(text: str, phrases: tuple[str, ...]) -> list[str]:
    lowered = f" {fold_tr(text)} "
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
        re.search(r"\b(ok|okay|tamam)\b", fold_tr(text or ""))
    )
