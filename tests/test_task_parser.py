from src.task_parser import parse_top_level_tasks

SAMPLE_BODY = """今日の予定

⬜ タスクA - 期限 今日
⬜ タスクB - 期限 今日
        ⬜ サブタスクB-1
        ⬜ サブタスクB-2
⬜ タスクC: 説明 - 補足 - 期限 今日
        ⬜ サブタスクC-1
        ✅ サブタスクC-2(完了済み)
        Notes: メッセージへのリンク<https://example.com>
⬜ タスクD - 期限 今日
・箇条書きのメモ(タスクではない)
"""


def test_extracts_only_top_level_tasks():
    titles = parse_top_level_tasks(SAMPLE_BODY)
    assert titles == ["タスクA", "タスクB", "タスクC: 説明 - 補足", "タスクD"]


def test_excludes_completed_and_indented_lines():
    titles = parse_top_level_tasks(SAMPLE_BODY)
    assert not any("サブタスク" in t for t in titles)
    assert not any(t.startswith("✅") for t in titles)


def test_line_without_due_suffix_still_captured():
    body = "⬜ 期日なしタスク\n"
    assert parse_top_level_tasks(body) == ["期日なしタスク"]


def test_empty_body_returns_empty_list():
    assert parse_top_level_tasks("") == []
