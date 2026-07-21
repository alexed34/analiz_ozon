import openpyxl
import json
import sys
import re
import os
import gzip

sys.stdout.reconfigure(encoding='utf-8')

SRC = r'C:\Users\eduard2\pych-Opencode proekt\кофе\data.xlsx'
DST = r'C:\Users\eduard2\pych-Opencode proekt\кофе\data.json'

wb = openpyxl.load_workbook(SRC, data_only=True)
ws = wb.active

rows_iter = list(ws.iter_rows(values_only=True))

# Extract metadata from first rows
meta = {}
for i in range(min(5, len(rows_iter))):
    cell = str(rows_iter[i][0]).strip() if rows_iter[i] and rows_iter[i][0] else ''
    if cell.startswith('Период:'):
        meta['period'] = cell.replace('Период:', '').strip()
    elif cell.startswith('Категория:'):
        meta['categories'] = cell.replace('Категория:', '').strip()
    elif cell.startswith('Сортировка:'):
        meta['sorting'] = cell.replace('Сортировка:', '').strip()

header_idx = None
for i, row in enumerate(rows_iter):
    if row and any(cell and 'Название товара' in str(cell) for cell in row):
        header_idx = i
        break

if header_idx is None:
    print('ERROR: header row not found')
    sys.exit(1)

base_headers = [str(c).strip() if c else '' for c in rows_iter[header_idx]]
derived_headers = [
    'Вес_из_названия_г',
    'Категория_веса',
    'Категория_цены',
    'CTR_из_поиска_%',
    'Конверсия_в_покупку_%',
    'Конверсия_из_показа_%',
    'Цена_за_1_г_₽',
    'Маржа_цены_%',
    'Средний_чек_₽',
    'Выручка_на_показ_₽',
    'Выручка_на_визит_₽',
    'ADS_на_единицу_объема_₽_л',
    'Эффективность_схемы',
    'Дней_с_остатком',
    'Коэфф_дефицита_%',
    'Потенциальный_спрос_₽',
]
headers = base_headers + derived_headers
print(f'Header row: {header_idx + 1} (1-indexed)')
print(f'Columns ({len(headers)}):')
for j, h in enumerate(headers):
    print(f'  {j}: [{h}]')

print('=== Metadata ===')
for k, v in meta.items():
    print(f'  {k}: {v}')

# Skip description row (header_idx + 1), data starts from header_idx + 2
data_rows = []
for row in rows_iter[header_idx + 2:]:
    if not row or len(row) < 3:
        continue
    if all(c is None or str(c).strip() in ('', '—', '-') for c in row):
        continue
    name = str(row[0]).strip() if row[0] else ''
    if not name or name in ('—', '-'):
        continue
    data_rows.append(row)

print(f'\nTotal data rows: {len(data_rows)}')

def extract_weight_grams(name):
    matches = re.findall(r'(\d+(?:[.,]\s*\d+)?)\s*(кг|г|гр|грамм|грамма)', name.lower())
    if not matches:
        return ''
    weights = []
    for num_str, unit in matches:
        num_str = num_str.replace(',', '.').replace(' ', '')
        try:
            val = float(num_str)
        except ValueError:
            continue
        if unit in ('кг',):
            val *= 1000
        weights.append(val)
    if not weights:
        return ''
    return max(weights)

def classify_weight(w):
    if w == '' or w is None or w == 0:
        return ''
    if w >= 3000:
        return ''
    if w < 10:
        return '0-10 г'
    if w < 100:
        return '10-100 г'
    if w < 200:
        return '100-200 г'
    if w < 250:
        return '200-250 г'
    if w < 500:
        return '250-500 г'
    if w < 800:
        return '500-800 г'
    if w < 1000:
        return '800-1000 г'
    if w == 1000:
        return '1000 г'
    if w <= 2000:
        return '1000-2000 г'
    return '2000+ г'

