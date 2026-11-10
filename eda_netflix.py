from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

DATA_PATH = Path(__file__).parent / "netflix_titles.csv"
CHART_DIR = Path(__file__).parent / "output"
REFERENCE_YEAR = 2021

PALETTE = {"Movie": "#E50914", "TV Show": "#00A8E1"}
sns.set_theme(style="whitegrid", context="notebook")
plt.rcParams["figure.dpi"] = 120
plt.rcParams["savefig.bbox"] = "tight"


def banner(title):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def save(fig, name):
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    path = CHART_DIR / name
    fig.savefig(path)
    plt.close(fig)
    print(f"  saved -> output/{name}")


def load():
    banner("LOADING DATASET")
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"{DATA_PATH.name} not found. Run: python download_data.py"
        )
    df = pd.read_csv(DATA_PATH, encoding="utf-8")
    print(f"  source : {DATA_PATH.name}")
    print(f"  size   : {DATA_PATH.stat().st_size / 1024:.1f} KB")
    return df


def explore(df):
    banner("1. DATASET SHAPE")
    print(f"  rows    : {df.shape[0]:,}")
    print(f"  columns : {df.shape[1]}")

    banner("2. COLUMNS AND DATA TYPES")
    info = pd.DataFrame(
        {
            "dtype": df.dtypes.astype(str),
            "non_null": df.notna().sum(),
            "null": df.isna().sum(),
            "unique": df.nunique(dropna=True),
        }
    )
    print(info.to_string())
    print("\n  sample records:")
    print(df.head(3).to_string(max_colwidth=28))


def missing_values(df):
    banner("3. MISSING VALUES")
    total_cells = df.size
    missing = df.isna().sum()
    report = pd.DataFrame(
        {
            "missing": missing,
            "missing_%": (missing / len(df) * 100).round(2),
        }
    ).sort_values("missing", ascending=False)
    report = report[report["missing"] > 0]
    print(report.to_string() if not report.empty else "  no missing values")
    print(f"\n  total cells      : {total_cells:,}")
    print(f"  total missing    : {int(missing.sum()):,}")
    print(f"  overall miss rate: {missing.sum() / total_cells * 100:.2f}%")

    cols = [c for c in report.index if report.loc[c, "missing"] > 0]
    if cols:
        fig, ax = plt.subplots(figsize=(8, max(3, 0.45 * len(cols))))
        sns.barplot(
            data=report.reset_index().rename(columns={"index": "column"}),
            x="missing_%",
            y="column",
            ax=ax,
            color="#E50914",
        )
        ax.set_title("Missing Values by Column (%)", fontweight="bold")
        ax.set_xlabel("% missing")
        ax.set_ylabel("")
        save(fig, "03_missing_values.png")


def duplicates(df):
    banner("4. DUPLICATE RECORDS")
    print(f"  fully duplicated rows        : {df.duplicated().sum()}")
    print(f"  duplicate show_id values     : {df['show_id'].duplicated().sum()}")
    print(f"  duplicate title values       : {df['title'].duplicated().sum()}")
    key = ["title", "type", "release_year"]
    print(f"  duplicate (title,type,year)  : {df.duplicated(subset=key).sum()}")

    dupes = df[df.duplicated(subset=key, keep=False)].sort_values(key)
    if not dupes.empty:
        print("\n  examples of duplicated titles:")
        print(
            dupes[["show_id", "title", "type", "release_year"]]
            .head(10)
            .to_string(index=False)
        )
        return df.drop_duplicates(subset=key, keep="first").reset_index(drop=True)
    return df


