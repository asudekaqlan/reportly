"""ITSM classification: Talep → Birim → Modül → Süreç/Talep tipi."""

from __future__ import annotations

from dataclasses import dataclass

from text_norm import fold_tr


@dataclass(frozen=True)
class TaxonomyPath:
    talep_turu: str
    talep_turu_label: str
    birim: str
    birim_label: str
    modul: str
    modul_label: str
    surec: str
    surec_label: str
    keywords: tuple[str, ...]
    clarify_hint: str


PATHS: tuple[TaxonomyPath, ...] = (
    TaxonomyPath(
        "ariza",
        "Arıza (Incident)",
        "it_destek",
        "IT Destek",
        "uc_birim",
        "Uç birim",
        "donanim_ariza",
        "Donanım arızası",
        (
            "bilgisayar",
            "laptop",
            "dizüstü",
            "dizustu",
            "masaüstü",
            "masaustu",
            "bozuldu",
            "açılmıyor",
            "acilmiyor",
            "açılmiyor",
            "açılmıyo",
            "acilmiyo",
            "açılmiyo",
            "açilmiyo",
            "bozuluyo",
            "ekran",
            "klavye",
            "donuyor",
            "mavi ekran",
            "cihaz",
        ),
        "Cihaz mı (laptop/masaüstü), yoksa yazıcı veya monitör mü?",
    ),
    TaxonomyPath(
        "ariza",
        "Arıza (Incident)",
        "it_destek",
        "IT Destek",
        "ag",
        "Ağ",
        "ag_kesintisi",
        "Ağ / VPN kesintisi",
        (
            "internet",
            "ağ",
            "ag",
            "wifi",
            "wi-fi",
            "vpn",
            "bağlanamıyorum",
            "baglanamiyorum",
            "kopuyor",
            "yavaş",
            "yavas",
            "kesildi",
        ),
        "Ofis ağı mı, VPN mi, yoksa sadece bir uygulama mı açılmıyor?",
    ),
    TaxonomyPath(
        "ariza",
        "Arıza (Incident)",
        "it_destek",
        "IT Destek",
        "yazilim",
        "Yazılım",
        "yazilim_hatasi",
        "Uygulama hatası",
        (
            "outlook",
            "excel",
            "teams",
            "uygulama",
            "yazılım",
            "yazilim",
            "hata veriyor",
            "çöktü",
            "coktu",
            "açılmıyor program",
        ),
        "Hangi uygulama? Hata metnini paylaşabilir misin?",
    ),
    TaxonomyPath(
        "hizmet_talebi",
        "Hizmet talebi",
        "it_destek",
        "IT Destek",
        "erisim",
        "Hesap / erişim",
        "sifre_sifirlama",
        "Şifre sıfırlama",
        (
            "şifre",
            "sifre",
            "parola",
            "unuttum",
            "kilitlendi",
            "hesabım",
            "hesabim",
            "giriş yapamıyorum",
            "giris yapamiyorum",
        ),
        "Şirket hesabı mı, VPN mi, yoksa bir uygulama şifresi mi?",
    ),
    TaxonomyPath(
        "hizmet_talebi",
        "Hizmet talebi",
        "it_destek",
        "IT Destek",
        "erisim",
        "Hesap / erişim",
        "yetki_talebi",
        "Yetki / erişim talebi",
        (
            "yetki",
            "erişim",
            "erisim",
            "klasör",
            "klasor",
            "paylaşım",
            "paylasim",
            "izin ver",
            "ekip drive",
        ),
        "Hangi klasör veya sistem için yetki istiyorsun?",
    ),
    TaxonomyPath(
        "hizmet_talebi",
        "Hizmet talebi",
        "it_destek",
        "IT Destek",
        "uc_birim",
        "Uç birim",
        "yeni_cihaz",
        "Yeni cihaz / kurulum",
        (
            "yeni laptop",
            "yeni bilgisayar",
            "kurulum",
            "format",
            "yazıcı kurulumu",
            "yazici kurulumu",
        ),
        "Yeni cihaz mı, mevcut cihaza yazılım kurulumu mu?",
    ),
    TaxonomyPath(
        "ariza",
        "Arıza (Incident)",
        "tesis",
        "Tesis / İdari işler",
        "ofis",
        "Ofis",
        "yazici_ariza",
        "Yazıcı / ofis ekipmanı",
        (
            "yazıcı",
            "yazici",
            "printer",
            "basmıyor",
            "basmiyor",
            "kağıt sıkıştı",
            "kagit sikisti",
            "fotokopi",
        ),
        "Hangi kat / hangi yazıcı?",
    ),
    TaxonomyPath(
        "bilgi",
        "Bilgi talebi",
        "ik",
        "İnsan Kaynakları",
        "bordro",
        "Özlük / bordro",
        "izin_bilgisi",
        "İzin / özlük bilgisi",
        (
            "izin",
            "yıllık izin",
            "yillik izin",
            "bordro",
            "maaş",
            "maas",
            "özlük",
            "ozluk",
        ),
        "İzin bakiyesi mi, bordro mu, yoksa başka bir özlük konusu mu?",
    ),
    TaxonomyPath(
        "hizmet_talebi",
        "Hizmet talebi",
        "finans",
        "Finans",
        "odeme",
        "Ödeme / masraf",
        "masraf_talebi",
        "Masraf / fatura",
        (
            "masraf",
            "fatura",
            "ödeme",
            "odeme",
            "avans",
            "harcama",
        ),
        "Masraf formu mu, fatura mı, yoksa ödeme takibi mi?",
    ),
)


