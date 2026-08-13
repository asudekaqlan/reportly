import pandas as pd

path = "data/raw/complaints.csv"

# Sadece ihtiyacimiz olan 2 kolon
cols = ["Consumer complaint narrative", "Product"]

print("Veri okunuyor (biraz surebilir)...")
df = pd.read_csv(path, usecols=cols)

print("Okunan satir sayisi:", len(df))

# Metni bos olanlari at
df = df.dropna(subset=["Consumer complaint narrative"])
print("Metni olan satir sayisi:", len(df))

# Kolon adlarini sadelestir
df = df.rename(
    columns={
        "Consumer complaint narrative": "text",
        "Product": "category",
    }
)

# Rastgele 5000 ornek al
sample_size = 5000
df_sample = df.sample(n=sample_size, random_state=42)

# Kaydet
out_path = "data/processed/complaints_sample.csv"
df_sample.to_csv(out_path, index=False)

print("Kaydedildi:", out_path)
print("Orneklem satiri:", len(df_sample))
print()
print("Kategori dagilimi:")
print(df_sample["category"].value_counts())
