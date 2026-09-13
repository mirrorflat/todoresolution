from src.task_parser import parse_onenote_print_tasks, parse_top_level_tasks

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


ONENOTE_PRINT_SAMPLE = """今日の予定
amazonmasterカートETC
タスク・1/4・日今日
マイナンバ-カードの更新
タスク・日今日
指輪2の計画をたてる
タスク・日今日
2026年9月13日
〇〇〇〇〇〇〇〇〇〇〇〇〇〇〇》
保険の見直し
子どもに金融教育をする。
タスク・日今日
ゴミのサイクル設計
タスク・日今日
株式プログラムファンタメンタル情報ダッシュボードのデザインと実装
タスク・日今日
犬をどうするか決める
芝生どうするか決める
タスク・日今日
家計簿ロ-カル、構築
タスク・日今日
[MS活用]Microsoftの活用計画
タスク・日今日
英会話とにかく喋る。
鏡平式練習
日次タスク・日今日0
運動工クササイズ
日次タスク・日今日0
タスク・日今日
タスク・日今日
日次タスク・日今日0
オメガ修理
タスク・日今日
MicrosoftToDoで印刷
1/2
今日の予定
週次タスク.日今日
週次タスク.日今日0
昼飯
夕飯
2026年9月13日
MicrosoftToDoで印刷
2/2
"""


def test_onenote_print_extracts_expected_task_titles():
    titles = parse_onenote_print_tasks(ONENOTE_PRINT_SAMPLE)
    assert titles == [
        "amazonmasterカートETC",
        "マイナンバ-カードの更新",
        "指輪2の計画をたてる",
        "保険の見直し",
        "子どもに金融教育をする。",
        "ゴミのサイクル設計",
        "株式プログラムファンタメンタル情報ダッシュボードのデザインと実装",
        "犬をどうするか決める",
        "芝生どうするか決める",
        "家計簿ロ-カル、構築",
        "[MS活用]Microsoftの活用計画",
        "英会話とにかく喋る。",
        "鏡平式練習",
        "運動工クササイズ",
        "オメガ修理",
        "昼飯",
        "夕飯",
    ]
    assert len(titles) == 17


def test_onenote_print_excludes_noise_line_variants():
    body = "\n".join(
        [
            "今日の予定",
            "タスク・日今日",
            "日次タスク・日今日0",
            "週次タスク.日今日",
            "タスク・1/4・日今日",
            "2026年9月13日",
            "〇〇〇》",
            "MicrosoftToDoで印刷",
            "1/2",
            "実際のタスク",
        ]
    )
    assert parse_onenote_print_tasks(body) == ["実際のタスク"]


def test_onenote_print_empty_body_returns_empty_list():
    assert parse_onenote_print_tasks("") == []
