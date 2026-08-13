import pandas as pd
import re

# 1) Orneklemi oku
path = "data/processed/complaints_sample.csv"
df = pd.read_csv(path)

print("Satir sayisi:", len(df))
print("Kolonlar:", df.columns.tolist())
print()

# 2) Eksik deger var mi?
print("Eksik degerler:")
print(df.isna().sum())
print()

# 3) Kategori dagilimi
print("Kategori sayisi:", df["category"].nunique())
print(df["category"].value_counts().head(10))
print()

# 4) Ornek bir metne bak
print("Ornek metin (ilk satir):")
print(df.loc[0, "text"][:300])
print()


def clean_text(text):
    """Metni modele daha uygun hale getirir."""
    text = str(text)              # her sey string olsun
    text = text.lower()           # kucuk harf
    text = re.sub(r"\s+", " ", text)  # fazla bosluklari tek bosluga indir
    text = text.strip()           # bas/sondaki bosluklari sil
    return text


# 5) Temizligi uygula
df["text_clean"] = df["text"].apply(clean_text)

# 6) Kaydet
out_path = "data/processed/complaints_clean.csv"
df[["text_clean", "category"]].rename(
    columns={"text_clean": "text"}
).to_csv(out_path, index=False)

print("Temiz veri kaydedildi:", out_path)
print("Temiz ornek:")
print(df.loc[0, "text_clean"][:300])