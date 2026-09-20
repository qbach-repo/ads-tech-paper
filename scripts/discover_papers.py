#!/usr/bin/env python3
"""Search arXiv for new ML papers related to ads ranking / ads technology.

Runs from the discover-papers GitHub Actions workflow, which has real
outbound internet access (this repo's Claude Code sessions may not).
Writes newly-found candidates to discovery/candidates.json and records
their arXiv IDs in discovery/seen_ids.json so future runs do not
re-surface the same paper.
"""
import json
import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

ATOM_NS = "{http://www.w3.org/2005/Atom}"
ARXIV_NS = "{http://arxiv.org/schemas/atom}"

SEEN_PATH = "discovery/seen_ids.json"
CANDIDATES_PATH = "discovery/candidates.json"

LOOKBACK_DAYS = int(os.environ.get("LOOKBACK_DAYS", "10"))
MAX_RESULTS = int(os.environ.get("MAX_RESULTS", "50"))

# arXiv categories most likely to contain ads-ranking / ads-tech ML papers.
CATEGORIES = ["cs.IR", "cs.LG", "cs.AI", "stat.ML"]

# Keyword/phrase search terms, matched against title + abstract.
# Edit this list to widen or narrow discovery.
KEYWORDS = [
    "ads ranking",
    "ad ranking",
    "ads recommendation",
    "click-through rate",
    "click through rate",
    "CTR prediction",
    "conversion rate prediction",
    "CVR prediction",
    "cost-per-click",
    "cost per click",
    "CPC",
    "cost-per-action",
    "cost per action",
    "CPA",
    "computational advertising",
    "online advertising",
    "sponsored search",
    "real-time bidding",
    "ad auction",
    "pCTR",
    "pCVR",
    "pClick",
    "pBook",
    "recommender ranking",
    "recommendation ranking",
]


def build_query() -> str:
    cat_clause = " OR ".join(f"cat:{c}" for c in CATEGORIES)
    kw_clause = " OR ".join(f'abs:"{k}"' for k in KEYWORDS)
    return f"({cat_clause}) AND ({kw_clause})"


def fetch_arxiv(query: str, max_results: int) -> bytes:
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url,
        headers={
            # arXiv's front end returns 406 Not Acceptable to requests that
            # don't send a real Accept header (default urllib sends none).
            "Accept": "application/atom+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": "ads-tech-paper-discovery/1.0 (github.com/qbach-repo/ads-tech-paper)",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def parse_entries(xml_bytes: bytes) -> list[dict]:
    root = ET.fromstring(xml_bytes)
    entries = []
    for entry in root.findall(f"{ATOM_NS}entry"):
        raw_id = entry.findtext(f"{ATOM_NS}id", default="").strip()
        match = re.search(r"abs/([^v]+)v?(\d*)", raw_id)
        arxiv_id = match.group(1) if match else raw_id
        title = " ".join(entry.findtext(f"{ATOM_NS}title", default="").split())
        summary = " ".join(entry.findtext(f"{ATOM_NS}summary", default="").split())
        published = entry.findtext(f"{ATOM_NS}published", default="")
        authors = [
            a.findtext(f"{ATOM_NS}name")
            for a in entry.findall(f"{ATOM_NS}author")
            if a.findtext(f"{ATOM_NS}name")
        ]
        primary_cat_el = entry.find(f"{ARXIV_NS}primary_category")
        primary_category = (
            primary_cat_el.get("term") if primary_cat_el is not None else ""
        )
        entries.append(
            {
                "id": arxiv_id,
                "title": title,
                "summary": summary,
                "published": published,
                "authors": authors,
                "link": f"https://arxiv.org/abs/{arxiv_id}",
                "html_link": f"https://arxiv.org/html/{arxiv_id}",
                "primary_category": primary_category,
            }
        )
    return entries


def load_seen() -> dict:
    if not os.path.exists(SEEN_PATH):
        return {"seen": []}
    with open(SEEN_PATH) as f:
        return json.load(f)


def save_seen(data: dict) -> None:
    os.makedirs(os.path.dirname(SEEN_PATH), exist_ok=True)
    with open(SEEN_PATH, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def within_lookback(published_str: str, days: int) -> bool:
    try:
        published = datetime.strptime(
            published_str, "%Y-%m-%dT%H:%M:%SZ"
        ).replace(tzinfo=timezone.utc)
    except ValueError:
        return True
    return published >= datetime.now(timezone.utc) - timedelta(days=days)


def matched_keywords(entry: dict) -> list[str]:
    text = f"{entry['title']} {entry['summary']}".lower()
    return [k for k in KEYWORDS if k.lower() in text]


def main() -> None:
    query = build_query()
    xml_bytes = fetch_arxiv(query, MAX_RESULTS)
    entries = parse_entries(xml_bytes)

    seen_data = load_seen()
    seen_ids = set(seen_data.get("seen", []))

    new_candidates = []
    for entry in entries:
        if entry["id"] in seen_ids:
            continue
        if not within_lookback(entry["published"], LOOKBACK_DAYS):
            continue
        entry["matched_keywords"] = matched_keywords(entry)
        new_candidates.append(entry)
        seen_ids.add(entry["id"])

    os.makedirs("discovery", exist_ok=True)
    with open(CANDIDATES_PATH, "w") as f:
        json.dump(new_candidates, f, indent=2)

    seen_data["seen"] = sorted(seen_ids)
    save_seen(seen_data)

    print(f"Found {len(new_candidates)} new candidate(s) out of {len(entries)} results.")


if __name__ == "__main__":
    main()
