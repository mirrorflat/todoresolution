import re

TOP_LEVEL_MARK = "⬜"
_INDENT_CHARS = " \t　"
_SUFFIX_RE = re.compile(r"^⬜\s*(.+?)\s*-\s*期限\s*\S+\s*$")


def parse_top_level_tasks(body: str) -> list[str]:
    titles = []
    for line in body.splitlines():
        if not line or line[0] in _INDENT_CHARS:
            continue
        stripped = line.strip()
        if not stripped.startswith(TOP_LEVEL_MARK):
            continue
        match = _SUFFIX_RE.match(stripped)
        if match:
            title = match.group(1)
        else:
            title = stripped[len(TOP_LEVEL_MARK):].strip()
        if title:
            titles.append(title)
    return titles


# --- OneNote「印刷イメージ」からのテキストコピー用パーサー ---
#
# OneNote の印刷プレビューを「全ページからテキストをコピー」すると、タスク名の行の
# 間に種別・ページ送り等のノイズ行が不規則に混ざった、1行1項目のプレーンテキストに
# なる。タスク名行とノイズ行を区別する明示的なマーカーが無いため、既知のノイズ
# パターンに一致しない行をすべてタスクとして扱う。

_ONENOTE_EXACT_NOISE_LINES = {"今日の予定", "MicrosoftToDoで印刷"}
_ONENOTE_NOISE_SUBSTRING = "日今日"  # 「タスク・日今日」「日次タスク・日今日0」等の種別行に共通
_ONENOTE_DATE_ONLY_RE = re.compile(r"^\d{4}年\d{1,2}月\d{1,2}日$")
_ONENOTE_PAGINATION_RE = re.compile(r"^\d+\s*/\s*\d+$")
# 用途不明の装飾/区切り行(〇の連続)。OneNote側の印刷レイアウト由来と推測されるが未確定。
_ONENOTE_DECORATIVE_RE = re.compile(r"^[〇○]{2,}[》』】)]?$")


def parse_onenote_print_tasks(text: str) -> list[str]:
    titles = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped in _ONENOTE_EXACT_NOISE_LINES:
            continue
        if _ONENOTE_NOISE_SUBSTRING in stripped:
            continue
        if _ONENOTE_DATE_ONLY_RE.match(stripped):
            continue
        if _ONENOTE_PAGINATION_RE.match(stripped):
            continue
        if _ONENOTE_DECORATIVE_RE.match(stripped):
            continue
        titles.append(stripped)
    return titles
