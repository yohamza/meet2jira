import os
import requests
from requests.auth import HTTPBasicAuth

DEFAULT_API_VERSION = "3"

def _get_config():
    base_url = os.environ.get("JIRA_BASE_URL")
    email = os.environ.get("JIRA_EMAIL")
    api_token = os.environ.get("JIRA_API_TOKEN")
    api_version = os.environ.get("JIRA_API_VERSION", DEFAULT_API_VERSION)
    if not base_url or not email or not api_token:
        return None
    return {
        "base_url": base_url.rstrip("/"),
        "email": email,
        "api_token": api_token,
        "api_version": api_version
    }

def is_configured():
    return _get_config() is not None

def _to_adf(text):
    paragraphs = []
    for line in text.splitlines():
        if not line.strip():
            continue
        paragraphs.append({
            "type": "paragraph",
            "content": [{"type": "text", "text": line}]
        })
    if not paragraphs:
        paragraphs = [{
            "type": "paragraph",
            "content": [{"type": "text", "text": ""}]
        }]
    return {
        "type": "doc",
        "version": 1,
        "content": paragraphs
    }

def add_comment(issue_key, comment_text):
    """
    Adds a comment to a Jira issue. Returns the response JSON.
    """
    cfg = _get_config()
    if not cfg:
        raise RuntimeError("Jira config missing. Set JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN.")

    url = f"{cfg['base_url']}/rest/api/{cfg['api_version']}/issue/{issue_key}/comment"
    if cfg["api_version"] == "2":
        payload = {"body": comment_text}
    else:
        payload = {"body": _to_adf(comment_text)}

    response = requests.post(
        url,
        auth=HTTPBasicAuth(cfg["email"], cfg["api_token"]),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        json=payload,
        timeout=30
    )
    response.raise_for_status()
    return response.json()

def post_ticket_notes(ticket_notes, meeting_title=None):
    """
    Posts a combined comment per ticket. Returns dict of issue_key -> status.
    """
    results = {}
    for ticket, notes in ticket_notes.items():
        if not notes:
            continue
        lines = []
        if meeting_title:
            lines.append(f"Meeting notes from: {meeting_title}")
        if len(notes) == 1:
            lines.append(notes[0])
        else:
            lines.append("Notes:")
            for note in notes:
                lines.append(f"- {note}")
        comment_text = "\n".join(lines)
        add_comment(ticket, comment_text)
        results[ticket] = "posted"
    return results
