# AGENTS.md

## Repo structure

```
├── index.html             # Landing page + Web3Forms feedback form
├── dashboard.html         # ECharts dashboard (28 charts) — loads data.json
├── data.xlsx              # Source: Ozon export (~10K rows, Russian columns)
├── data.json              # Pre-processed: JSON array-of-arrays, consumed by dashboard
├── parse_to_csv.py        # Pipeline: data.xlsx → data.json (derived columns + normalization)
├── headers.json           # Column names extracted from data.xlsx header row
├── описание столбцов.txt  # Column descriptions (Russian)
└── визуализации_рынка_кофе.md  # Reference doc for charts (already implemented)
```

## Data pipeline

- **`data.xlsx`** is the source of truth (Ozon export). Edit this when data changes.
- **`parse_to_csv.py`** converts `data.xlsx` → `data.json` (run manually). It:
  - Auto-detects header row by searching for `Название товара`, skips metadata rows above
  - Normalizes formatted cells (` ₽`, `X из 28`, `0001-01-01`, percentages)
  - Adds 16 derived columns (weight in grams, price categories, CTR, conversion, margin, etc.)
  - Outputs `data.json` as an array-of-arrays (period row, header row, data rows)
- After updating `data.xlsx`, run: `python parse_to_csv.py`
- **`data.json`** is what the dashboard actually loads (via `fetch('data.json?v=<hash>')`)
- `data2.xlsx` is a sibling export, same schema — **not** loaded by the app
- `~$data.xlsx` / `~$*.xlsx` is an Office temp/lock file — gitignored

## Dashboard (dashboard.html)

- Self-contained HTML, no build step — serve with `python -m http.server 8080`, `npx serve .`, or Live Server
- Uses **ECharts.js** (CDN only); reads `data.json` via `fetch()` — **will not work from `file://`**
- 28 charts (see `renderCharts()`), single page: filters bar, KPI row, chart grid
- Cross-filtering: clicking category/brand charts fills the corresponding filter
- Filters saved to `localStorage`, restored on reload
- Offline fallback: uses IndexedDB cache on network failure

## Feedback form (index.html)

- Posts to Web3Forms API via JS `fetch()`
- **Setup required**: register at web3forms.com, replace both `ВАШ_КЛЮЧ_С_WEB3FORMS` in `index.html` with real access key

## Data quirks

- `data.json` uses `openpyxl` with `data_only=True` — formulas become cached values
- `0001-01-01` dates = missing/unknown; empty numeric cells = `''` in JSON
- `Категория 3 уровня` = coffee type: `Кофе растворимый`, `Кофе в зернах`, `Кофе молотый`, etc.
- Cell formatting (currency, thousands separators, percentages, "X из 28") is handled by `normalize()` in `parse_to_csv.py` — edit the xlsx as-is, don't pre-clean

## No tooling

Pure static files: no package.json, no linter, no formatter, no test runner, no CI.
