from threading import RLock

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st

from eda_netflix import (
    PALETTE,
    REFERENCE_YEAR,
    clean,
    duplicates,
    feature_engineering,
    load,
)

st.set_page_config(
    page_title="Netflix Content Analysis",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

_lock = RLock()
sns.set_theme(style="whitegrid", context="notebook")

TYPE_ORDER = ["Movie", "TV Show"]
FILTER_KEYS = ["f_types", "f_years", "f_genres", "f_countries", "f_ratings"]


def show(fig):
    with _lock:
        st.pyplot(fig)
    plt.close(fig)


@st.cache_data(show_spinner="Loading and cleaning dataset...")
def get_data():
    df = load()
    df = duplicates(df)
    df = clean(df)
    return feature_engineering(df)


def exploded_genres(df):
    return df["genres"].explode().dropna()


def apply_filters(df, types, years, genres, countries, ratings):
    out = df
    out = out[out["type"].isin(types)]
    out = out[out["release_year"].between(years[0], years[1])]
    out = out[out["genres"].apply(lambda gs: any(g in genres for g in gs))]
    out = out[out["primary_country"].isin(countries)]
    out = out[out["rating"].isin(ratings)]
    return out


def duration_label(df, content_type):
    if content_type == "Movie":
        return f"{df['duration_value'].median():.0f} min median runtime"
    return f"{df['duration_value'].median():.0f} seasons median"


def fig_type_distribution(df):
    counts = df["type"].value_counts()
    ordered = [t for t in TYPE_ORDER if t in counts.index]
    fig, ax = plt.subplots(figsize=(6, 4.5))
    sns.barplot(
        x=ordered,
        y=[counts[t] for t in ordered],
        hue=ordered,
        palette={t: PALETTE.get(t, "#888888") for t in ordered},
        legend=False,
        ax=ax,
    )
    for i, t in enumerate(ordered):
        v = counts[t]
        ax.text(i, v + max(counts) * 0.02, f"{v:,}\n{v / len(df) * 100:.1f}%",
                ha="center", fontweight="bold", fontsize=10)
    ax.set_title("Content Type Split", fontweight="bold")
    ax.set_xlabel("")
    ax.set_ylabel("Titles")
    ax.set_ylim(0, counts.max() * 1.2)
    return fig


def fig_top_genres(df, n=15):
    counts = exploded_genres(df).value_counts().head(n)
    fig, ax = plt.subplots(figsize=(9, max(4, 0.4 * len(counts))))
    sns.barplot(x=counts.values, y=counts.index, hue=counts.index,
                palette="husl", legend=False, ax=ax)
    ax.set_title(f"Top {len(counts)} Genres", fontweight="bold")
    ax.set_xlabel("Titles")
    ax.set_ylabel("")
    return fig


def fig_genres_by_type(df, n=10):
    ex = df[["type", "genres"]].explode("genres").dropna(subset=["genres"])
    ex = ex.rename(columns={"genres": "genre"})
    top = ex["genre"].value_counts().head(n).index
    pivot = (
        ex[ex["genre"].isin(top)]
        .assign(n=1)
        .pivot_table(index="genre", columns="type", values="n", aggfunc="sum")
        .fillna(0)
    )
    cols = [c for c in TYPE_ORDER if c in pivot.columns]
    pivot = pivot.sort_values(by=cols, ascending=False)
    melted = pivot.reset_index().melt(id_vars="genre", var_name="type", value_name="titles")
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=melted, x="genre", y="titles", hue="type",
                palette={c: PALETTE.get(c, "#888888") for c in cols}, ax=ax)
    ax.set_title("Top Genres: Movies vs TV Shows", fontweight="bold")
    ax.set_xlabel("")
    ax.set_ylabel("Titles")
    ax.tick_params(axis="x", rotation=35)
    return fig


def fig_releases_by_year(df):
    pivot = (
        df.pivot_table(index="release_year", columns="type", values="show_id", aggfunc="count")
        .fillna(0)
    )
    fig, ax = plt.subplots(figsize=(12, 5))
    for content_type in pivot.columns:
        ax.plot(pivot.index, pivot[content_type], label=content_type,
                color=PALETTE.get(content_type, "#888888"), linewidth=2)
    ax.set_title("Titles by Release Year", fontweight="bold")
    ax.set_xlabel("Release year")
    ax.set_ylabel("Titles")
    ax.legend()
    return fig


