# Instructions: Reading & Summarizing Research Papers

This repo collects research papers related to Ads Tech. Every paper added to
this repo follows the process below so summaries stay consistent and easy to
scan.

## Process

1. **Read the paper** in full before writing anything.
2. **Summarize it** using the structure in [Summary Format](#summary-format)
   below. Keep the writing concise — this is a summary, not a rewrite of the
   paper.
3. **Create one Markdown file per paper** in the [`papers/`](papers/)
   directory. Use [`papers/TEMPLATE.md`](papers/TEMPLATE.md) as the starting
   point.
4. **Name the file** using a short slug of the paper title, e.g.
   `papers/deep-interest-network.md`.
5. **Cite the source** at the end of the file (see [Citing the
   Source](#citing-the-source)).

## Summary Format

Each paper's Markdown file must follow this section order:

1. **Title** — H1 heading with the paper's title.
2. **TL;DR** — A short (2-4 sentence) summary at the very top of the file.
   A reader should understand what the paper is about and why it matters
   without reading further.
3. **Main Contributions** — Bullet points of what the paper introduces or
   proves that is new.
4. **Main Benefits** — Bullet points of the practical value or advantages
   (performance gains, cost savings, simplification, etc.).
5. **How to Set Up** — Steps needed to reproduce, apply, or try out the
   paper's method (dependencies, datasets, code repo links, configuration).
   If the paper has no accompanying code or setup, state that explicitly.
6. **Details** — The longer-form write-up: problem statement, method,
   architecture, experiments, results, and limitations. This is where depth
   belongs; the sections above should stay concise.
7. **Source** — Citation for the paper (see below).

## Citing the Source

End every paper file with a `## Source` section containing:

- Full citation: authors, title, venue/conference or journal, year.
- A link to the paper (e.g. arXiv, ACM DL, publisher page).

Example:

```markdown
## Source

Zhou, G., et al. (2018). *Deep Interest Network for Click-Through Rate
Prediction*. KDD 2018. https://arxiv.org/abs/1706.06978
```

## Template

Use [`papers/TEMPLATE.md`](papers/TEMPLATE.md) as the starting point for
every new paper summary — copy it, rename it, and fill in each section.
