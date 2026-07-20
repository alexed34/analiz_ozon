# AGENTS.md

## Repo structure

```
├── index.html           # Landing page with dashboard links + feedback form
├── dashboard.html       # Self-contained ECharts dashboard (22 charts)
├── test.csv             # 100-row subset, raw numbers
├── data.csv             # Raw Ozon export (formatted), ~10K rows
├── data2.csv            # Same schema as data.csv, different export
├── data.xlsx            # Same data, loaded by dashboard
├── описание столбцов.txt   # Column descriptions (Russian)
└── визуализации_рынка_кофе.md  # Reference doc for charts (already implemented)
```

## Data quirks

- CSV delimiter is `;` (not comma), decimal separator is `,` (`0,06` = 0.06)
- `0001-01-01` dates = missing/unknown; empty numeric cells = 0
- `Категория 3 уровня` = coffee type: `Кофе растворимый`, `Кофе в зернах`, `Кофе молотый`
- `data.csv`/`data2.csv` share the same schema; **row 2 is column descriptions (skip it)**
- `data.csv`/`data2.csv`: formatted numbers (`1 003 ₽`), percentages (`2.3%`), days as `X из 28`
- `test.csv`: raw numbers (`1003`), decimal (`0.023`), raw days (`28`), extra columns (`год`, `месяц`, `Категория_веса`, `Категория_цена`, `Дней c остатком`). No description row. Uses `Средняя цена, ₽` instead of `Средняя цена покупки, ₽`.

## Dashboard (dashboard.html)

- Self-contained HTML, no build step — serve with `python -m http.server 8080`, `npx serve .`, or Live Server
- Uses **ECharts.js** (CDN) + **SheetJS** for XLSX parsing; loads `data.xlsx` via `fetch()` — **will not work from `file://`**
- 22 charts, single page with filters bar, KPI row, chart grid
- Cross-filtering: clicking category/brand charts fills the corresponding filter
- Filters saved to `localStorage`, restored on reload

## Feedback form (index.html)

- Form submits to Web3Forms API (`https://api.web3forms.com/submit`) via JS `fetch()`
- **Setup required**: register at web3forms.com, replace both `ВАШ_КЛЮЧ_С_WEB3FORMS` in `index.html` with real access key
- Shows "Спасибо за сообщение!" on success; error message on failure

## No tooling

No `package.json`, no linter, no formatter, no test runner, no CI. Pure static files.
