"""Chat intents: open ticket, solution failed, confirm, reporting."""

from text_norm import fold_tr

OPEN_TICKET_PHRASES = (
    "ticket aç",
    "talep aç",
    "kayıt aç",
    "kayit ac",
    "iş kaydı",
    "is kaydi",
    "şikayet aç",
    "sikayet ac",
    "oluştur",
    "olustur",
)

STILL_UNRESOLVED_PHRASES = (
    "işe yaramadı",
    "ise yaramadi",
    "yaramadı",
    "çözülmedi",
    "cozulmedi",
    "düzelmedi",
    "hala aynı",
    "hala ayni",
    "yine olmadı",
    "yine olmadi",
)

CONFIRM_PHRASES = (
    "evet",
    "isterim",
    "istiyorum",
    "olur",
    "tamam",
    "lütfen",
    "lutfen",
    "yapalım",
    "yapalim",
    "ok",
    "okay",
)

DECLINE_PHRASES = (
    "hayır",
    "hayir",
    "istemiyorum",
    "gerek yok",
    "lazım değil",
    "lazim degil",
    "vazgeç",
    "vazgec",
)


def _hits(text: str, phrases: tuple[str, ...]) -> list[str]:
    lowered = fold_tr(text)
    return [p for p in phrases if p in lowered]


def looks_confirm(text: str) -> bool:
    return bool(_hits(text, CONFIRM_PHRASES))


def looks_decline(text: str) -> bool:
    lowered = fold_tr(text)
    if any(p in lowered for p in DECLINE_PHRASES):
        if "evet" in lowered or "istiyorum" in lowered:
            return False
        return True
    return False


def detect_intents(text: str) -> dict:
    open_ticket = _hits(text, OPEN_TICKET_PHRASES)
    still_unresolved = _hits(text, STILL_UNRESOLVED_PHRASES)
    return {
        "open_ticket": bool(open_ticket),
        "still_unresolved": bool(still_unresolved),
        "hits": {
            "open_ticket": open_ticket,
            "still_unresolved": still_unresolved,
        },
    }
