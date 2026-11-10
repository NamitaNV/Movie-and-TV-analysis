# 🎬 Netflix Movies & TV Shows — Exploratory Data Analysis

An end-to-end exploratory data analysis of the **real Netflix catalogue** (8,807 titles),
combining a reproducible analysis script, a set of publication-ready charts, and an
interactive Streamlit dashboard.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![pandas](https://img.shields.io/badge/pandas-2.x-150458?logo=pandas&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32%2B-FF4B4B?logo=streamlit&logoColor=white)
![Dataset](https://img.shields.io/badge/Dataset-8%2C807%20titles-E50914)

---

## 📌 Overview

This project explores what Netflix's catalogue actually looks like: how movies and TV shows
are balanced, which genres and countries dominate, how the library grew over time, how long
content runs, which ratings are most common, and where the data is incomplete.

It contains **two ways to explore the data**:

| Entry point | What it does |
|---|---|
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
├── app.py                  # Streamlit dashboard
├── eda_netflix.py          # Scripted EDA + chart generation
├── download_data.py        # Downloads & validates the real dataset
├── netflix_titles.csv      # Real Netflix catalogue (8,807 rows)
├── requirements.txt        # Python dependencies
├── output/                 # 18 generated charts (PNG)
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

### 4. Run the scripted analysis

```bash
python eda_netflix.py
```

The report is printed to the terminal and all charts are written to `output/`.

### 5. (Optional) Re-download the dataset

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

---

## 👤 Author

**Namita NV**
GitHub: [@NamitaNV](https://github.com/NamitaNV)

---

## 📄 Data Attribution

Dataset: *Netflix Movies and TV Shows* by Shivam Bansal, sourced from Kaggle and mirrored
publicly for reproducibility. Netflix branding and title metadata belong to their respective
owners; this project is for educational and analytical purposes only.