def classify_price(p):
    if p == '' or p is None or p == 0:
        return ''
    if not isinstance(p, (int, float)):
        try:
            p = float(p)
        except (ValueError, TypeError):
            return ''
    if p < 500:
        return '0-500 ₽'
    if p < 800:
        return '500-800 ₽'
    if p < 1000:
        return '800-1000 ₽'
    if p < 1200:
        return '1000-1200 ₽'
    if p < 1500:
        return '1200-1500 ₽'
    if p < 2000:
        return '1500-2000 ₽'
    if p < 3000:
        return '2000-3000 ₽'
    if p < 5000:
        return '3000-5000 ₽'
    if p < 10000:
        return '5000-10000 ₽'
    return '10000+ ₽'

def safe_div(a, b):
    if a is None or a == '':
        return ''
    if a == 0:
        return 0.0
    if b is None or b == '' or b == 0:
        return ''
    if not isinstance(a, (int, float)):
        try:
            a = float(a)
        except (ValueError, TypeError):
            return ''
    if not isinstance(b, (int, float)):
        try:
            b = float(b)
        except (ValueError, TypeError):
            return ''
    return round(a / b, 4)

def normalize(val, col_idx):
    if val is None:
        return ''
    s = str(val)
    if s == '—' or s == '-' or s == '—':
        return ''
    # Parse "X из 28" in column 'Дней без остатка, дни' (col 14)
    if col_idx == 14 and 'из' in s:
        m = re.search(r'([\d\s]+)\s*из', s)
        if m:
            return int(m.group(1).replace(' ', ''))
        return s
    # Parse 0001-01-01 dates as empty
    if s == '0001-01-01':
        return ''
    return val

all_rows = []
if 'period' in meta:
    all_rows.append([f"Период: {meta['period']}"])
all_rows.append(headers)

for row in data_rows:
    name = str(row[0]).strip() if row[0] else ''
    weight = extract_weight_grams(name)
    weight_cat = classify_weight(weight)
    price_val = normalize(row[12] if len(row) > 12 else '', 12)
    price_cat = classify_price(price_val)
    norm = [normalize(row[j] if j < len(row) else '', j) for j in range(len(base_headers))]
    z = norm
    ctr = safe_div(z[22], z[21])
    conv_purchase = safe_div(z[10], z[22])
    conv_impression = safe_div(z[10], z[21])
    price_per_g = safe_div(z[12], weight)
    margin = safe_div(z[12] - z[11], z[12])
    avg_check = safe_div(z[8], z[10])
    rev_per_imp = safe_div(z[8], z[21])
    rev_per_visit = safe_div(z[8], z[22])
    ads_per_vol = safe_div(z[15], z[18])
    scheme_eff = (float(z[19]) - float(z[20]) if isinstance(z[19], (int, float)) and isinstance(z[20], (int, float)) else '')
    days_in_stock = (28 - z[14] if isinstance(z[14], (int, float)) else '')
    deficit = safe_div(z[13], (z[8] + z[13]) if isinstance(z[8], (int, float)) and isinstance(z[13], (int, float)) else 0)
    potential = (z[8] + z[13] if isinstance(z[8], (int, float)) and isinstance(z[13], (int, float)) else '')

    extras = [
        weight, weight_cat, price_cat,
        ctr * 100 if ctr != '' else '',
        conv_purchase * 100 if conv_purchase != '' else '',
        conv_impression * 100 if conv_impression != '' else '',
        price_per_g,
        margin * 100 if margin != '' else '',
        avg_check,
        rev_per_imp,
        rev_per_visit,
        ads_per_vol,
        scheme_eff,
        days_in_stock,
        deficit * 100 if deficit != '' else '',
        potential,
    ]
    all_rows.append(norm + extras)

with open(DST, 'w', encoding='utf-8') as f:
    json.dump(all_rows, f, ensure_ascii=False)