def fig_year_histogram(df):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    sns.histplot(data=df, x="release_year", hue="type", multiple="stack",
                 palette=PALETTE, bins=40, ax=ax)
    ax.set_title("Distribution of Release Years", fontweight="bold")
    ax.set_xlabel("Release year")
    ax.set_ylabel("Titles")
    return fig


def fig_monthly_additions(df):
    added = df.dropna(subset=["added_month"]).groupby("added_month").size()
    if added.empty:
        return None
    idx = added.index.to_timestamp()
    fig, ax = plt.subplots(figsize=(12, 4.5))
    ax.plot(idx, added.values, color="#E50914", linewidth=1.8)
    ax.fill_between(idx, added.values, alpha=0.2, color="#E50914")
    ax.set_title("Titles Added to the Catalogue per Month", fontweight="bold")
    ax.set_xlabel("Date added")
    ax.set_ylabel("Titles added")
    return fig


def fig_top_countries(df, n=15):
    counts = df["primary_country"].value_counts().head(n)
    fig, ax = plt.subplots(figsize=(9, max(4, 0.4 * len(counts))))
    sns.barplot(x=counts.values, y=counts.index, hue=counts.index,
                palette="viridis", legend=False, ax=ax)
    ax.set_title(f"Top {len(counts)} Countries by Titles", fontweight="bold")
    ax.set_xlabel("Titles")
    ax.set_ylabel("")
    return fig


def fig_country_share(df, n=10):
    counts = df["primary_country"].value_counts()
    head = counts.head(n)
    other = counts.iloc[n:].sum()
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.pie(
        list(head.values) + [other],
        labels=list(head.index) + ["Other"],
        autopct="%1.1f%%",
        colors=list(sns.color_palette("tab10", n)) + [sns.color_palette("Greys", 2)[1]],
        textprops={"fontsize": 9},
    )
    ax.set_title(f"Share of Titles by Country (Top {n} + Other)", fontweight="bold")
    return fig


def fig_rating_distribution(df):
    order = df["rating"].value_counts().index
    fig, ax = plt.subplots(figsize=(10, 4.5))
    sns.countplot(data=df, x="rating", order=order, hue="type", palette=PALETTE, ax=ax)
    ax.set_title("Content Rating Distribution", fontweight="bold")
    ax.set_xlabel("Rating")
    ax.set_ylabel("Titles")
    return fig


def fig_duration_box(df):
    movies = df.loc[df["is_movie"], "duration_value"].dropna()
    shows = df.loc[~df["is_movie"], "duration_value"].dropna()
    present = [c for c in TYPE_ORDER if c in set(df["type"])]
    fig, axes = plt.subplots(1, len(present), figsize=(6 * len(present), 4.5), squeeze=False)
    for i, content_type in enumerate(present):
        ax = axes[0][i]
        if content_type == "Movie":
            sns.boxplot(data=movies, ax=ax, color=PALETTE["Movie"])
            ax.set_title("Movie Runtime (minutes)", fontweight="bold")
        else:
            sns.boxplot(data=shows, ax=ax, color=PALETTE["TV Show"])
            ax.set_title("TV Show Seasons", fontweight="bold")
        ax.set_xlabel("")
    return fig


def fig_cast_box(df):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    order = [t for t in TYPE_ORDER if t in set(df["type"])]
    sns.boxplot(data=df, x="type", y="num_cast", order=order, hue="type",
                palette=PALETTE, legend=False, ax=ax)
    ax.set_title("Cast Size Distribution", fontweight="bold")
    ax.set_xlabel("")
    ax.set_ylabel("Cast members")
    return fig


def fig_corr_heatmap(df, cols):
    corr = df[cols].corr(numeric_only=True)
    fig, ax = plt.subplots(figsize=(7, 5.5))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0,
                vmin=-1, vmax=1, square=True, ax=ax)
    ax.set_title("Correlation Heatmap", fontweight="bold")
    return fig


