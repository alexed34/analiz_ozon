# AGENTS.md

## Repo structure

```
├── test.csv                  # 100-row subset, raw numbers
├── data.csv                  # Raw Ozon export (formatted), ~10K rows
├── data2.csv                 # Same schema as data.csv, different export
├── data.xlsx                 # Same data, loaded by dashboard
├── описание столбцов.txt     # Column descriptions (Russian)
├── визуализации_рынка_кофе.md  # 22 viz recommendations (reference doc)
└── dashboard.html            # Self-contained ECharts dashboard
```

## Data quirks

- CSV delimiter is `;` (not comma)
- Comma is decimal separator (Russian locale: `0,06` = 0.06)
- `0001-01-01` dates = missing/unknown
- Numeric columns may be empty (treat as 0)
- `Категория 3 уровня` = coffee type: `Кофе растворимый`, `Кофе в зернах`, `Кофе молотый`

## Three CSV files, two formats

| File | Rows | Numbers | Percentages | Days | Extra columns |
|------|------|---------|-------------|------|---------------|
| `test.csv` | 100 | raw (`1003`) | decimal (`0.023`) | raw (`28`) | `год`, `месяц`, `Категория_веса`, `Категория_цена`, `Дней c остатком` |
| `data.csv` | ~10K | formatted (`1 003 ₽`) | percent (`2.3%`) | `X из 28` | none |
| `data2.csv` | ~10K | formatted (`795 ₽`) | percent (`5.2%`) | `X из 28` | none |

`data.csv` and `data2.csv` share the same schema: row 2 is column descriptions (skip it). `test.csv` has no description row and uses `Средняя цена, ₽` instead of `Средняя цена покупки, ₽`.

## Dashboard

- Self-contained HTML, no build step — serves from any static HTTP server
- Uses **ECharts.js** (not Chart.js) from CDN + SheetJS for XLSX parsing
- Loads `data.xlsx` via `fetch()` — **will not work from `file://`**. Use `python -m http.server 8080`, `npx serve .`, or Live Server
- 12 charts (not 22 — the 22-viz doc is a separate reference, not implemented)
- No tabs: single page with filters bar, KPI row, and chart grid
- Cross-filtering: clicking category/brand charts auto-fills the corresponding filter
- Filters are saved to `localStorage` and restored on reload

## No tooling

No `package.json`, no linter, no formatter, no test runner. Pure static files.