file_size = os.path.getsize(DST)
with open(DST, 'rb') as f_in:
    gz_size = len(gzip.compress(f_in.read()))

print(f'\nWritten to: {DST}')
print(f'File size: {file_size:,} bytes ({file_size/1024:.1f} KB)')
print(f'Gzip size: {gz_size:,} bytes ({gz_size/1024:.1f} KB, {gz_size/file_size*100:.0f}%)')

# === VERIFICATION ===
print(f'\n=== VERIFICATION: First 5 data rows (+ 16 derived columns) ===')
for idx, row in enumerate(data_rows[:5], 1):
    name = str(row[0]).strip() if row[0] else ''
    weight = extract_weight_grams(name)
    weight_cat = classify_weight(weight)
    price_val = normalize(row[12] if len(row) > 12 else '', 12)
    price_cat = classify_price(price_val)
    norm = [normalize(row[j] if j < len(row) else '', j) for j in range(len(base_headers))]
    z = norm
    ctr = safe_div(z[22], z[21])
    conv_purchase = safe_div(z[10], z[22])
    conv_impression = safe_div(z[10], z[21])
    price_per_g = safe_div(z[12], weight)
    margin = safe_div(z[12] - z[11], z[12])
    avg_check = safe_div(z[8], z[10])
    rev_per_imp = safe_div(z[8], z[21])
    rev_per_visit = safe_div(z[8], z[22])
    ads_per_vol = safe_div(z[15], z[18])
    scheme_eff = (float(z[19]) - float(z[20]) if isinstance(z[19], (int, float)) and isinstance(z[20], (int, float)) else '')
    days_in_stock = (28 - z[14] if isinstance(z[14], (int, float)) else '')
    deficit = safe_div(z[13], (z[8] + z[13]) if isinstance(z[8], (int, float)) and isinstance(z[13], (int, float)) else 0)
    potential = (z[8] + z[13] if isinstance(z[8], (int, float)) and isinstance(z[13], (int, float)) else '')
    extras = [
        weight, weight_cat, price_cat,
        ctr * 100 if ctr != '' else '',
        conv_purchase * 100 if conv_purchase != '' else '',
        conv_impression * 100 if conv_impression != '' else '',
        price_per_g,
        margin * 100 if margin != '' else '',
        avg_check,
        rev_per_imp,
        rev_per_visit,
        ads_per_vol,
        scheme_eff,
        days_in_stock,
        deficit * 100 if deficit != '' else '',
        potential,
    ]
    key_vals = [
        str(norm[0])[:40], str(weight), str(price_per_g), str(avg_check),
        str(days_in_stock), str(deficit * 100 if deficit != '' else '')[:8]
    ]
    print(f'Row {idx}: name={key_vals[0]}, вес={key_vals[1]}г, цена_за_1г={key_vals[2]}₽, ср.чек={key_vals[3]}₽, дней_в_наличии={key_vals[4]}, дефицит={key_vals[5]}%')

print('\n=== Categories ===')
cats = {}
for row in data_rows:
    cat = str(row[6]).strip() if len(row) > 6 and row[6] else ''
    if not cat or cat == '—':
        cat = '(empty)'
    cats[cat] = cats.get(cat, 0) + 1
for k, v in sorted(cats.items(), key=lambda x: -x[1]):
    print(f'  {k}: {v}')

print('\n=== Top 10 brands ===')
brands = {}
for row in data_rows:
    brand = str(row[4]).strip() if len(row) > 4 and row[4] else ''
    if not brand or brand == '—':
        brand = '(empty)'
    brands[brand] = brands.get(brand, 0) + 1
for k, v in sorted(brands.items(), key=lambda x: -x[1])[:10]:
    print(f'  {k}: {v}')

# Category_веса stats
print('\n=== Категория_веса distribution ===')
cat_bins = {}
outliers = 0
for row in data_rows:
    name = str(row[0]).strip() if row[0] else ''
    w = extract_weight_grams(name)
    c = classify_weight(w)
    if c:
        cat_bins[c] = cat_bins.get(c, 0) + 1
    elif w != '' and w != 0:
        outliers += 1