def fig_scatter(df, x_col, y_col, color_col=None):
    data = df.dropna(subset=[x_col, y_col])
    if data.empty:
        return None
    fig, ax = plt.subplots(figsize=(7, 4.8))
    if color_col and data[color_col].nunique() > 1:
        sns.scatterplot(data=data, x=x_col, y=y_col, hue=color_col,
                        palette=PALETTE, alpha=0.4, s=22, ax=ax)
    else:
        sns.scatterplot(data=data, x=x_col, y=y_col, color="#E50914",
                        alpha=0.4, s=22, ax=ax)
    ax.set_title(f"{y_col.replace('_', ' ').title()} vs {x_col.replace('_', ' ').title()}",
                 fontweight="bold")
    return fig


def fig_missing(raw):
    missing = raw.isna().sum()
    missing = missing[missing > 0].sort_values(ascending=False)
    if missing.empty:
        return None
    fig, ax = plt.subplots(figsize=(8, max(2.5, 0.45 * len(missing))))
    sns.barplot(x=missing.values, y=missing.index, hue=missing.index,
                palette="Reds_r", legend=False, ax=ax)
    ax.set_title("Missing Values by Column", fontweight="bold")
    ax.set_xlabel("Missing count")
    ax.set_ylabel("")
    return fig


def iqr_table(df):
    rows = []
    targets = {
        "Movie runtime (minutes)": df.loc[df["is_movie"], "duration_value"].dropna(),
        "TV show seasons": df.loc[~df["is_movie"], "duration_value"].dropna(),
        "Cast size": df["num_cast"].astype(float),
        "Release year": df["release_year"].astype(float),
        "Genres per title": df["num_genres"].astype(float),
    }
    for label, series in targets.items():
        if series.empty:
            continue
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr = q3 - q1
        low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        mask = (series < low) | (series > high)
        rows.append(
            {
                "Feature": label,
                "Q1": round(float(q1), 2),
                "Q3": round(float(q3), 2),
                "IQR": round(float(iqr), 2),
                "Lower fence": round(float(low), 2),
                "Upper fence": round(float(high), 2),
                "Outliers": int(mask.sum()),
                "Outlier %": round(float(mask.mean() * 100), 2),
            }
        )
    return pd.DataFrame(rows)


def sidebar(df):
    st.sidebar.title("🎬 Netflix EDA")
    st.sidebar.caption("Filter the catalogue, then explore every tab.")

    all_types = [t for t in TYPE_ORDER if t in set(df["type"])]
    all_genres = sorted(exploded_genres(df).unique())
    all_countries = sorted(df["primary_country"].unique())
    all_ratings = sorted(df["rating"].dropna().unique())
    ymin, ymax = int(df["release_year"].min()), int(df["release_year"].max())
    if ymin >= ymax:
        ymax = ymin + 1

    if st.sidebar.button("↺ Reset filters"):
        for k in FILTER_KEYS:
            st.session_state.pop(k, None)
        st.rerun()

    st.sidebar.divider()
    types = st.sidebar.multiselect("Content type", all_types, default=all_types, key="f_types")
    years = st.sidebar.slider(
        "Release year range", ymin, ymax, (ymin, ymax), key="f_years"
    )
    genres = st.sidebar.multiselect("Genres", all_genres, default=all_genres, key="f_genres")
    countries = st.sidebar.multiselect(
        "Primary country", all_countries, default=all_countries, key="f_countries"
    )
    ratings = st.sidebar.multiselect("Rating", all_ratings, default=all_ratings, key="f_ratings")

    st.sidebar.divider()
    st.sidebar.metric("Titles in view", f"{len(df):,}")

    if not types or not genres or not countries or not ratings:
        st.warning("Select at least one value in every filter to see results.")
        st.stop()

    return apply_filters(df, types, years, genres, countries, ratings)