def clean(df):
    banner("5. DATA CLEANING")
    before = len(df)
    df = df.drop_duplicates(subset=["title", "type", "release_year"], keep="first")
    df = df.drop_duplicates(subset=["show_id"], keep="first")
    df = df.dropna(subset=["show_id", "type", "title", "release_year"])
    df["show_id"] = df["show_id"].astype(str)
    df["type"] = df["type"].str.strip().str.title()
    df["type"] = df["type"].replace({"Tv Show": "TV Show", "Tvshow": "TV Show"})
    df["release_year"] = pd.to_numeric(df["release_year"], errors="coerce")
    df = df.dropna(subset=["release_year"])
    df["release_year"] = df["release_year"].astype(int)
    df = df[(df["release_year"] >= 1925) & (df["release_year"] <= REFERENCE_YEAR)]
    print(f"  rows before : {before:,}")
    print(f"  rows after  : {len(df):,}  (removed {before - len(df):,})")
    print(f"  type values : {sorted(df['type'].unique())}")
    return df.reset_index(drop=True)


def feature_engineering(df):
    banner("6. FEATURE ENGINEERING (DERIVED COLUMNS)")

    # The real catalogue uses full month names ("September 25, 2021"), while
    # some snapshots use abbreviations, so let pandas infer each value.
    df["date_added"] = pd.to_datetime(
        df["date_added"].astype("string").str.strip(), format="mixed", errors="coerce"
    )
    unparsed = int(df["date_added"].isna().sum())
    print(f"  date_added rows that failed to parse (coerced to NaT): {unparsed}")

    df["added_year"] = df["date_added"].dt.year
    df["added_month"] = df["date_added"].dt.to_period("M")
    df["content_age"] = REFERENCE_YEAR - df["release_year"]

    duration = df["duration"].astype(str).str.strip()
    df["duration_value"] = pd.to_numeric(
        duration.str.extract(r"(\d+)")[0], errors="coerce"
    )
    df["duration_unit"] = np.where(
        duration.str.contains("Season", case=False), "seasons", "minutes"
    )
    df["is_movie"] = df["type"].eq("Movie")

    df["num_cast"] = (
        df["cast"].fillna("").str.split(",").map(lambda x: len([c for c in x if c.strip()]))
    )
    df["num_genres"] = (
        df["listed_in"].fillna("").str.split(",").map(lambda x: len([g for g in x if g.strip()]))
    )
    df["primary_country"] = df["country"].fillna("Unknown").str.split(",").str[0].str.strip()
    df["director_name"] = df["director"].fillna("Unknown Director").str.strip()

    df["genres"] = df["listed_in"].fillna("").apply(
        lambda s: [g.strip() for g in s.split(",") if g.strip()]
    )

    print("  new columns: added_year, added_month, content_age, duration_value,")
    print("              duration_unit, is_movie, num_cast, num_genres,")
    print("              primary_country, director_name, genres")
    return df


def genre_frame(df):
    exploded = df[["show_id", "type", "genres"]].explode("genres")
    return exploded.dropna(subset=["genres"])


def type_analysis(df):
    banner("7. MOVIES VS TV SHOWS")
    counts = df["type"].value_counts()
    share = (counts / len(df) * 100).round(2)
    summary = pd.DataFrame({"count": counts, "share_%": share})
    print(summary.to_string())

    for content_type in counts.index:
        subset = df[df["type"] == content_type]
        print(f"\n  --- {content_type} ---")
        print(f"  count              : {len(subset):,}")
        print(f"  release year range : {subset['release_year'].min()} - {subset['release_year'].max()}")
        print(f"  median release year: {subset['release_year'].median():.0f}")
        print(f"  avg genres/title   : {subset['num_genres'].mean():.2f}")
        print(f"  avg cast size      : {subset['num_cast'].mean():.2f}")
        print(f"  distinct countries : {subset['primary_country'].nunique()}")
        if content_type == "Movie":
            print(f"  median runtime     : {subset['duration_value'].median():.0f} min")
        else:
            print(f"  median seasons     : {subset['duration_value'].median():.0f}")

    fig, ax = plt.subplots(figsize=(7, 5))
    colors = [PALETTE.get(t, "#888888") for t in counts.index]
    sns.barplot(x=counts.index, y=counts.values, ax=ax, hue=counts.index,
                palette=dict(zip(counts.index, colors)), legend=False)
    for i, v in enumerate(counts.values):
        ax.text(i, v + 60, f"{v:,}\n({share.iloc[i]}%)", ha="center", fontweight="bold")
    ax.set_title("Content Type Distribution", fontweight="bold")
    ax.set_xlabel("")
    ax.set_ylabel("Number of titles")
    ax.set_ylim(0, counts.max() * 1.18)
    save(fig, "01_type_distribution.png")


