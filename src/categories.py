"""Issue-type labels for Turkish consumer reviews.

The Hugging Face set has no category column. Labels are assigned with
keyword scores (weak supervision), then the TF-IDF model copies them.
"""

from __future__ import annotations

from text_norm import fold_tr

# Stable ids used by the classifier, rules, tickets, and debug UI.
CATEGORIES: tuple[str, ...] = (
    "kargo_teslimat",
    "siparis_eksik",
    "iptal_iade",
    "fatura_ucret",
    "kusurlu_urun",
    "abonelik_uyelik",
    "odeme_kart",
    "hizmet_erisim",
    "diger",
)

# Longer / more specific phrases first. Score = number of hits.
_LABEL_KEYWORDS: dict[str, tuple[str, ...]] = {
    "kargo_teslimat": (
        "teslim edilmedi",
        "teslim etmedi",
        "teslim edilmeyen",
        "teslim edilmiyor",
        "ulaştırılmayan",
        "kargo gelmedi",
        "kargom gelmedi",
        "dağıtıma çıkmıyor",
        "kargo şube",
        "kargo sube",
        "yurtiçi kargo",
        "yurtici kargo",
        "sürat kargo",
        "surat kargo",
        "aras kargo",
        "mng kargo",
        "ups türkiye",
        "ups turkiye",
        "kargoya verildi",
        "kargoda görünüyor",
        "kargoda gorunuyor",
        "kargom",
        "kargo",
    ),
    "siparis_eksik": (
        "eksik ürün",
        "eksik urun",
        "eksik gönder",
        "eksik gonder",
        "yanlış ürün",
        "yanlis urun",
        "yanlış geldi",
        "yanlis geldi",
        "yanlış gönder",
        "hala hazırlanıyor",
        "hala hazirlaniyor",
        "tedarik sürec",
        "tedarik surec",
        "siparişim gelmedi",
        "siparisim gelmedi",
        "elime ulaşmadı",
        "elime ulasmadi",
        "ürünüm gelmedi",
        "urunum gelmedi",
        "sipariş",
        "siparis",
    ),
    "iptal_iade": (
        "ücret iadesi",
        "ucret iadesi",
        "para iadesi",
        "iade yapılmıyor",
        "iade yapilmiyor",
        "iade edilmedi",
        "iademi alamıyorum",
        "iademi alamiyorum",
        "paramı alamıyorum",
        "parami alamiyorum",
        "iade talebi",
        "iptal hakk",
        "sipariş iptal",
        "siparis iptal",
        "üyelik iptal",
        "uyelik iptal",
        "iade",
        "iptal",
    ),
    "fatura_ucret": (
        "fazla fatura",
        "fatura abart",
        "yüksek fatura",
        "yuksek fatura",
        "haksız kesinti",
        "haksiz kesinti",
        "güvence bedeli",
        "guvence bedeli",
        "tahsis ücret",
        "tahsis ucret",
        "yıllık ücret",
        "yillik ucret",
        "faturam",
        "fatura",
        "kesinti",
    ),
    "kusurlu_urun": (
        "teknik servis",
        "servis çözmedi",
        "servis cozmedi",
        "koku yapıyor",
        "koku yapiyor",
        "arıza",
        "ariza",
        "bozuk",
        "kusurlu",
        "defolu",
        "çalışmıyor",
        "calismiyor",
        "montaj",
        "garanti",
        "servis",
        "tamir",
        "kırık",
        "kirik",
        "hasarlı",
        "hasarli",
        "küflü",
        "kuflu",
        "sızdır",
        "sizdir",
        "akıtıyor",
        "akitiyor",
        "lekelen",
        "çökme",
        "cokme",
        "kalitesiz",
        "yazılımsal",
        "yazilimsal",
        "donuyor",
        "kapanıyor",
        "kapaniyor",
    ),
    "abonelik_uyelik": (
        "üyeliğimi dondur",
        "uyeligimi dondur",
        "abonelik iptal",
        "üyelik iptal",
        "uyelik iptal",
        "spor merkezi",
        "üyelik",
        "uyelik",
        "abonelik",
        "aidat",
        "taahhüt",
        "taahhut",
    ),
    "odeme_kart": (
        "kredi kart",
        "kartımı iptal",
        "kartimi iptal",
        "sormadan iptal",
        "izinsiz çekim",
        "izinsiz cekim",
        "habersiz çekim",
        "hesabımdan para",
        "hesabimdan para",
        "kredi tahsis",
        "kredi başvuru",
        "kredi basvuru",
        "hukuk bürosu",
        "hukuk burosu",
        "borç",
        "borc",
        "icra",
        "avukat",
        "banka",
        "kart",
    ),
    "hizmet_erisim": (
        "müşteri hizmet",
        "musteri hizmet",
        "ulaşamıyorum",
        "ulasamiyorum",
        "ulaşamıyoruz",
        "geri dönüş yok",
        "geri donus yok",
        "arayan yok",
        "randevu",
        "ilgisiz",
        "telefonlarıma",
        "telefonlarima",
        "bağlanamıyorum",
        "baglanamiyorum",
        "dönüş yapılmıyor",
        "donus yapilmiyor",
    ),
}

# If two labels tie, prefer the more specific issue type.
_TIE_BREAK: tuple[str, ...] = (
    "kargo_teslimat",
    "iptal_iade",
    "kusurlu_urun",
    "fatura_ucret",
    "abonelik_uyelik",
    "odeme_kart",
    "hizmet_erisim",
    "siparis_eksik",
    "diger",
)


def keyword_hits(text: str, phrases: tuple[str, ...]) -> list[str]:
    folded = fold_tr(text)
    return [phrase for phrase in phrases if phrase in folded]


def assign_category(text: str, min_score: int = 1) -> str:
    """Return the best weak label, or `diger`."""
    best_label = "diger"
    best_score = 0
    for label, phrases in _LABEL_KEYWORDS.items():
        score = len(keyword_hits(text, phrases))
        if score > best_score:
            best_score = score
            best_label = label
        elif score == best_score and score > 0:
            if _TIE_BREAK.index(label) < _TIE_BREAK.index(best_label):
                best_label = label
    if best_score < min_score:
        return "diger"
    return best_label
