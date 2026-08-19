import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score

import joblib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 1) Load cleaned data
df = pd.read_csv(ROOT / "data" / "processed" / "complaints_clean.csv")

# Drop rare categories (keep classes with at least 20 samples)
min_count = 20
counts = df["category"].value_counts()
keep = counts[counts >= min_count].index
df = df[df["category"].isin(keep)].copy()

print("Remaining categories:", df["category"].nunique())
print("Remaining rows:", len(df))

X = df["text"]  # input: complaint text
y = df["category"]  # output: category

# 2) Train / test split (80% train, 20% test)
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y,  # keep category ratios similar in train/test
)

print("Train size:", len(X_train))
print("Test size:", len(X_test))

# 3) Convert text to numbers (TF-IDF)
vectorizer = TfidfVectorizer(
    max_features=5000,  # at most 5000 features
    ngram_range=(1, 2),  # unigrams + bigrams
    stop_words="english",
)

X_train_vec = vectorizer.fit_transform(X_train)  # learn vocab on train
X_test_vec = vectorizer.transform(X_test)  # apply same vocab to test

# 4) Train model
model = LogisticRegression(max_iter=1000)
model.fit(X_train_vec, y_train)

# 5) Predict on test set
y_pred = model.predict(X_test_vec)

# 6) Evaluate
acc = accuracy_score(y_test, y_pred)
print("Accuracy:", round(acc, 4))
print()
print(classification_report(y_test, y_pred, zero_division=0))

# 7) Save model and vectorizer
models_dir = ROOT / "models"
models_dir.mkdir(exist_ok=True)

joblib.dump(vectorizer, models_dir / "tfidf_vectorizer.joblib")
joblib.dump(model, models_dir / "logreg_model.joblib")

print("Model saved: models/")
