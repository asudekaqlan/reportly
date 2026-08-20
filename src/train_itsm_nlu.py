"""Train a small ITSM süreç classifier (TF-IDF + logreg).

    python src/train_itsm_nlu.py
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
import sys

SRC = Path(__file__).resolve().parent
ROOT = SRC.parent
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

from taxonomy import PATHS
from text_norm import fold_tr

CSV_PATH = ROOT / "data" / "itsm_siniflandirma.csv"

# CSV süreç labels that overlap the prototype's 9 surec ids. Other rows are skipped.
CSV_SUREC_MAP: dict[str, str] = {
    "Bilgisayar Arıza/Onarım Talebi": "donanim_ariza",
    "İnternet Bağlantı Sorunu": "ag_kesintisi",
    "VPN Erişim Sorunu": "ag_kesintisi",
    "Wi-Fi Bağlantı Talebi": "ag_kesintisi",
    "Yazılım Hata/Arıza Bildirimi": "yazilim_hatasi",
    "Yazılım Güncelleme Talebi": "yazilim_hatasi",
    "Şifre Sıfırlama Talebi": "sifre_sifirlama",
    "Yetki/Sistem Erişim Talebi": "yetki_talebi",
    "Yeni Kullanıcı Hesabı Açma": "yetki_talebi",
    "Yazıcı Kurulum Talebi": "yeni_cihaz",
    "Yeni Ekipman Talebi": "yeni_cihaz",
    "Mobil Cihaz Talebi": "yeni_cihaz",
    "Ekipman Değişim/Yükseltme Talebi": "yeni_cihaz",
    "Yazılım Kurulum/Lisans Talebi": "yeni_cihaz",
    "Yazıcı Arıza Bildirimi": "yazici_ariza",
    "Toner/Kartuş Talebi": "yazici_ariza",
    "Yıllık İzin Talebi": "izin_bilgisi",
    "İzin İptal/Değişiklik Talebi": "izin_bilgisi",
    "Bordro/Maaş Bilgisi Talebi": "izin_bilgisi",
    "Maaş Hatası Bildirimi": "izin_bilgisi",
    "Özlük Belgesi Talebi": "izin_bilgisi",
    "Rapor/Sağlık İzni Bildirimi": "izin_bilgisi",
}

TEMPLATES = (
    "{kw}",
    "{kw} var",
    "{kw} sorunum var",
    "{kw} çalışmıyor",
    "{kw} calismiyor",
    "talep açmak istiyorum {kw}",
    "{kw} için ticket aç",
    "yardım {kw}",
    "{kw} bozuldu",
)

EXTRA: dict[str, tuple[str, ...]] = {
    "donanim_ariza": (
        "pc açılmıyor",
        "notebook siyah ekran",
        "bilgisayarım açılmıyo",
        "cihaz ısınmıyor açılmıyor",
        "mavi ekran verdi laptop",
    ),
    "ag_kesintisi": (
        "vpn düşüyor",
        "wifi yok ofiste",
        "internet koptu",
        "ağa bağlanamıyorum",
    ),
    "yazilim_hatasi": (
        "teams açılmıyor",
        "excel hata verdi",
        "program çöktü",
        "uygulama dondu",
    ),
    "sifre_sifirlama": (
        "parolamı unuttum",
        "hesap kilitlendi giriş yok",
        "şifre sıfırlama lazım",
    ),
    "yetki_talebi": (
        "klasöre erişim istiyorum",
        "paylaşım yetkisi yok",
        "drive izni verin",
    ),
    "yeni_cihaz": (
        "yeni laptop kurulumu",
        "bilgisayar format atın",
        "yazıcı kurulumu istiyorum",
    ),
    "yazici_ariza": (
        "printer basmıyor",
        "fotokopi sıkıştı",
        "kat yazıcısı çalışmıyor",
    ),
    "izin_bilgisi": (
        "kaç gün iznim kaldı",
        "maaş bordrosu nerede",
        "özlük bilgilerim",
    ),
    "masraf_talebi": (
        "avans talebim var",
        "fatura ödenmedi",
        "harcama formu",
    ),
}


def _keyword_examples() -> tuple[list[str], list[str]]:
    texts: list[str] = []
    labels: list[str] = []
    for path in PATHS:
        for keyword in path.keywords:
            for template in TEMPLATES:
                texts.append(fold_tr(template.format(kw=keyword)))
                labels.append(path.surec)
        for extra in EXTRA.get(path.surec, ()):
            texts.append(fold_tr(extra))
            labels.append(path.surec)
    return texts, labels


def _csv_examples() -> tuple[list[str], list[str], int, int]:
    if not CSV_PATH.exists():
        print("No CSV at", CSV_PATH)
        return [], [], 0, 0
    mapped: list[tuple[str, str]] = []
    total = 0
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            total += 1
            surec = CSV_SUREC_MAP.get((row.get("surec_talep_tipi") or "").strip())
            text = fold_tr(row.get("talep_metni") or "")
            if not surec or not text:
                continue
            mapped.append((text, surec))
    unique = list(dict.fromkeys(mapped))
    texts = [item[0] for item in unique]
    labels = [item[1] for item in unique]
    return texts, labels, total, len(mapped)


def _examples() -> tuple[list[str], list[str]]:
    texts, labels = _keyword_examples()
    csv_texts, csv_labels, csv_total, csv_mapped = _csv_examples()
    print(
        f"CSV rows: {csv_total} mapped: {csv_mapped} unique: {len(csv_texts)} "
        f"skipped: {csv_total - csv_mapped}"
    )
    if csv_labels:
        print("CSV class counts:", dict(Counter(csv_labels)))
    texts.extend(csv_texts)
    labels.extend(csv_labels)
    return texts, labels


def main() -> None:
    texts, labels = _examples()
    print("Examples:", len(texts), "classes:", len(set(labels)))
    x_train, x_test, y_train, y_test = train_test_split(
        texts,
        labels,
        test_size=0.2,
        random_state=42,
        stratify=labels,
    )
    vectorizer = TfidfVectorizer(max_features=4000, ngram_range=(1, 2), min_df=1)
    x_train_vec = vectorizer.fit_transform(x_train)
    x_test_vec = vectorizer.transform(x_test)
    model = LogisticRegression(max_iter=1000)
    model.fit(x_train_vec, y_train)
    pred = model.predict(x_test_vec)
    print("Accuracy:", round(accuracy_score(y_test, pred), 4))
    print(classification_report(y_test, pred, zero_division=0))
    models_dir = ROOT / "models"
    models_dir.mkdir(exist_ok=True)
    joblib.dump(vectorizer, models_dir / "itsm_tfidf.joblib")
    joblib.dump(model, models_dir / "itsm_logreg.joblib")
    print("Saved models/itsm_tfidf.joblib and models/itsm_logreg.joblib")


if __name__ == "__main__":
    main()