def overview(df, raw):
    st.subheader("Dataset Overview")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Titles", f"{len(df):,}")
    c2.metric("Distinct genres", f"{exploded_genres(df).nunique()}")
    c3.metric("Countries", f"{df['primary_country'].nunique()}")
    c4.metric("Year range", f"{df['release_year'].min()}-{df['release_year'].max()}")
    c5.metric("Genres / title", f"{df['num_genres'].mean():.2f}")

    st.markdown("#### Content type split")
    left, right = st.columns([1, 2])
    with left:
        show(fig_type_distribution(df))
    with right:
        counts = df["type"].value_counts()
        summary = pd.DataFrame(
            {
                "Titles": counts,
                "Share %": (counts / len(df) * 100).round(2),
                "Median year": df.groupby("type")["release_year"].median(),
                "Avg genres": df.groupby("type")["num_genres"].mean().round(2),
                "Avg cast": df.groupby("type")["num_cast"].mean().round(2),
            }
        )
        st.dataframe(summary)

    st.markdown("#### Column types")
    scal = [c for c in df.columns if c != "genres"]
    dtypes = pd.DataFrame(
        {
            "dtype": df[scal].dtypes.astype(str),
            "non-null": df[scal].notna().sum(),
            "null": df[scal].isna().sum(),
            "unique": df[scal].nunique(dropna=True),
        }
    )
    st.dataframe(dtypes)

    st.markdown("#### Sample records")
    sample = df.head(10)[["show_id", "type", "title", "director", "country",
                         "release_year", "rating", "duration", "listed_in"]]
    st.dataframe(sample, hide_index=True)


def data_quality(df, raw):
    st.subheader("Data Quality")

    a, b, c = st.columns(3)
    a.metric("Rows loaded", f"{len(raw):,}")
    dup_frame = raw.drop(columns=["genres"], errors="ignore")
    b.metric("Fully duplicated rows", f"{int(dup_frame.duplicated().sum()):,}")
    c.metric("Rows after cleaning", f"{len(df):,}")

    st.markdown("#### Missing values")
    fig = fig_missing(raw)
    if fig is None:
        st.success("No missing values detected.")
    else:
        show(fig)
        missing = raw.isna().sum()
        missing = missing[missing > 0].sort_values(ascending=False)
        report = pd.DataFrame(
            {
                "Missing": missing,
                "Missing %": (missing / len(raw) * 100).round(2),
            }
        )
        st.dataframe(report, hide_index=True)

    st.markdown("#### Duplicates")
    key = ["title", "type", "release_year"]
    dupes = raw[raw.duplicated(subset=key, keep=False)].sort_values(key)
    st.write(
        f"Duplicate check on `{'`, `'.join(key)}`: **{int(raw.duplicated(subset=key).sum()):,}** "
        "redundant rows removed during cleaning."
    )
    if not dupes.empty:
        with st.expander("Show duplicate records"):
            st.dataframe(
                dupes[["show_id", "title", "type", "release_year"]].head(100),
                hide_index=True,
            )

    st.markdown("#### Cleaning steps applied")
    st.markdown(
        """
        - Dropped rows missing `show_id`, `type`, `title` or `release_year`
        - Removed duplicate `show_id` values and duplicate (title, type, year) combinations
        - Normalised `type` casing so `tv show` / `Tv Show` / `TV Show` collapse to one value
        - Coerced `release_year` to integer and filtered to 1925-2021
        - Parsed `date_added` into a datetime and split `duration` into value + unit
        - Split `listed_in`, `cast` and `country` into genre, cast-size and primary-country fields
        """
    )


def genres_tab(df):
    st.subheader("Genre Analysis")
    ex = df[["type", "genres"]].explode("genres").dropna(subset=["genres"])
    counts = ex["genres"].value_counts()

    a, b, c, d = st.columns(4)
    a.metric("Genre tags", f"{len(ex):,}")
    b.metric("Distinct genres", f"{counts.size}")
    c.metric("Avg genres / title", f"{df['num_genres'].mean():.2f}")
    d.metric("Most common", counts.index[0] if len(counts) else "n/a")

    left, right = st.columns(2)
    with left:
        show(fig_top_genres(df))
    with right:
        show(fig_genres_by_type(df))

    st.markdown("#### Top genres table")
    top = counts.head(20)
    st.dataframe(
        pd.DataFrame({"Titles": top, "Share %": (top / len(df) * 100).round(2)}),
        hide_index=True,
    )

    st.markdown("#### Genres per title")
    buckets = pd.cut(df["num_genres"], [-1, 0, 1, 2, 3], labels=["0", "1", "2", "3+"])
    bcounts = buckets.value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.barplot(x=bcounts.index.astype(str), y=bcounts.values, color="#E50914", ax=ax)
    ax.set_title("How many genres per title", fontweight="bold")
    ax.set_xlabel("Number of genres")
    ax.set_ylabel("Titles")
    show(fig)


