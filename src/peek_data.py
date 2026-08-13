import pandas as pd

# Ham veri yolu
path = "data/raw/complaints.csv"

# Sadece ilk 5 satiri oku (tum dosyayi degil)
df = pd.read_csv(path, nrows=5)

print("Kolonlar:")
print(df.columns.tolist())
print()
print("Ilk 5 satir:")
print(df)