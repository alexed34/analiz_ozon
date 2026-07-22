"""
generate_dashboard_doc.py — обновляет описание_дашборда.md из dashboard.html

Извлекает CHART_DEFS и buildUI() sections из dashboard.html,
генерирует список графиков и вставляет между маркерами
<!-- CHART_LIST_START --> / <!-- CHART_LIST_END -->.

Запуск (из корня проекта):
    python scripts/generate_dashboard_doc.py
"""
import re
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(SCRIPT_DIR)
HTML_PATH = os.path.join(REPO_DIR, 'dashboard.html')
MD_PATH = os.path.join(REPO_DIR, 'описание_дашборда.md')


def skip_string(text, i):
    """Пропускает строковый литерал начиная с i (кавычка или апостроф)."""
    quote = text[i]
    i += 1
    while i < len(text):
        if text[i] == '\\':
            i += 2
            continue
        if text[i] == quote:
            return i + 1
        i += 1
    return i


def find_matching(text, start, open_ch, close_ch):
    """Ищет парный close_ch для open_ch на позиции start."""
    assert text[start] == open_ch
    depth = 1
    i = start + 1
    while i < len(text) and depth > 0:
        ch = text[i]
        if ch in '"\'':
            i = skip_string(text, i)
            continue
        if text[i:i+2] == '//':
            nl = text.find('\n', i)
            i = nl + 1 if nl != -1 else len(text)
            continue
        if text[i:i+2] == '/*':
            end = text.find('*/', i + 2)
            i = end + 2 if end != -1 else len(text)
            continue
        if ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
        i += 1
    return i - 1 if depth == 0 else len(text)


def extract_objects(text):
    """Извлекает JS-объекты { ... } из текста на нулевом уровне вложенности."""
    objects = []
    i = 0
    while i < len(text):
        brace_open = text.find('{', i)
        if brace_open == -1:
            break
        brace_close = find_matching(text, brace_open, '{', '}')
        if brace_close < len(text):
            objects.append(text[brace_open:brace_close + 1])
            i = brace_close + 1
        else:
            i = brace_open + 1
    return objects


def extract_chart_defs(html):
    """Извлекает список графиков из CHART_DEFS."""
    match = re.search(r'const\s+CHART_DEFS\s*=\s*\[', html)
    if not match:
        print('CHART_DEFS не найден')
        return []
    start = match.end()
    end = find_matching(html, start - 1, '[', ']')
    array_content = html[start:end]

    objects = extract_objects(array_content)
    charts = []
    for obj in objects:
        id_m = re.search(r"id:\s*'([^']+)'", obj)
        title_m = re.search(r"title:\s*'([^']+)'", obj)
        desc_m = re.search(r"desc:\s*'([^']+)'", obj)
        if id_m and title_m:
            charts.append({
                'id': id_m.group(1),
                'title': title_m.group(1),
                'desc': desc_m.group(1) if desc_m else '',
            })
    return charts


def extract_sections(html):
    """Извлекает секции из buildUI() (ищем unique firstId)."""
    idx = html.find("firstId: 'ch-demand-deficit'")
    if idx == -1:
        return []
    # Идём назад до открывающей скобки массива
    arr_start = html.rfind('[', 0, idx)
    if arr_start == -1:
        return []
    arr_end = find_matching(html, arr_start, '[', ']')
    array_content = html[arr_start + 1:arr_end]
    sections = []
    objs = extract_objects(array_content)
    for obj in objs:
        first_id_m = re.search(r"firstId:\s*'([^']+)'", obj)
        title_m = re.search(r"title:\s*'([^']+)'", obj)
        desc_m = re.search(r"desc:\s*'([^']+)'", obj)
        if first_id_m and title_m:
            sections.append({
                'first_id': first_id_m.group(1),
                'title': title_m.group(1),
                'desc': desc_m.group(1) if desc_m else '',
            })
    return sections


def chart_id_to_render_func(chart_id):
    """Преобразует ch-revenue-cat → renderRevenueByCategory."""
    overrides = {
        'ch-revenue-cat': 'renderRevenueByCategory',
        'ch-super-compare': 'renderSuperCompare',
        'ch-oos-hist': 'renderDaysOosHist',
        'ch-card-efficiency': 'renderCardEfficiencyIndex',
        'ch-rev-per-visit-top': 'renderRevenuePerVisitTop',
    }
    if chart_id in overrides:
        return overrides[chart_id]
    parts = chart_id[3:].split('-')
    return 'render' + ''.join(p.capitalize() for p in parts)


def generate_chart_markdown(charts, sections):
    """Генерирует markdown со списком графиков по секциям."""
    lines = ['## Список графиков', '']

    # Строим маппинг first_id → секция
    section_map = {}
    for i, s in enumerate(sections):
        end_id = sections[i + 1]['first_id'] if i + 1 < len(sections) else None
        section_map[s['first_id']] = {
            'title': s['title'], 'desc': s['desc'], 'end_id': end_id
        }

    printed = set()
    in_table = False
    chart_num = 0

    for c in charts:
        if c['id'] in printed:
            continue
        printed.add(c['id'])
        chart_num += 1

        # Заголовок новой секции
        if c['id'] in section_map:
            if in_table:
                lines.append('')
            sec = section_map[c['id']]
            lines.append(f'### {sec["title"]}')
            lines.append(f'> {sec["desc"]}')
            lines.append('')
            lines.append('| # | ID | Рендер | График |')
            lines.append('|---|---|---|---|')
            in_table = True

        func = chart_id_to_render_func(c['id'])
        desc = c['desc'][:90] + '…' if len(c['desc']) > 90 else c['desc']
        lines.append(f'| {chart_num} | `{c["id"]}` | `{func}()` | {c["title"]} |')

    lines.append('')
    lines.append(f'_Всего графиков: {chart_num}_')
    return '\n'.join(lines)


def update_md(md_path, chart_list):
    """Вставляет сгенерированный список между маркерами в md-файл."""
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    start_marker = '<!-- CHART_LIST_START -->'
    end_marker = '<!-- CHART_LIST_END -->'

    s = content.find(start_marker)
    e = content.find(end_marker)
    if s == -1 or e == -1:
        print(f'Маркеры не найдены в {md_path}')
        return False

    s += len(start_marker)
    new = content[:s] + '\n\n' + chart_list + '\n\n' + content[e:]
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(new)
    return True


def main():
    with open(HTML_PATH, 'r', encoding='utf-8') as f:
        html = f.read()

    charts = extract_chart_defs(html)
    sections = extract_sections(html)

    if not charts:
        print('Ошибка: не удалось извлечь графики из CHART_DEFS')
        return

    chart_list = generate_chart_markdown(charts, sections)
    if update_md(MD_PATH, chart_list):
        print(f'OK: {MD_PATH} — {len(charts)} графиков, {len(sections)} секций')
    else:
        print('Ошибка при обновлении файла')


if __name__ == '__main__':
    main()