def types_tab(df):
    st.subheader("Movies vs TV Shows")
    counts = df["type"].value_counts()
    show(fig_type_distribution(df))

    st.markdown("#### Comparison")
    table = df.groupby("type").agg(
        titles=("show_id", "count"),
        first_year=("release_year", "min"),
        last_year=("release_year", "max"),
        median_year=("release_year", "median"),
        avg_genres=("num_genres", "mean"),
        avg_cast=("num_cast", "mean"),
        countries=("primary_country", "nunique"),
        median_duration=("duration_value", "median"),
    ).round(2)
    st.dataframe(table)

    for content_type in TYPE_ORDER:
        if content_type not in set(df["type"]):
            continue
        subset = df[df["type"] == content_type]
        with st.expander(f"Top 10 {content_type} genres"):
            top = subset[["genres"]].explode("genres").dropna(subset=["genres"])["genres"]
            top = top.value_counts().head(10)
            st.dataframe(
                pd.DataFrame({"Titles": top, "Share %": (top / len(subset) * 100).round(2)}),
                hide_index=True,
            )


def years_tab(df):
    st.subheader("Release Year Analysis")
    a, b, c = st.columns(3)
    a.metric("Earliest", f"{df['release_year'].min()}")
    b.metric("Latest", f"{df['release_year'].max()}")
    recent = int((df["release_year"] >= 2015).sum())
    c.metric("From 2015+", f"{recent:,} ({recent / len(df) * 100:.1f}%)")

    show(fig_releases_by_year(df))
    left, right = st.columns(2)
    with left:
        show(fig_year_histogram(df))
    with right:
        fig = fig_monthly_additions(df)
        if fig is not None:
            show(fig)

    st.markdown("#### Decade buckets")
    decade = pd.cut(
        df["release_year"],
        [1924, 1989, 1999, 2009, 2014, 2016, 2018, REFERENCE_YEAR],
        labels=["<1990", "1990s", "2000s", "2010-14", "2015-16", "2017-18", "2019-21"],
    )
    dcounts = decade.value_counts().sort_index()
    st.dataframe(
        pd.DataFrame({"Titles": dcounts, "Share %": (dcounts / len(df) * 100).round(2)}),
        hide_index=True,
    )

    st.markdown("#### Titles per year by type")
    pivot = df.pivot_table(index="release_year", columns="type",
                           values="show_id", aggfunc="count").fillna(0).astype(int)
    st.dataframe(pivot.tail(15))


def countries_tab(df):
    st.subheader("Country Analysis")
    counts = df["primary_country"].value_counts()
    a, b, c = st.columns(3)
    a.metric("Distinct countries", f"{counts.size}")
    b.metric("Top country", counts.index[0] if len(counts) else "n/a")
    c.metric("Single-title countries", f"{int((counts == 1).sum())}")

    left, right = st.columns(2)
    with left:
        show(fig_top_countries(df))
    with right:
        show(fig_country_share(df))

    st.markdown("#### Top 20 countries")
    top = counts.head(20)
    st.dataframe(
        pd.DataFrame({"Titles": top, "Share %": (top / len(df) * 100).round(2)}),
        hide_index=True,
    )

    st.markdown("#### Movies vs TV shows by country (top 12)")
    pivot = (
        df[["primary_country", "type"]]
        .assign(n=1)
        .pivot_table(index="primary_country", columns="type", values="n", aggfunc="sum")
        .fillna(0)
        .astype(int)
    )
    pivot = pivot.loc[pivot.index.isin(top.head(12).index)]
    cols = [c for c in TYPE_ORDER if c in pivot.columns]
    st.dataframe(pivot.sort_values(by=cols, ascending=False))


def duration_tab(df):
    st.subheader("Duration & Ratings")
    a, b, c = st.columns(3)
    movies = df[df["type"] == "Movie"]
    shows = df[df["type"] == "TV Show"]
    a.metric("Median runtime", f"{movies['duration_value'].median():.0f} min" if not movies.empty else "n/a")
    b.metric("Median seasons", f"{shows['duration_value'].median():.0f}" if not shows.empty else "n/a")
    c.metric("Most common rating", df["rating"].mode().iloc[0] if df["rating"].notna().any() else "n/a")

    st.caption(
        "`duration` mixes units: minutes for movies, seasons for TV shows. "
        "The two are charted separately and never pooled."
    )
    show(fig_duration_box(df))

    left, right = st.columns(2)
    with left:
        show(fig_rating_distribution(df))
    with right:
        show(fig_cast_box(df))

    st.markdown("#### Rating distribution")
    rc = df["rating"].value_counts()
    st.dataframe(
        pd.DataFrame({"Titles": rc, "Share %": (rc / len(df) * 100).round(2)}),
        hide_index=True,
    )