def genre_analysis(df):
    banner("8. GENRE ANALYSIS")
    exploded = genre_frame(df)
    genre_counts = exploded["genres"].value_counts()
    top = genre_counts.head(15)

    print(f"  total genre tags      : {len(exploded):,}")
    print(f"  distinct genres       : {genre_counts.size}")
    print(f"  avg genres per title  : {df['num_genres'].mean():.2f}")
    print(f"  titles with no genre  : {int((df['num_genres'] == 0).sum())}")
    print("\n  TOP 15 GENRES")
    top_df = pd.DataFrame({"titles": top, "share_%": (top / len(df) * 100).round(2)})
    print(top_df.to_string())

    print("\n  TOP 10 GENRES SPLIT BY TYPE")
    pivot = (
        exploded[exploded["genres"].isin(top.head(10).index)]
        .pivot_table(index="genres", columns="type", values="show_id", aggfunc="count")
        .fillna(0)
        .astype(int)
    )
    pivot = pivot.sort_values(by=list(pivot.columns), ascending=False)
    print(pivot.to_string())

    print("\n  MULTI-GENRE TITLES")
    buckets = pd.cut(df["num_genres"], [-1, 0, 1, 2, 3], labels=["0", "1", "2", "3+"])
    print(buckets.value_counts().sort_index().to_string())

    fig, ax = plt.subplots(figsize=(10, 7))
    sns.barplot(
        x=top.values, y=top.index, ax=ax, hue=top.index, palette="husl", legend=False
    )
    ax.set_title("Top 15 Most Common Genres", fontweight="bold")
    ax.set_xlabel("Number of titles")
    ax.set_ylabel("")
    save(fig, "02_top_genres.png")

    fig, ax = plt.subplots(figsize=(11, 6))
    sns.barplot(data=pivot.reset_index().melt(id_vars="genres", var_name="type", value_name="titles"),
                x="genres", y="titles", hue="type", ax=ax, palette=PALETTE)
    ax.set_title("Top 10 Genres: Movies vs TV Shows", fontweight="bold")
    ax.set_xlabel("")
    ax.set_ylabel("Number of titles")
    ax.tick_params(axis="x", rotation=35)
    save(fig, "03_genres_by_type.png")


