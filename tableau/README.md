# Tableau Dashboard

`Netflix_Catalogue_Dashboard.twbx` is a packaged Tableau workbook: the `.twb` definition
and all three CSV tables are bundled inside, so it opens on any machine with Tableau.

## Open it

1. Install **Tableau Desktop 2021.4 or newer** (or the latest **Tableau Public**).
2. Double-click `Netflix_Catalogue_Dashboard.twbx`.
3. If prompted, choose *Open* rather than extracting the archive.

Tableau Public users can also publish the workbook from *File → Save to Tableau Public*.

## What is inside

| Worksheet | Mark | Fields |
|---|---|---|
| KPI Total Titles | Text | `SUM(Number of Records)` |
| KPI Movies | Text | count, filtered `type = Movie` |
| KPI TV Shows | Text | count, filtered `type = TV Show` |
| KPI Movie Runtime | Text | `MEDIAN(duration_value)`, filtered to movies |
| KPI Countries | Text | `COUNTD(country)` from `countries.csv` |
| Titles Added per Year | Line | `added_year` × count |
| Movies vs TV Shows | Pie | `type` colour × count |
| Top 10 Countries | Bar | `country` × count, top-10 filter |
| Top 10 Genres | Bar | `genre` × count, top-10 filter |
| Ratings Mix | Bar | `rating` × count |
| Titles by Decade | Stacked bar | `decade` × count, coloured by `type` |

All of these are arranged on the **Netflix Catalogue Dashboard** worksheet.

## Rebuild

From the repository root:

```bash
python prepare_tableau_data.py
python build_tableau_workbook.py
```

`prepare_tableau_data.py` reuses the cleaning pipeline in `eda_netflix.py` and writes:

- `Data/Netflix/titles.csv` — one row per title
- `Data/Netflix/genres.csv` — one row per title/genre
- `Data/Netflix/countries.csv` — one row per title/country

`build_tableau_workbook.py` writes the `.twb` XML and zips it with the CSVs into the
`.twbx`. Edit the Python builder (not the `.twb`) when you want to change colours,
layout, titles, or add worksheets.

## Notes

- The dashboard is a fixed 1400 × 900 layout, designed for a laptop/desktop screen.
- `genres.csv` and `countries.csv` are intentionally long tables. A title with three
  genres contributes one row to each genre, which is what makes the top-genre and
  top-country bars match the EDA report.
- The KPI country count is a distinct count (122 countries); missing country values are excluded.
- Country bars count every credited country, so a co-production contributes to each country.
- The workbook is generated at TWB format version `18.1` with a Tableau 2021.4 build
  stamp, so Tableau Desktop 2021.4+ and current Tableau Public open it directly.
