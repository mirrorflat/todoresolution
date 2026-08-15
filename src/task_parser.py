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
