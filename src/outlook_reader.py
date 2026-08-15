TARGET_SUBJECT = "Microsoft To Do - 今日の予定"
OL_FOLDER_INBOX = 6


class MailNotFoundError(Exception):
    pass


def fetch_today_digest_body(subject: str = TARGET_SUBJECT) -> str:
    import win32com.client

    outlook = win32com.client.Dispatch("Outlook.Application")
    namespace = outlook.GetNamespace("MAPI")
    inbox = namespace.GetDefaultFolder(OL_FOLDER_INBOX)

    items = inbox.Items
    items.Sort("[ReceivedTime]", True)
    subject_escaped = subject.replace("'", "''")
    matches = items.Restrict(f"[Subject] = '{subject_escaped}'")

    if matches.Count == 0:
        raise MailNotFoundError(f"件名「{subject}」のメールが受信トレイに見つかりません。")

    return matches.Item(1).Body
