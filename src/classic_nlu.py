"""Train TF-IDF + logistic regression on labeled Turkish reviews."""

from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    df = pd.read_csv(ROOT / "data" / "processed" / "reviews_clean.csv")
    df = df.dropna(subset=["text", "category"]).copy()

    min_count = 20
    counts = df["category"].value_counts()
    keep = counts[counts >= min_count].index
    df = df[df["category"].isin(keep)].copy()

    print("Remaining categories:", df["category"].nunique())
    print("Remaining rows:", len(df))
    print(df["category"].value_counts().to_string())
    print()

    X_train, X_test, y_train, y_test = train_test_split(
        df["text"],
        df["category"],
        test_size=0.2,
        random_state=42,
        stratify=df["category"],
    )
    print("Train size:", len(X_train))
    print("Test size:", len(X_test))

    vectorizer = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),
        min_df=2,
    )
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    model = LogisticRegression(max_iter=1000)
    model.fit(X_train_vec, y_train)
    y_pred = model.predict(X_test_vec)

    acc = accuracy_score(y_test, y_pred)
    print("Accuracy:", round(acc, 4))
    print()
    print(classification_report(y_test, y_pred, zero_division=0))

    models_dir = ROOT / "models"
    models_dir.mkdir(exist_ok=True)
    joblib.dump(vectorizer, models_dir / "tfidf_vectorizer.joblib")
    joblib.dump(model, models_dir / "logreg_model.joblib")
    print("Model saved: models/")


if __name__ == "__main__":
    main()
