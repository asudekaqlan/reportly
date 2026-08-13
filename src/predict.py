import joblib
from pathlib import Path

# 1) Load saved model and vectorizer
models_dir = Path("models")
vectorizer = joblib.load(models_dir / "tfidf_vectorizer.joblib")
model = joblib.load(models_dir / "logreg_model.joblib")

# 2) Complaint text to predict
text = input("Enter complaint text: ").strip()

if not text:
    print("Empty text entered.")
    raise SystemExit

# 3) Convert with the same TF-IDF
X = vectorizer.transform([text])

# 4) Predict
pred = model.predict(X)[0]

# 5) Optional probabilities
proba = model.predict_proba(X)[0]
confidence = max(proba)

print("Text:", text)
print("Predicted category:", pred)
print("Confidence:", round(confidence, 3))
