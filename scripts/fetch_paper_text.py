#!/usr/bin/env python3
"""Fetch the full HTML text of one or more arXiv papers and print it.

Runs from the fetch-paper-text GitHub Actions workflow (real outbound
internet access; this repo's Claude Code sessions may not have it).
Deliberately prints to stdout instead of committing anything to the
repo: the extracted text is meant to be read once, from the workflow
run's log, by whoever (or whichever Claude Code session) is about to
write a paper summary -- not stored long-term in git.
"""
import sys
import time
from html.parser import HTMLParser

import requests

BEGIN_MARKER = "===== BEGIN PAPER {id} ====="
END_MARKER = "===== END PAPER {id} ====="

BLOCK_TAGS = {
    "p", "div", "section", "article", "li", "tr", "table",
    "h1", "h2", "h3", "h4", "h5", "h6", "br", "figure", "figcaption",
}
SKIP_TAGS = {"script", "style", "nav", "header", "footer"}


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._chunks = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in SKIP_TAGS:
            self._skip_depth += 1
        elif tag in BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_endtag(self, tag):
        if tag in SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1
        elif tag in BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_data(self, data):
        if self._skip_depth == 0:
            self._chunks.append(data)

    def text(self) -> str:
        raw = "".join(self._chunks)
        lines = [" ".join(line.split()) for line in raw.splitlines()]
        lines = [line for line in lines if line]
        return "\n".join(lines)


def fetch_html(arxiv_id: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 "
            "ads-tech-paper-discovery/1.0 (github.com/qbach-repo/ads-tech-paper)"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    resp = requests.get(
        f"https://arxiv.org/html/{arxiv_id}", headers=headers, timeout=30
    )
    resp.raise_for_status()
    return resp.text


def main() -> None:
    ids = sys.argv[1:]
    if not ids:
        print("Usage: fetch_paper_text.py <arxiv_id> [arxiv_id ...]", file=sys.stderr)
        sys.exit(1)

    for i, arxiv_id in enumerate(ids):
        if i > 0:
            time.sleep(3)  # be polite to arxiv.org between requests
        print(BEGIN_MARKER.format(id=arxiv_id))
        try:
            html = fetch_html(arxiv_id)
        except requests.HTTPError as e:
            print(f"[fetch failed: {e}]")
            print(END_MARKER.format(id=arxiv_id))
            continue
        extractor = TextExtractor()
        extractor.feed(html)
        print(extractor.text())
        print(END_MARKER.format(id=arxiv_id))


if __name__ == "__main__":
    main()
