"""High-severity ITSM phrases. Orchestrator still decides; this is the lexicon."""

from text_norm import fold_tr

FORCE_TICKET_PHRASES = (
    "fidye",
    "ransomware",
    "veri sızıntısı",
    "veri sizintisi",
    "yetkisiz erişim",
    "yetkisiz erisim",
    "phishing",
    "oltalama",
)


def force_ticket(text: str) -> bool:
    lowered = fold_tr(text)
    return any(p in lowered for p in FORCE_TICKET_PHRASES)
