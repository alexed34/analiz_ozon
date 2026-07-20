# AGENTS.md

## Repo structure

```
├── index.html           # Landing page with dashboard links + feedback form
├── dashboard.html       # Self-contained ECharts dashboard (28 charts)
├── data.xlsx            # Live data source for the dashboard (Ozon export, ~10K rows)
├── data2.xlsx           # Parallel export, same schema — for manual reference/comparison
├── описание столбцов.txt   # Column descriptions (Russian)
└── визуализации_рынка_кофе.md  # Reference doc for charts (already implemented)
```

## Data quirks

- The dashboard reads **`data.xlsx`** (not CSV). `data2.xlsx` is a sibling export, same schema, not loaded by the app.
- `dashboard.html` auto-detects the header row (searches for `Название товара`) and skips the period/description rows above it — no manual row-skipping needed when editing the sheet.
- `0001-01-01` dates = missing/unknown; empty numeric cells = 0.
- `Категория 3 уровня` = coffee type: `Кофе растворимый`, `Кофе в зернах`, `Кофе молотый`.
- Cells may hold formatted values: numbers with ` ₽`/` ` thousands separators, percentages (`2.3%`), days as `X из 28`. The parser normalizes these to `_num` fields; edit the sheet as-is, don't pre-clean.

## Dashboard (dashboard.html)

- Self-contained HTML, no build step — serve with `python -m http.server 8080`, `npx serve .`, or Live Server
- Uses **ECharts.js** (CDN) + **SheetJS** for XLSX parsing; loads `data.xlsx` via `fetch()` — **will not work from `file://`**
- 28 charts (see `renderCharts()` in dashboard.html), single page with filters bar, KPI row, chart grid
- Cross-filtering: clicking category/brand charts fills the corresponding filter
- Filters saved to `localStorage`, restored on reload

## Feedback form (index.html)

- Form submits to Web3Forms API (`https://api.web3forms.com/submit`) via JS `fetch()`
- **Setup required**: register at web3forms.com, replace both `ВАШ_КЛЮЧ_С_WEB3FORMS` in `index.html` with real access key
- Shows "Спасибо за сообщение!" on success; error message on failure

## No tooling

No `package.json`, no linter, no formatter, no test runner, no CI. Pure static files.
