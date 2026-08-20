"""Fill required ITSM ticket fields from chat text."""

from __future__ import annotations

import re

from text_norm import fold_tr

REQUIRED_FIELDS = ("asset", "location", "impact")

FIELD_PROMPTS = {
    "asset": "Hangi cihaz veya varlık bu? (ör. laptop, yazıcı, kullanıcı hesabı)",
    "location": "Neredesin / ekipman nerede? (ör. 3. kat, İstanbul ofis, uzaktan)",
    "impact": "Kimleri etkiliyor? (yalnız ben / ekibim / tüm ofis)",
}

_ASSET_HINTS = (
    "laptop",
    "dizüstü",
    "dizustu",
    "masaüstü",
    "masaustu",
    "bilgisayar",
    "yazıcı",
    "yazici",
    "telefon",
    "hesap",
    "outlook",
    "vpn",
    "monitör",
    "monitor",
)

_LOCATION_RE = re.compile(
    r"(\d+\.\s*kat|istanbul|ankara|izmir|ofis|uzaktan|evden|toplanti odasi|toplantı)",
    re.I,
)

_IMPACT_MAP = (
    (("tüm ofis", "tum ofis", "herkes", "bütün kat", "butun kat"), "tüm ofis"),
    (("ekibim", "ekip", "takım", "takim"), "ekibim"),
    (("yalnız", "yalniz", "sadece ben", "beni"), "yalnız ben"),
)


def empty_slots() -> dict[str, str]:
    return {key: "" for key in REQUIRED_FIELDS}


def merge_slots(current: dict | None, incoming: dict | None) -> dict[str, str]:
    slots = empty_slots()
    for key in REQUIRED_FIELDS:
        slots[key] = str((current or {}).get(key) or (incoming or {}).get(key) or "").strip()
    return slots


def extract_slots(text: str) -> dict[str, str]:
    raw = text or ""
    lowered = fold_tr(raw)
    found = empty_slots()
    for hint in _ASSET_HINTS:
        if hint in lowered:
            found["asset"] = hint
            break
    loc = _LOCATION_RE.search(raw) or _LOCATION_RE.search(lowered)
    if loc:
        found["location"] = loc.group(0)
    for phrases, label in _IMPACT_MAP:
        if any(p in lowered for p in phrases):
            found["impact"] = label
            break
    return found


def missing_fields(slots: dict[str, str]) -> list[str]:
    return [key for key in REQUIRED_FIELDS if not str(slots.get(key) or "").strip()]


def apply_answer(slots: dict[str, str], field: str, text: str) -> dict[str, str]:
    updated = merge_slots(slots, None)
    extracted = extract_slots(text)
    if field in REQUIRED_FIELDS:
        value = extracted.get(field) or " ".join((text or "").split())
        if value:
            updated[field] = value[:120]
    for key, value in extracted.items():
        if value and not updated[key]:
            updated[key] = value
    return updated


def next_prompt(slots: dict[str, str]) -> str | None:
    missing = missing_fields(slots)
    if not missing:
        return None
    return FIELD_PROMPTS[missing[0]]
