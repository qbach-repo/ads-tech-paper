#!/usr/bin/env python3
"""Open one GitHub issue per newly-discovered candidate paper.

Reads discovery/candidates.json (written by discover_papers.py) and files
a "paper-candidate" issue per entry so a human can triage: keep it open
(and optionally label it "approved") to have someone trigger a Claude
Code session to write the summary, or close it to reject the candidate.
"""
import json
import os
import urllib.error
import urllib.request

CANDIDATES_PATH = "discovery/candidates.json"
LABEL_NAME = "paper-candidate"
LABEL_COLOR = "0e8a16"
LABEL_DESCRIPTION = (
    "New paper found by the weekly discovery workflow, awaiting triage"
)


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "ads-tech-paper-discovery",
        "Content-Type": "application/json",
    }


def ensure_label(repo: str, token: str) -> None:
    url = f"https://api.github.com/repos/{repo}/labels/{LABEL_NAME}"
    req = urllib.request.Request(url, headers=_headers(token))
    try:
        urllib.request.urlopen(req)
        return
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise

    payload = json.dumps(
        {
            "name": LABEL_NAME,
            "color": LABEL_COLOR,
            "description": LABEL_DESCRIPTION,
        }
    ).encode()
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/labels",
        data=payload,
        headers=_headers(token),
        method="POST",
    )
    urllib.request.urlopen(req)


def create_issue(repo: str, token: str, entry: dict) -> dict:
    title = f"[Candidate] {entry['title']}"

    authors = entry.get("authors", [])
    author_line = ", ".join(authors[:8])
    if len(authors) > 8:
        author_line += ", et al."

    keywords = ", ".join(entry.get("matched_keywords", [])) or "n/a"

    body = (
        f"**arXiv ID:** {entry['id']}\n"
        f"**Abstract page:** {entry['link']}\n"
        f"**HTML:** {entry['html_link']}\n"
        f"**Published:** {entry['published']}\n"
        f"**Primary category:** {entry['primary_category']}\n"
        f"**Authors:** {author_line}\n"
        f"**Matched keywords:** {keywords}\n\n"
        f"**Abstract:**\n{entry['summary']}\n\n"
        "---\n"
        "Surfaced automatically by the weekly paper-discovery workflow "
        "(`.github/workflows/discover-papers.yml`). This is a triage "
        "queue, not an approval:\n\n"
        "- Worth summarizing? Keep this issue open and, whenever you're "
        "ready, trigger a Claude Code session referencing this issue or "
        "the arXiv link above to write the summary per `INSTRUCTIONS.md`.\n"
        "- Not relevant? Close this issue.\n"
    )

    payload = json.dumps(
        {"title": title, "body": body, "labels": [LABEL_NAME]}
    ).encode()
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/issues",
        data=payload,
        headers=_headers(token),
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def main() -> None:
    repo = os.environ["GITHUB_REPOSITORY"]
    token = os.environ["GH_TOKEN"]

    if not os.path.exists(CANDIDATES_PATH):
        print("No candidates file found; nothing to do.")
        return

    with open(CANDIDATES_PATH) as f:
        candidates = json.load(f)

    if not candidates:
        print("No new candidates this run.")
        return

    ensure_label(repo, token)

    for entry in candidates:
        issue = create_issue(repo, token, entry)
        print(f"Created issue #{issue['number']}: {entry['title']}")


if __name__ == "__main__":
    main()