# One distinctive word is enough (user often answers "laptop" / "cihaz").
STRONG_KEYWORDS = {
    "laptop",
    "bilgisayar",
    "dizüstü",
    "dizustu",
    "masaüstü",
    "masaustu",
    "cihaz",
    "vpn",
    "wifi",
    "internet",
    "şifre",
    "sifre",
    "parola",
    "outlook",
    "teams",
    "excel",
    "yazıcı",
    "yazici",
    "printer",
    "yetki",
    "izin",
    "bordro",
    "masraf",
}


def _hits(text: str, keywords: tuple[str, ...]) -> list[str]:
    lowered = fold_tr(text)
    return [kw for kw in keywords if kw in lowered]


def path_by_surec(surec: str) -> TaxonomyPath | None:
    for path in PATHS:
        if path.surec == surec:
            return path
    return None


def _from_path(
    path: TaxonomyPath,
    score: float,
    hits: list[str],
    source: str,
    *,
    model_confidence: float = 0.0,
) -> dict:
    return {
        "unclear": False,
        "score": score,
        "hits": hits,
        "source": source,
        "model_confidence": model_confidence,
        "talep_turu": path.talep_turu,
        "talep_turu_label": path.talep_turu_label,
        "birim": path.birim,
        "birim_label": path.birim_label,
        "modul": path.modul,
        "modul_label": path.modul_label,
        "surec": path.surec,
        "surec_label": path.surec_label,
        "path_label": (
            f"{path.talep_turu_label} → {path.birim_label} → "
            f"{path.modul_label} → {path.surec_label}"
        ),
        "clarify_hint": path.clarify_hint,
    }


def classify_request(text: str, min_score: int = 2) -> dict:
    """Keyword path first; small TF-IDF model if keywords are unclear."""
    best: TaxonomyPath | None = None
    best_score = 0
    best_hits: list[str] = []
    for path in PATHS:
        hits = _hits(text, path.keywords)
        score = len(hits)
        if any(fold_tr(h) in STRONG_KEYWORDS or h in STRONG_KEYWORDS for h in hits):
            score += 1
        if score > best_score:
            best_score = score
            best = path
            best_hits = hits
    if best is not None and best_score >= min_score:
        return _from_path(best, best_score, best_hits, "keyword")

    from itsm_nlu import predict_surec

    pred = predict_surec(text)
    modeled = path_by_surec(str(pred.get("surec") or ""))
    if modeled is not None:
        return _from_path(
            modeled,
            max(best_score, min_score),
            best_hits,
            "model",
            model_confidence=float(pred.get("confidence") or 0.0),
        )

    return {
        "unclear": True,
        "score": best_score,
        "hits": best_hits,
        "source": "none",
        "model_confidence": float(pred.get("confidence") or 0.0),
        "talep_turu": "",
        "talep_turu_label": "",
        "birim": "",
        "birim_label": "",
        "modul": "",
        "modul_label": "",
        "surec": "",
        "surec_label": "",
        "path_label": "",
        "clarify_hint": (
            best.clarify_hint
            if best
            else "Cihaz, ağ, yazılım, erişim veya başka bir birim mi?"
        ),
    }


def path_line(classification: dict | None) -> str:
    if not classification or classification.get("unclear"):
        return "sınıf henüz net değil"
    return str(classification.get("path_label") or "")