def year_analysis(df):
    banner("9. RELEASE YEAR ANALYSIS")
    print(df["release_year"].describe().round(2).to_string())
    print(f"\n  oldest title year : {df['release_year'].min()}")
    print(f"  newest title year : {df['release_year'].max()}")

    recent = df[df["release_year"] >= 2015]
    print(f"  titles from 2015+ : {len(recent):,} ({len(recent) / len(df) * 100:.1f}% of catalogue)")

    decade = pd.cut(
        df["release_year"],
        [1924, 1989, 1999, 2009, 2014, 2016, 2018, 2021],
        labels=["<1990", "1990s", "2000s", "2010-14", "2015-16", "2017-18", "2019-21"],
    )
    print("\n  BY DECADE BUCKET")
    print(decade.value_counts().sort_index().to_string())

    pivot = (
        df.pivot_table(index="release_year", columns="type", values="show_id", aggfunc="count")
        .fillna(0)
        .astype(int)
    )
    print("\n  LAST 12 RELEASE YEARS BY TYPE")
    print(pivot.tail(12).to_string())

    fig, ax = plt.subplots(figsize=(13, 6))
    for content_type in pivot.columns:
        ax.plot(pivot.index, pivot[content_type], label=content_type, color=PALETTE[content_type], linewidth=2)
    ax.set_title("Titles Added to Netflix by Release Year", fontweight="bold")
    ax.set_xlabel("Release year")
    ax.set_ylabel("Number of titles")
    ax.legend()
    save(fig, "04_releases_by_year.png")

    fig, ax = plt.subplots(figsize=(9, 5))
    sns.histplot(data=df, x="release_year", hue="type", multiple="stack", palette=PALETTE, bins=40, ax=ax)
    ax.set_title("Distribution of Release Years", fontweight="bold")
    ax.set_xlabel("Release year")
    ax.set_ylabel("Number of titles")
    save(fig, "05_release_year_histogram.png")

    if "added_year" in df and df["added_year"].notna().any():
        added = df.dropna(subset=["added_month"]).groupby("added_month").size()
        if len(added) > 1:
            fig, ax = plt.subplots(figsize=(13, 5))
            ax.plot(added.index.to_timestamp(), added.values, color="#E50914", linewidth=1.8)
            ax.fill_between(added.index.to_timestamp(), added.values, alpha=0.2, color="#E50914")
            ax.set_title("Titles Added to the Catalogue per Month", fontweight="bold")
            ax.set_xlabel("Date added")
            ax.set_ylabel("Titles added")
            save(fig, "06_monthly_additions.png")
            print(f"\n  peak month for additions: {added.idxmax()} ({added.max():,} titles)")


def country_analysis(df):
    banner("10. COUNTRY ANALYSIS")
    counts = df["primary_country"].value_counts()
    top = counts.head(15)
    print(f"  distinct primary countries : {counts.size}")
    print(f"  titles with country missing: {int(df['primary_country'].eq('Unknown').sum())}")
    print("\n  TOP 15 COUNTRIES")
    print(pd.DataFrame({"titles": top, "share_%": (top / len(df) * 100).round(2)}).to_string())

    us = counts.get("United States", 0)
    print(f"\n  United States share : {us / len(df) * 100:.2f}%")
    print(f"  top 3 countries     : {counts.head(3).sum() / len(df) * 100:.2f}% of catalogue")
    print(f"  long tail           : {int((counts == 1).sum())} countries have exactly 1 title")

    fig, ax = plt.subplots(figsize=(10, 7))
    sns.barplot(x=top.values, y=top.index, ax=ax, hue=top.index, palette="viridis", legend=False)
    ax.set_title("Top 15 Countries by Number of Titles", fontweight="bold")
    ax.set_xlabel("Number of titles")
    ax.set_ylabel("")
    save(fig, "07_top_countries.png")

    fig, ax = plt.subplots(figsize=(8, 8))
    head = counts.head(10)
    other = counts.iloc[10:].sum()
    ax.pie(
        list(head.values) + [other],
        labels=list(head.index) + ["Other"],
        autopct="%1.1f%%",
        colors=list(sns.color_palette("tab10", 10)) + [sns.color_palette("Greys", 2)[1]],
        textprops={"fontsize": 9},
    )
    ax.set_title("Share of Titles by Primary Country (Top 10 + Other)", fontweight="bold")
    save(fig, "08_country_share.png")


