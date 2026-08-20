"""Turkish-aware lowercase for keyword matching."""


def fold_tr(text: str) -> str:
    table = str.maketrans(
        {
            "I": "ı",
            "İ": "i",
            "Ş": "ş",
            "Ğ": "ğ",
            "Ü": "ü",
            "Ö": "ö",
            "Ç": "ç",
            "Â": "a",
            "Î": "i",
            "Û": "u",
        }
    )
    return (text or "").translate(table).lower()
