"""Prepare Tableau-friendly CSV tables from the cleaned Netflix catalogue.

Outputs (in ``tableau/Data/Netflix``):
    titles.csv     - one row per title
    genres.csv     - one row per title/genre pair (for accurate genre counts)
    countries.csv  - one row per title/country pair (for accurate country counts)

Run with:  python prepare_tableau_data.py
"""

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import pandas as pd

from eda_netflix import clean, duplicates, feature_engineering, load

BASE_DIR = Path(__file__).parent
OUT_DIR = BASE_DIR / "tableau" / "Data" / "Netflix"

TITLE_COLUMNS = [
    "show_id",
    "type",
    "title",
    "director",
    "country",
    "release_year",
    "rating",
    "duration_value",
    "duration_unit",
    "listed_in",
    "primary_genre",
    "primary_country",
    "added_year",
    "added_month",
    "decade",
    "num_cast",
    "num_genres",
    "content_age",
]


def build_frames():
    # The EDA helpers print progress banners; keep this script's output quiet.
    with redirect_stdout(StringIO()):
        df = load()
        df = duplicates(df)
        df = clean(df)
        df = feature_engineering(df)

    df["primary_genre"] = (
        df["genres"].apply(lambda gs: gs[0] if gs else "Unknown").replace("", "Unknown")
    )
    df["decade"] = (df["release_year"] // 10 * 10).astype(int)
    df["added_year"] = df["added_year"].astype("Int64")
    df["added_month"] = df["added_month"].astype("string")

    titles = df.reindex(columns=TITLE_COLUMNS).copy()
    titles["director"] = titles["director"].fillna("Unknown")
    titles["country"] = titles["country"].fillna("Unknown")
    titles["rating"] = titles["rating"].fillna("Unknown")
    titles["duration_unit"] = titles["duration_unit"].fillna("Unknown")
    for column in ["duration_value", "num_cast", "num_genres", "content_age"]:
        titles[column] = titles[column].astype("Int64")

    genres = (
        df[["show_id", "type", "release_year", "added_year", "genres"]]
        .explode("genres")
        .rename(columns={"genres": "genre"})
        .dropna(subset=["genre"])
    )
    genres = genres[genres["genre"].str.strip().ne("")]

    countries = (
        df[["show_id", "type", "release_year", "added_year", "country"]]
        .assign(country=lambda d: d["country"].fillna("").str.split(","))
        .explode("country")
    )
    countries["country"] = countries["country"].str.strip()
    countries = countries[
        countries["country"].ne("") & countries["country"].ne("Unknown")
    ]

    return titles, genres, countries


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    titles, genres, countries = build_frames()

    titles.to_csv(OUT_DIR / "titles.csv", index=False, encoding="utf-8")
    genres.to_csv(OUT_DIR / "genres.csv", index=False, encoding="utf-8")
    countries.to_csv(OUT_DIR / "countries.csv", index=False, encoding="utf-8")

    print(f"titles    : {len(titles):,} rows -> {OUT_DIR / 'titles.csv'}")
    print(f"genres    : {len(genres):,} rows -> {OUT_DIR / 'genres.csv'}")
    print(f"countries : {len(countries):,} rows -> {OUT_DIR / 'countries.csv'}")


if __name__ == "__main__":
    main()
