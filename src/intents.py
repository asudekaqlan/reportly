"""Keyword intents on top of category: file a complaint, still broken."""

FILE_COMPLAINT_PHRASES = (
    "file a complaint",
    "open a complaint",
    "create a complaint",
    "open a ticket",
    "create a ticket",
    "i want to complain",
    "file a formal",
    "speak to a manager",
    "talk to a manager",
)

STILL_UNRESOLVED_PHRASES = (
    "didn't work",
    "did not work",
    "didn't help",
    "did not help",
    "still the same",
    "not resolved",
    "that didn't",
    "no luck",
    "nothing changed",
    "still broken",
    "still wrong",
    "that didn't fix",
    "still happening",
)


def _hits(text: str, phrases: tuple[str, ...]) -> list[str]:
    lowered = (text or "").lower()
    return [p for p in phrases if p in lowered]


def detect_intents(text: str) -> dict:
    file_complaint = _hits(text, FILE_COMPLAINT_PHRASES)
    still_unresolved = _hits(text, STILL_UNRESOLVED_PHRASES)
    return {
        "file_complaint": bool(file_complaint),
        "still_unresolved": bool(still_unresolved),
        "hits": {
            "file_complaint": file_complaint,
            "still_unresolved": still_unresolved,
        },
    }
