"""Download the Turkish reviews mini set, weak-label, and write a training CSV.

Source: https://huggingface.co/datasets/orhanxakarsu/turkishReviews-ds-mini
The Hub files have no category column; labels come from `categories.assign_category`.
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(__file__).resolve().parent
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from categories import assign_category
from text_norm import fold_tr

DATASET = "orhanxakarsu/turkishReviews-ds-mini"
RAW_DIR = ROOT / "data" / "raw"
OUT_PATH = ROOT / "data" / "processed" / "reviews_clean.csv"
PARQUET_API = f"https://huggingface.co/api/datasets/{DATASET}/parquet"


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return
    print("Downloading", url)
    tmp = dest.with_suffix(dest.suffix + ".part")
    urllib.request.urlretrieve(url, tmp)
    tmp.replace(dest)


def _parquet_urls() -> list[str]:
    with urllib.request.urlopen(PARQUET_API, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))
    urls: list[str] = []
    for split in payload.get("default", {}).values():
        urls.extend(split)
    if not urls:
        raise RuntimeError(f"No parquet URLs for {DATASET}")
    return urls


def _clean_text(text: object) -> str:
    folded = fold_tr(str(text or ""))
    return " ".join(folded.split())


def main() -> None:
    frames = []
    for index, url in enumerate(_parquet_urls()):
        path = RAW_DIR / f"turkish_reviews_{index}.parquet"
        _download(url, path)
        frames.append(pd.read_parquet(path))
    df = pd.concat(frames, ignore_index=True)
    if "review" not in df.columns:
        raise RuntimeError(f"Unexpected columns: {df.columns.tolist()}")

    df = df.dropna(subset=["review"]).copy()
    df["text"] = df["review"].map(_clean_text)
    df = df[df["text"].str.len() >= 40].copy()
    df["category"] = df["review"].map(assign_category)

    out = df[["text", "category"]].drop_duplicates(subset=["text"])
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_PATH, index=False, encoding="utf-8")

    print("Saved:", OUT_PATH)
    print("Rows:", len(out))
    print()
    print(out["category"].value_counts().to_string())


if __name__ == "__main__":
    main()
