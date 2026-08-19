import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
path = ROOT / "data" / "raw" / "complaints.csv"

# Only the two columns we need
cols = ["Consumer complaint narrative", "Product"]

print("Reading data (this may take a while)...")
df = pd.read_csv(path, usecols=cols)

print("Rows read:", len(df))

# Drop rows with empty text
df = df.dropna(subset=["Consumer complaint narrative"])
print("Rows with text:", len(df))

# Simplify column names
df = df.rename(
    columns={
        "Consumer complaint narrative": "text",
        "Product": "category",
    }
)

# Take a random sample of 5000 rows
sample_size = 5000
df_sample = df.sample(n=sample_size, random_state=42)

# Save
out_path = ROOT / "data" / "processed" / "complaints_sample.csv"
out_path.parent.mkdir(parents=True, exist_ok=True)
df_sample.to_csv(out_path, index=False)

print("Saved:", out_path)
print("Sample rows:", len(df_sample))
print()
print("Category distribution:")
print(df_sample["category"].value_counts())
