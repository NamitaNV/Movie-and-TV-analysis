"""Download the real Netflix Movies and TV Shows dataset.

The dataset is the public "Netflix Movies and TV Shows" catalogue originally
published on Kaggle by Shivam Bansal (8,807 titles, last updated September 2021).
It is fetched from a public mirror so the project can be reproduced without a
Kaggle account.
"""

import io
import urllib.request
from pathlib import Path

import pandas as pd

DATA_PATH = Path(__file__).parent / "netflix_titles.csv"

# Mirror 1 is the full 8,807-row Kaggle snapshot; mirror 2 is the earlier
# 7,787-row snapshot published by TidyTuesday if the first one is unavailable.
SOURCES = [
    "https://huggingface.co/datasets/hugginglearners/netflix-shows/resolve/main/netflix_titles.csv",
    "https://raw.githubusercontent.com/rfordatascience/tidytuesday/master/data/2021/2021-04-20/netflix_titles.csv",
]

REQUIRED_COLUMNS = [
    "show_id",
    "type",
    "title",
    "director",
    "cast",
    "country",
    "date_added",
    "release_year",
    "rating",
    "duration",
    "listed_in",
    "description",
]


def validate(df):
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"download is missing columns: {', '.join(missing)}")
    if len(df) < 5000:
        raise ValueError(f"download looks truncated ({len(df):,} rows)")
    types = set(df["type"].dropna().unique())
    if types != {"Movie", "TV Show"}:
        raise ValueError(f"unexpected content types: {sorted(types)}")
    return df


def download(dest=DATA_PATH):
    """Fetch the dataset and save it to ``dest`` as UTF-8 CSV."""
    errors = []
    for url in SOURCES:
        try:
            with urllib.request.urlopen(url, timeout=120) as response:
                payload = response.read()
            df = validate(pd.read_csv(io.BytesIO(payload), encoding="utf-8"))
            dest.write_bytes(payload)
            print(f"Downloaded {len(df):,} real titles x {df.shape[1]} columns -> {dest}")
            print(f"  source   : {url}")
            print(f"  movies   : {int((df['type'] == 'Movie').sum()):,}")
            print(f"  TV shows : {int((df['type'] == 'TV Show').sum()):,}")
            print(f"  years    : {int(df['release_year'].min())} - {int(df['release_year'].max())}")
            return df
        except Exception as exc:  # try the next mirror
            errors.append(f"{url} -> {exc}")
    raise RuntimeError("Could not download the dataset:\n  " + "\n  ".join(errors))


if __name__ == "__main__":
    download()
