import joblib
from pathlib import Path

# 1) Kayitli model ve vectorizer'i yukle
models_dir = Path("models")
vectorizer = joblib.load(models_dir / "tfidf_vectorizer.joblib")
model = joblib.load(models_dir / "logreg_model.joblib")

# 2) Tahmin edilecek ornek metin
text = input("Sikayet metnini yaz: ").strip()

if not text:
    print("Bos metin girdin.")
    raise SystemExit

# 3) Ayni TF-IDF ile sayiya cevir
X = vectorizer.transform([text])

# 4) Tahmin
pred = model.predict(X)[0]

# 5) (Istege bagli) olasiliklar
proba = model.predict_proba(X)[0]
confidence = max(proba)

print("Metin:", text)
print("Tahmin kategori:", pred)
print("Guven skoru:", round(confidence, 3))