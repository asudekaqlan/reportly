import pandas as pd

# Raw data path
path = "data/raw/complaints.csv"

# Read only the first 5 rows (not the full file)
df = pd.read_csv(path, nrows=5)

print("Columns:")
print(df.columns.tolist())
print()
print("First 5 rows:")
print(df)