for label in ['0-10 г', '10-100 г', '100-200 г', '200-250 г', '250-500 г', '500-800 г', '800-1000 г', '1000 г', '1000-2000 г', '2000+ г']:
    cnt = cat_bins.get(label, 0)
    bar = '#' * (cnt // 40)
    print(f'  {label:>13s}: {cnt:>4d} {bar}')
if outliers:
    print(f'  Выбросы (>3000): {outliers}')

# Категория_цены stats
print('\n=== Категория_цены distribution ===')
price_bins = {}
for row in data_rows:
    price_val = normalize(row[12] if len(row) > 12 else '', 12)
    c = classify_price(price_val)
    if c:
        price_bins[c] = price_bins.get(c, 0) + 1
for label in ['0-500 ₽', '500-800 ₽', '800-1000 ₽', '1000-1200 ₽', '1200-1500 ₽', '1500-2000 ₽', '2000-3000 ₽', '3000-5000 ₽', '5000-10000 ₽', '10000+ ₽']:
    cnt = price_bins.get(label, 0)
    bar = '#' * (cnt // 30)
    print(f'  {label:>15s}: {cnt:>4d} {bar}')

# Stats on numeric columns
print('\n=== Column stats (original) ===')
numeric_samples = [8, 9, 10, 12, 14, 15, 21, 22]
for ci in numeric_samples:
    vals = []
    for row in data_rows:
        v = normalize(row[ci] if ci < len(row) else '', ci)
        if isinstance(v, (int, float)) and v != 0:
            vals.append(v)
    if vals:
        print(f'  {headers[ci]}: min={min(vals):.2f}, max={max(vals):.2f}, avg={sum(vals)/len(vals):.2f}, non-zero={len(vals)}')

print('\n=== Derived column stats ===')
ctr_vals, conv_vals, ppg_vals, check_vals, dis_vals, deficit_vals, pot_vals = [], [], [], [], [], [], []
for row in data_rows:
    name = str(row[0]).strip() if row[0] else ''
    weight = extract_weight_grams(name)
    norm = [normalize(row[j] if j < len(row) else '', j) for j in range(len(base_headers))]
    z = norm
    if isinstance(z[21], (int, float)) and z[21] != 0 and isinstance(z[22], (int, float)):
        ctr_vals.append(z[22] / z[21] * 100)
    if isinstance(z[22], (int, float)) and z[22] != 0 and isinstance(z[10], (int, float)):
        conv_vals.append(z[10] / z[22] * 100)
    if weight != '' and weight != 0 and isinstance(z[12], (int, float)):
        ppg_vals.append(z[12] / weight)
    if isinstance(z[8], (int, float)) and isinstance(z[10], (int, float)) and z[10] != 0:
        check_vals.append(z[8] / z[10])
    if isinstance(z[14], (int, float)):
        dis_vals.append(28 - z[14])
    if isinstance(z[8], (int, float)) and isinstance(z[13], (int, float)) and (z[8] + z[13]) != 0:
        deficit_vals.append(z[13] / (z[8] + z[13]) * 100)
        pot_vals.append(z[8] + z[13])
for label, vals in [
    ('CTR_из_поиска_%', ctr_vals),
    ('Конверсия_в_покупку_%', conv_vals),
    ('Цена_за_1_г_₽', ppg_vals),
    ('Средний_чек_₽', check_vals),
    ('Дней_с_остатком', dis_vals),
    ('Коэфф_дефицита_%', deficit_vals),
    ('Потенциальный_спрос_₽', pot_vals),
]:
    if vals:
        print(f'  {label}: min={min(vals):.4f}, max={max(vals):.4f}, avg={sum(vals)/len(vals):.4f}, n={len(vals)}')