def statistical_summary(df):
    banner("11. STATISTICAL SUMMARY")
    print(df[["release_year", "content_age", "duration_value", "num_cast", "num_genres"]].describe().round(2).to_string())

    print("\n  BY TYPE (release year, runtime/seasons, cast, genres)")
    print(
        df.groupby("type")[["release_year", "duration_value", "num_cast", "num_genres"]]
        .agg(["mean", "median", "std"])
        .round(2)
        .to_string()
    )

    print("\n  MODE / MOST COMMON VALUES")
    print(f"  most common type     : {df['type'].mode().iloc[0]}")
    print(f"  most common rating   : {df['rating'].mode().iloc[0]}")
    print(f"  most common country  : {df['primary_country'].mode().iloc[0]}")
    print(f"  most common genre    : {genre_frame(df)['genres'].mode().iloc[0]}")

    print("\n  CONTENT RATING DISTRIBUTION")
    print(pd.DataFrame({"titles": df["rating"].value_counts()}).to_string())

    fig, ax = plt.subplots(figsize=(11, 5))
    order = df["rating"].value_counts().index
    sns.countplot(data=df, x="rating", order=order, hue="type", palette=PALETTE, ax=ax)
    ax.set_title("Content Rating Distribution by Type", fontweight="bold")
    ax.set_xlabel("Rating")
    ax.set_ylabel("Number of titles")
    save(fig, "09_rating_distribution.png")

    fig, ax = plt.subplots(figsize=(12, 5))
    sns.countplot(data=df, x="release_year", order=list(range(2005, REFERENCE_YEAR + 1)), hue="type",
                  palette=PALETTE, ax=ax)
    ax.set_title("Titles per Release Year (2005+)", fontweight="bold")
    ax.set_xlabel("Release year")
    ax.set_ylabel("Number of titles")
    ax.tick_params(axis="x", rotation=45)
    save(fig, "10_titles_per_year.png")


def correlation_analysis(df):
    banner("12. CORRELATION ANALYSIS")
    numeric_cols = ["release_year", "content_age", "duration_value", "num_cast", "num_genres"]
    numeric = df[numeric_cols].copy()
    movies = df.loc[df["is_movie"], "duration_value"]
    shows = df.loc[~df["is_movie"], "duration_value"]

    print(f"  movies with runtime : {movies.notna().sum():,}")
    print(f"  shows with seasons  : {shows.notna().sum():,}")
    print("  NOTE: duration_value mixes minutes (movies) and seasons (shows);")
    print("        interpret its correlations separately per type below.")

    print("\n  PEARSON CORRELATION (all titles)")
    print(numeric.corr(numeric_only=True).round(3).to_string())

    print("\n  PEARSON CORRELATION (movies only, duration = minutes)")
    print(
        df.loc[df["is_movie"], numeric_cols].corr(numeric_only=True).round(3).to_string()
    )

    print("\n  PEARSON CORRELATION (TV shows only, duration = seasons)")
    print(
        df.loc[~df["is_movie"], numeric_cols].corr(numeric_only=True).round(3).to_string()
    )

    print("\n  STRONGEST FEATURE PAIRS (|r| >= 0.15, all titles)")
    corr = numeric.corr(numeric_only=True)
    pairs = []
    cols = list(corr.columns)
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            pairs.append((cols[i], cols[j], corr.iloc[i, j]))
    for a, b, r in sorted(pairs, key=lambda x: abs(x[2]), reverse=True):
        if abs(r) >= 0.15:
            print(f"    {a:>14} ~ {b:<14} r = {r:+.3f}")

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0,
                vmin=-1, vmax=1, square=True, ax=ax)
    ax.set_title("Correlation Heatmap (Numeric Features)", fontweight="bold")
    save(fig, "11_correlation_heatmap.png")


