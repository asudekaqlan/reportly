import pandas as pd
import re

# 1) Load the sample
path = "data/processed/complaints_sample.csv"
df = pd.read_csv(path)

print("Row count:", len(df))
print("Columns:", df.columns.tolist())
print()

# 2) Check missing values
print("Missing values:")
print(df.isna().sum())
print()

# 3) Category distribution
print("Number of categories:", df["category"].nunique())
print(df["category"].value_counts().head(10))
print()

# 4) Look at a sample text
print("Sample text (first row):")
print(df.loc[0, "text"][:300])
print()


def clean_text(text):
    """Make text more suitable for the model."""
    text = str(text)  # ensure string
    text = text.lower()  # lowercase
    text = re.sub(r"\s+", " ", text)  # collapse whitespace
    text = text.strip()  # trim ends
    return text


# 5) Apply cleaning
df["text_clean"] = df["text"].apply(clean_text)

# 6) Save
out_path = "data/processed/complaints_clean.csv"
df[["text_clean", "category"]].rename(
    columns={"text_clean": "text"}
).to_csv(out_path, index=False)

print("Clean data saved:", out_path)
print("Clean sample:")
print(df.loc[0, "text_clean"][:300])
