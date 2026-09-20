# Paper discovery pipeline

This directory backs the automated paper-discovery workflow
(`.github/workflows/discover-papers.yml`). It finds new ML research
related to ads ranking / ads technology and files each candidate as a
GitHub issue for you to triage — it never writes a summary itself.

## How it works

1. **Weekly, every Monday at 13:00 UTC** (or on demand via the
   "Discover ads-tech papers" workflow's *Run workflow* button),
   `scripts/discover_papers.py` queries the
   [arXiv API](https://info.arxiv.org/help/api/index.html) for papers in
   `cs.IR`, `cs.LG`, `cs.AI`, or `stat.ML` whose title/abstract match one
   of a curated list of ads-ranking / ads-tech keywords (CTR, CVR, CPC,
   CPA, pCTR, pCVR, pClick, pBook, sponsored search, real-time bidding,
   computational advertising, etc. — see `KEYWORDS` in the script).
2. Papers whose arXiv ID is already in `discovery/seen_ids.json` are
   skipped. New ones are written to a transient `discovery/candidates.json`
   and added to `seen_ids.json` so they're never surfaced twice.
3. `scripts/create_candidate_issues.py` opens one GitHub issue per new
   candidate, labeled `paper-candidate`, with the title, authors,
   abstract, matched keywords, and links to the paper.
4. The workflow commits the updated `discovery/seen_ids.json` back to
   `main` so state persists across runs.

## The human gate

**Discovery never triggers a summary.** Each `paper-candidate` issue is a
triage item:

- **Worth summarizing?** Keep the issue open. Whenever you're ready,
  trigger a Claude Code session (ad hoc — no automatic trigger is wired
  up) and point it at the issue or the arXiv link; it will follow
  `INSTRUCTIONS.md` to write `papers/<slug>.md`.
- **Not relevant?** Close the issue.

## Tuning discovery

- **Keywords / categories** — edit `KEYWORDS` / `CATEGORIES` at the top
  of `scripts/discover_papers.py`.
- **Schedule** — edit the `cron` line in
  `.github/workflows/discover-papers.yml` (currently weekly, Mondays
  13:00 UTC).
- **Lookback window** — the workflow only considers papers submitted in
  the last `LOOKBACK_DAYS` (default 10, overridable as a
  `workflow_dispatch` input) to give some overlap between runs without
  re-surfacing already-seen papers.

## Notes

- arXiv keyword search is a blunt instrument — expect some false
  positives (and the occasional miss); that's why triage is manual.
- If a scheduled workflow goes 60 days without the repository receiving
  any activity, GitHub auto-disables it. Any commit (e.g. a new paper
  summary) resets that clock; if it ever does trip, re-enable it from the
  repo's Actions tab.
