import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score

import joblib
from pathlib import Path

# 1) Temiz veriyi oku
df = pd.read_csv("data/processed/complaints_clean.csv")

# Nadir kategorileri at (en az 20 ornek olsun)
min_count = 20
counts = df["category"].value_counts()
keep = counts[counts >= min_count].index
df = df[df["category"].isin(keep)].copy()

print("Kalan kategori:", df["category"].nunique())
print("Kalan satir:", len(df))

X = df["text"]       # girdi: sikayet metni
y = df["category"]   # cikti: kategori

# 2) Train / test ayir (%80 egitim, %20 sinav)
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y,  # kategorilerin orani train/test'te benzer kalsin
)

print("Train boyutu:", len(X_train))
print("Test boyutu:", len(X_test))

# 3) Metni sayiya cevir (TF-IDF)
vectorizer = TfidfVectorizer(
    max_features=5000,   # en fazla 5000 kelime/ozellik
    ngram_range=(1, 2),  # tek kelime + iki kelimelik ifadeler
    stop_words="english",
)

X_train_vec = vectorizer.fit_transform(X_train)  # train'den kelime sozlugu ogren
X_test_vec = vectorizer.transform(X_test)        # ayni sozlugu teste uygula

# 4) Model egit
model = LogisticRegression(max_iter=1000)
model.fit(X_train_vec, y_train)

# 5) Testte tahmin yap
y_pred = model.predict(X_test_vec)

# 6) Sonuclari olc
acc = accuracy_score(y_test, y_pred)
print("Accuracy:", round(acc, 4))
print()
print(classification_report(y_test, y_pred, zero_division=0))

# 7) Model ve vectorizer'i kaydet
models_dir = Path("models")
models_dir.mkdir(exist_ok=True)

joblib.dump(vectorizer, models_dir / "tfidf_vectorizer.joblib")
joblib.dump(model, models_dir / "logreg_model.joblib")

print("Model kaydedildi: models/")