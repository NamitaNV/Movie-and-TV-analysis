# 🎬 Netflix Movies & TV Shows — Exploratory Data Analysis

An end-to-end exploratory data analysis of the **real Netflix catalogue** (8,807 titles),
combining a reproducible analysis script, a set of publication-ready charts, an
interactive Streamlit dashboard, and a packaged Tableau dashboard.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![pandas](https://img.shields.io/badge/pandas-2.x-150458?logo=pandas&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32%2B-FF4B4B?logo=streamlit&logoColor=white)
![Tableau](https://img.shields.io/badge/Tableau-Dashboard-E97627?logo=tableau&logoColor=white)
![Dataset](https://img.shields.io/badge/Dataset-8%2C807%20titles-E50914)

---

## 📌 Overview

This project explores what Netflix's catalogue actually looks like: how movies and TV shows
are balanced, which genres and countries dominate, how the library grew over time, how long
content runs, which ratings are most common, and where the data is incomplete.

It contains **three ways to explore the data**:

| Entry point | What it does |
|---|---|
| `tableau/Netflix_Catalogue_Dashboard.twbx` | Packaged Tableau dashboard (open in Tableau Desktop or Public) |
| `app.py` | Interactive Streamlit dashboard with sidebar filters and 9 analysis tabs |
| `eda_netflix.py` | Scripted analysis that prints a full report and saves 18 charts to `output/` |

---

## 📂 Dataset

**Netflix Movies and TV Shows** — originally published on
[Kaggle](https://www.kaggle.com/datasets/shivamb/netflix-shows) by Shivam Bansal.

| Property | Value |
|---|---|
| Rows | 8,807 |
| Columns | 12 |
| Snapshot | September 2021 |
| Movies / TV Shows | 6,131 / 2,676 |
| Release years | 1925 – 2021 |
| File | `netflix_titles.csv` (UTF-8) |

Columns: `show_id`, `type`, `title`, `director`, `cast`, `country`, `date_added`,
`release_year`, `rating`, `duration`, `listed_in`, `description`.

The CSV is committed to the repository, so **no Kaggle account is required**.
To refresh it, run `python download_data.py`, which downloads and validates the file from a
public mirror (with the TidyTuesday snapshot as a fallback).

---

## 🔍 Key Findings

- **Movies dominate:** 6,131 movies (69.6%) vs 2,676 TV shows (30.4%).
- **The catalogue is recent:** 6,216 titles (70.6%) were released in 2015 or later.
- **International content leads genres:** *International Movies* appears on 2,752 titles
  (31.2%), followed by *Dramas* (2,427) and *Comedies* (1,674).
- **The US is the largest producer:** 3,211 titles (36.5%), followed by India and the UK.
- **Mature content dominates:** `TV-MA` is the most common rating.
- **Typical runtime:** the median movie is **98 minutes**; the median TV show has **1 season**.
- **Fastest growth:** July 2021 was the busiest month, with 257 titles added.
- **Data gaps:** 2,634 titles lack a director (29.9%), 831 lack a country (9.4%),
  825 lack cast information (9.4%), and a handful lack a rating or duration.

---

## 📁 Project Structure

```
Movie-and-TV-analysis/
├── app.py                        # Streamlit dashboard
├── eda_netflix.py                # Scripted EDA + chart generation
├── download_data.py              # Downloads & validates the real dataset
├── prepare_tableau_data.py       # Builds Tableau-ready CSV tables
├── build_tableau_workbook.py     # Generates the packaged Tableau workbook
├── netflix_titles.csv            # Real Netflix catalogue (8,807 rows)
├── requirements.txt              # Python dependencies
├── .gitattributes                # marks .twbx as binary, .twb as text
├── output/                       # 18 generated charts (PNG)
├── tableau/
│   ├── Netflix_Catalogue_Dashboard.twbx   # Open this in Tableau
│   ├── Netflix_Catalogue_Dashboard.twb    # Workbook XML (loose files)
│   └── Data/Netflix/             # titles.csv, genres.csv, countries.csv
└── README.md
```

### Generated charts

| File | Analysis |
|---|---|
| `01_type_distribution.png` | Movies vs TV shows |
| `02_top_genres.png` | Top 15 genres |
| `03_genres_by_type.png` | Top genres split by content type |
| `03_missing_values.png` | Missing values by column |
| `04_releases_by_year.png` | Titles by release year |
| `05_release_year_histogram.png` | Release-year distribution |
| `06_monthly_additions.png` | Titles added per month |
| `07_top_countries.png` | Top 15 countries |
| `08_country_share.png` | Share of titles by country |
| `09_rating_distribution.png` | Content ratings |
| `10_titles_per_year.png` | Titles per year since 2005 |
| `11_correlation_heatmap.png` | Numeric feature correlations |
| `12_duration_boxplot.png` | Runtime / season outliers |
| `13_cast_size_boxplot.png` | Cast-size outliers |
| `14_scatter_year_vs_duration.png` | Runtime & cast vs release year |
| `15_scatter_genres_cast.png` | Genres & cast relationships |
| `16_scatter_duration_by_type.png` | Duration by content type |
| `17_creators.png` | Top directors and TV actors |

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/NamitaNV/Movie-and-TV-analysis.git
cd Movie-and-TV-analysis
```

### 2. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 3. Run the interactive dashboard

```bash
python -m streamlit run app.py
```

Open **http://localhost:8501** if the browser does not open automatically.
Press `Ctrl + C` in the terminal to stop it.

### 4. Open the Tableau dashboard

Double-click `tableau/Netflix_Catalogue_Dashboard.twbx`, or open it from
**Tableau Desktop / Tableau Public → File → Open**. The CSV tables are bundled
inside the `.twbx`. See `tableau/README.md` for the sheet inventory and rebuild steps.

### 5. Run the scripted analysis

```bash
python eda_netflix.py
```

The report is printed to the terminal and all charts are written to `output/`.

### 6. (Optional) Re-download the dataset

```bash
python download_data.py
```

---

## 📊 Dashboard Tabs

1. **Overview** — headline metrics, content split, column profile, sample rows
2. **Data Quality** — missing values, duplicates, cleaning steps
3. **Genres** — top genres, genre mix by type, genres per title
4. **Movies vs TV** — side-by-side comparison and top genres per type
5. **Release Years** — yearly trends, decade buckets, monthly additions
6. **Countries** — top producers and country share
7. **Duration & Ratings** — runtime/season distributions and rating mix
8. **Correlations & Outliers** — correlation heatmaps, scatter plots, IQR outlier table
9. **Export** — download the currently filtered subset as CSV

Filters in the sidebar (content type, year range, genre, country, rating) apply across every tab.

---

## 🟧 Tableau Dashboard

The packaged workbook **`tableau/Netflix_Catalogue_Dashboard.twbx`** is a self-contained
Tableau dashboard. Double-click it, or open it with **Tableau Desktop 2021.4+** or
**Tableau Public** — the data travels inside the `.twbx`, so no CSV setup is required.

It contains **3 data sources, 11 worksheets and 1 dashboard**. The full sheet inventory
(marks, fields and filters) is documented in [`tableau/README.md`](tableau/README.md).

**Layout (1400 × 900, fixed):**

| Area | Visual |
|---|---|
| Header | Title + dataset snapshot |
| KPI strip | Total titles, movies, TV shows, median movie runtime, countries |
| Top row | Titles added per year (line), movies vs TV shows (pie), top 10 countries (bar) |
| Bottom row | Top 10 genres (bar), ratings mix (bar), titles by decade (stacked bar) |

**Data model:** the workbook uses three Tableau text connections generated from the
cleaned catalogue:

| Table | Grain | Used for |
|---|---|---|
| `titles.csv` | one row per title | KPIs, year trend, ratings, decade mix |
| `genres.csv` | one row per title/genre | accurate top-genre counts (multi-genre titles counted once per genre) |
| `countries.csv` | one row per title/country | accurate top-country counts (multi-country titles counted once per country) |

Keeping genres and countries in separate long tables avoids the undercounting you get
from splitting only the first value of each comma-separated list. Country bars therefore
count **every credited country** (a co-production appears under each): the US shows 3,690
titles here versus 3,211 in the primary-country figures quoted above. Missing country
values are excluded, which leaves **122** countries for the KPI card.

**Rebuild after changing the source data:**

```bash
python prepare_tableau_data.py      # writes tableau/Data/Netflix/*.csv
python build_tableau_workbook.py    # writes .twb + .twbx
```

`build_tableau_workbook.py` regenerates the workbook XML from scratch, so all formatting
and layout live in version control. The generated workbook targets the **Tableau 2021.4**
workbook schema so it opens in 2021.4 and every later release; the newer `<explain-data>`
block is deliberately omitted for that backward compatibility, and sorting uses the
long-standing `<computed-sort>` element rather than the newer `<shelf-sorts>`.

---

## 🧹 Data Cleaning & Feature Engineering

The pipeline applies the following steps:

- Removed rows missing `show_id`, `type`, `title`, or `release_year`
- Removed duplicate `show_id`s and duplicate `(title, type, release_year)` combinations
- Normalised `type` casing (`tv show` → `TV Show`)
- Parsed `date_added` into a datetime (handles both full and abbreviated month names)
- Split `duration` into a numeric value and a unit (minutes vs seasons)
- Derived `added_year`, `added_month`, `content_age`, `is_movie`, `num_cast`,
  `num_genres`, `primary_country`, and `genres`

### Caveats

- `duration` mixes units: **minutes** for movies and **seasons** for TV shows. The two are
  analysed separately and never pooled in correlations.
- Correlation does not imply causation; the numeric features are mostly descriptive.
- Missing directors/cast/country values are retained rather than imputed, and are surfaced
  explicitly in the Data Quality view.

---

## 🛠️ Tech Stack

- **Python 3.10+**
- **pandas** — data loading, cleaning, aggregation
- **NumPy** — numerical operations
- **Matplotlib / Seaborn** — static charts
- **Streamlit** — interactive dashboard
- **Tableau** — packaged BI dashboard (`.twbx`)

---

## 👤 Author

**Namita NV**
GitHub: [@NamitaNV](https://github.com/NamitaNV)

---

## 📄 Data Attribution

Dataset: *Netflix Movies and TV Shows* by Shivam Bansal, sourced from Kaggle and mirrored
publicly for reproducibility. Netflix branding and title metadata belong to their respective
owners; this project is for educational and analytical purposes only.