def outlier_analysis(df):
    banner("13. OUTLIER DETECTION (IQR METHOD)")

    def iqr_report(series, label, min_iqr=1.0):
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr = q3 - q1
        low, high = q1 - min_iqr * iqr, q3 + min_iqr * iqr
        mask = (series < low) | (series > high)
        print(f"\n  [{label}]")
        print(f"    Q1 / Q3      : {q1:.2f} / {q3:.2f}")
        print(f"    IQR          : {iqr:.2f}")
        print(f"    fences       : [{low:.2f}, {high:.2f}]")
        print(f"    outliers     : {int(mask.sum()):,} ({mask.mean() * 100:.2f}%)")
        if mask.any():
            vals = series[mask]
            print(f"    outlier range: {vals.min():.2f} to {vals.max():.2f}")
        return mask

    movie_duration = df.loc[df["is_movie"], "duration_value"].dropna()
    show_seasons = df.loc[~df["is_movie"], "duration_value"].dropna()
    cast_size = df["num_cast"].astype(float)

    iqr_report(movie_duration, "Movie runtime (minutes)")
    iqr_report(show_seasons, "TV show seasons")
    iqr_report(cast_size, "Cast size")
    iqr_report(df["release_year"].astype(float), "Release year")
    iqr_report(df["num_genres"].astype(float), "Genres per title")

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    sns.boxplot(data=movie_duration, ax=axes[0], color="#E50914")
    axes[0].set_title("Movie Runtime (minutes)", fontweight="bold")
    axes[0].set_xlabel("")
    sns.boxplot(data=show_seasons, ax=axes[1], color="#00A8E1")
    axes[1].set_title("TV Show Seasons", fontweight="bold")
    axes[1].set_xlabel("")
    fig.suptitle("Outlier Detection via Box Plots", fontweight="bold", y=1.04)
    save(fig, "12_duration_boxplot.png")

    fig, ax = plt.subplots(figsize=(9, 5.5))
    sns.boxplot(data=df, x="type", y="num_cast", order=["Movie", "TV Show"],
                hue="type", palette=PALETTE, legend=False, ax=ax)
    ax.set_title("Cast Size Outliers by Content Type", fontweight="bold")
    ax.set_xlabel("")
    ax.set_ylabel("Number of credited cast members")
    save(fig, "13_cast_size_boxplot.png")


def scatter_plots(df):
    banner("14. SCATTER PLOTS")

    movies = df[df["is_movie"]].dropna(subset=["duration_value"])
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.5))
    sns.regplot(data=movies, x="release_year", y="duration_value", ax=axes[0],
                scatter_kws={"alpha": 0.15, "s": 8}, line_kws={"color": "#E50914"})
    axes[0].set_title("Movie Runtime vs Release Year", fontweight="bold")
    axes[0].set_xlabel("Release year")
    axes[0].set_ylabel("Runtime (minutes)")
    sns.regplot(data=movies, x="release_year", y="num_cast", ax=axes[1],
                scatter_kws={"alpha": 0.15, "s": 8}, line_kws={"color": "#E50914"})
    axes[1].set_title("Cast Size vs Release Year (Movies)", fontweight="bold")
    axes[1].set_xlabel("Release year")
    axes[1].set_ylabel("Number of cast members")
    save(fig, "14_scatter_year_vs_duration.png")

    fig, axes = plt.subplots(1, 2, figsize=(15, 5.5))
    sns.scatterplot(data=df, x="release_year", y="num_genres", hue="type",
                    palette=PALETTE, alpha=0.35, s=18, ax=axes[0])
    axes[0].set_title("Genres per Title vs Release Year", fontweight="bold")
    axes[0].set_xlabel("Release year")
    axes[0].set_ylabel("Number of genres")
    sns.scatterplot(data=df, x="num_cast", y="num_genres", hue="type",
                    palette=PALETTE, alpha=0.35, s=18, ax=axes[1])
    axes[1].set_title("Cast Size vs Number of Genres", fontweight="bold")
    axes[1].set_xlabel("Number of cast members")
    axes[1].set_ylabel("Number of genres")
    save(fig, "15_scatter_genres_cast.png")

    fig, ax = plt.subplots(figsize=(10, 6))
    subset = df.dropna(subset=["duration_value"])
    for flag, label in ((True, "Movie"), (False, "TV Show")):
        part = subset[subset["is_movie"] == flag]
        if len(part) > 2:
            sns.regplot(data=part, x="release_year", y="duration_value", ax=ax,
                        scatter_kws={"alpha": 0.12, "s": 8},
                        line_kws={"color": PALETTE[label], "linewidth": 2.2},
                        label=label)
    ax.set_title("Duration vs Release Year, Split by Content Type", fontweight="bold")
    ax.set_xlabel("Release year")
    ax.set_ylabel("Duration (minutes for movies, seasons for shows)")
    ax.legend()
    save(fig, "16_scatter_duration_by_type.png")