def correlations_tab(df):
    st.subheader("Correlations & Outliers")
    numeric = ["release_year", "content_age", "duration_value", "num_cast", "num_genres"]
    numeric = [c for c in numeric if df[c].notna().any()]

    if len(numeric) < 2:
        st.warning("Not enough numeric columns in the current selection to correlate.")
        return

    left, right = st.columns(2)
    with left:
        show(fig_corr_heatmap(df, numeric))
    with right:
        x_col = st.selectbox("X axis", numeric, index=0)
        y_options = [c for c in numeric if c != x_col]
        y_col = st.selectbox("Y axis", y_options, index=0)
        color_col = st.selectbox("Colour by", ["type", "None"])
        fig = fig_scatter(df, x_col, y_col, None if color_col == "None" else color_col)
        if fig is not None:
            show(fig)

    st.caption(
        "`duration_value` is minutes for movies and seasons for shows, so pooled "
        "correlations involving it are not meaningful. Filter to a single type to read them."
    )

    st.markdown("#### Correlation by content type")
    for content_type in TYPE_ORDER:
        subset = df[df["type"] == content_type]
        if subset.empty:
            continue
        unit = "minutes" if content_type == "Movie" else "seasons"
        st.markdown(f"**{content_type}** (duration = {unit})")
        st.dataframe(subset[numeric].corr(numeric_only=True).round(3))

    st.markdown("#### Outliers (IQR method, 1.5 x IQR)")
    table = iqr_table(df)
    if table.empty:
        st.info("Not enough data to compute outliers.")
    else:
        st.dataframe(table, hide_index=True)
        st.caption(
            "Box plots in the Duration & Ratings tab visualise these fences. "
            "Very short or very long runtimes and large casts are the usual outliers."
        )


def download_tab(df):
    st.subheader("Export")
    st.write("Download the currently filtered subset as CSV.")
    export = df.drop(columns=["genres"], errors="ignore")
    csv = export.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇ Download filtered data",
        data=csv,
        file_name="netflix_filtered.csv",
        mime="text/csv",
    )
    st.write(f"Rows: **{len(export):,}** · Columns: **{export.shape[1]}**")
    st.dataframe(export.head(25), hide_index=True)


def main():
    st.title("Netflix Content Analysis & Exploratory Data Analysis")
    st.caption(
        "Shape · dtypes · missing values · duplicates · distributions · "
        "statistics · correlations · outliers · visualisations"
    )

    try:
        raw = get_data()
    except FileNotFoundError:
        st.error("`netflix_titles.csv` was not found next to `app.py`.")
        if st.button("Download the real dataset now"):
            from download_data import download

            with st.spinner("Downloading..."):
                download()
            get_data.clear()
            st.rerun()
        st.stop()
    except Exception as exc:
        st.exception(exc)
        st.stop()

    filtered = sidebar(raw)
    if filtered.empty:
        st.warning("No titles match the current filters. Try widening the year range.")
        st.stop()

    st.caption(f"Showing **{len(filtered):,}** of **{len(raw):,}** titles")

    tabs = st.tabs(
        [
            "📊 Overview",
            "🧹 Data Quality",
            "🎭 Genres",
            "🎬 Movies vs TV",
            "📅 Release Years",
            "🌍 Countries",
            "⏱ Duration & Ratings",
            "🔗 Correlations & Outliers",
            "⬇ Export",
        ]
    )
    with tabs[0]:
        overview(filtered, raw)
    with tabs[1]:
        data_quality(filtered, raw)
    with tabs[2]:
        genres_tab(filtered)
    with tabs[3]:
        types_tab(filtered)
    with tabs[4]:
        years_tab(filtered)
    with tabs[5]:
        countries_tab(filtered)
    with tabs[6]:
        duration_tab(filtered)
    with tabs[7]:
        correlations_tab(filtered)
    with tabs[8]:
        download_tab(filtered)


main()