def creator_analysis(df):
    banner("15. CREATOR ANALYSIS (BONUS)")
    directors = df.loc[df["is_movie"], "director_name"].value_counts().head(10)
    print("  TOP 10 DIRECTORS (movies, 'Unknown Director' excluded)")
    print(directors[directors.index != "Unknown Director"].to_string())

    show_cast = df.loc[~df["is_movie"]]
    actors = (
        show_cast["cast"]
        .fillna("")
        .str.split(",")
        .explode()
        .str.strip()
    )
    actors = actors[actors != ""].value_counts().head(10)
    print("\n  TOP 10 ACTORS (TV shows)")
    print(actors.to_string())

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    d = directors[directors.index != "Unknown Director"].head(10)
    sns.barplot(x=d.values, y=d.index, ax=axes[0], hue=d.index, palette="Reds_r", legend=False)
    axes[0].set_title("Top 10 Directors (Movies)", fontweight="bold")
    axes[0].set_xlabel("Number of titles")
    axes[0].set_ylabel("")
    sns.barplot(x=actors.values, y=actors.index, ax=axes[1], hue=actors.index,
                palette="Blues_r", legend=False)
    axes[1].set_title("Top 10 Actors (TV Shows)", fontweight="bold")
    axes[1].set_xlabel("Number of appearances")
    axes[1].set_ylabel("")
    save(fig, "17_creators.png")


def key_findings(df):
    banner("KEY FINDINGS")
    counts = df["type"].value_counts()
    genres = genre_frame(df)["genres"].value_counts()
    countries = df["primary_country"].value_counts()
    movies = df[df["is_movie"]]

    findings = [
        f"Content split: {counts.get('Movie', 0):,} movies vs {counts.get('TV Show', 0):,} TV shows "
        f"({(counts.get('Movie', 0) / len(df) * 100):.1f}% movies).",
        f"Most common genre: '{genres.index[0]}' with {genres.iloc[0]:,} titles "
        f"({genres.iloc[0] / len(df) * 100:.1f}% of the catalogue).",
        f"Top producer: {countries.index[0]} with {countries.iloc[0]:,} titles "
        f"({countries.iloc[0] / len(df) * 100:.1f}% share).",
        f"Catalogue is heavily back-weighted: {len(df[df['release_year'] >= 2015]):,} titles "
        f"({len(df[df['release_year'] >= 2015]) / len(df) * 100:.1f}%) are from 2015 or later; "
        f"earliest release year is {df['release_year'].min()}.",
        f"Median movie runtime is {movies['duration_value'].median():.0f} minutes; "
        f"median TV show runs {df.loc[~df['is_movie'], 'duration_value'].median():.0f} season(s).",
        f"Most common rating is '{df['rating'].mode().iloc[0]}' - the catalogue skews mature.",
        f"Data quality: {int(df['director'].isna().sum()):,} titles have no director and "
        f"{int(df['cast'].isna().sum()):,} no cast listed; "
        f"{int(df['listed_in'].isna().sum()):,} titles lack genre tags.",
    ]
    for i, f in enumerate(findings, 1):
        print(f"  {i}. {f}")

    banner("CHARTS SAVED")
    for p in sorted(CHART_DIR.glob("*.png")):
        print(f"  output/{p.name}")


def main():
    df = load()
    explore(df)
    missing_values(df)
    df = duplicates(df)
    df = clean(df)
    df = feature_engineering(df)
    type_analysis(df)
    genre_analysis(df)
    year_analysis(df)
    country_analysis(df)
    statistical_summary(df)
    correlation_analysis(df)
    outlier_analysis(df)
    scatter_plots(df)
    creator_analysis(df)
    key_findings(df)
    print(f"\nDone. {len(sorted(CHART_DIR.glob('*.png')))} charts written to {CHART_DIR}\n")


if __name__ == "__main__":
    main()
