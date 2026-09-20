# Generative Query Suggestion via Intent Coverage and Query-Level Credit Assignment

## TL;DR

A production system for generative query suggestion in a conversational
assistant: given the current dialogue, generate a slate of follow-up
queries (e.g. 3 suggestions) that are each individually useful *and*
collectively cover distinct user intents, rather than three near-duplicate
guesses. The paper's Intent-Driven Query Suggestion Framework combines (1)
intent-aware SFT data construction plus a diversity reward that explicitly
targets intent coverage, and (2) an RL stage that assigns credit at the
*query* level (each suggestion in the slate gets its own quality signal)
while still sharing a slate-level diversity signal across the whole slate.
Online A/B testing and offline evaluation on production data show gains in
click-through rate, human-judged query quality, and intent coverage over
both a prompt-engineering baseline and a naive supervised fine-tuned model.

## Main Contributions

- An **intent-aware diversity reward (IAD-R)** used both to construct
  intent-aligned SFT data and as an RL reward term, explicitly optimizing
  for a slate that spans distinct user intents rather than just generating
  plausible individual queries.
- A **query-level credit assignment** mechanism for RL over slates: instead
  of a single sequence-level reward for an entire generated slate, each
  query in the slate gets its own quality-based advantage (a mix of a
  rubric-based reward and a CTR-based reward), which is then broadcast to
  that query's own tokens — while diversity is still scored and normalized
  at the slate level and combined with the per-query signal.
- A **three-stage SFT data pipeline** (LLM-only prompting → LLM-generated
  candidates → human-AI collaborative refinement → mixed chain-of-thought
  and direct-query hybrid data) shown to improve both human-judged quality
  and intent coverage at each stage, used as the RL cold-start model.
- A production-scale evaluation combining **online A/B testing** (live
  click-through rate) with **offline human and LLM-judge evaluation**
  (a rubric-based "LLM Critic" score, lexical diversity via Self-BLEU, and
  human-annotated intent coverage), plus a scalability check showing the
  gains largely transfer to a much larger backbone model (Qwen3-235B-A22B).

## Main Benefits

- Measurable production gains: improvements in click-through rate, human
  preference (GSB-style comparison against the baseline), LLM-judged query
  quality, and annotated intent coverage, validated with a live one-week
  online A/B test in addition to offline metrics.
- Ablations isolate *why* it works: removing the diversity reward causes
  the single largest drop in intent coverage (0.91 → 0.71); removing the
  rubric-based quality reward causes the largest drop in LLM-judged quality
  (0.88 → 0.62); query-level credit assignment consistently beats a
  sequence-level RL baseline throughout training, not just at convergence.
- The gains are not backbone-specific: applying the same SFT+RL recipe to
  a much larger model (Qwen3-235B-A22B) retains a majority of the relative
  improvement in both LLM Critic score (+61%) and intent coverage (+62%)
  over that model's own prompt-engineering baseline.
- The reward design (rubric + CTR, mixed with fixed, untuned weights) and
  the discount factor for query-level advantage were deliberately *not*
  tuned on the test set (γ = 0.95 chosen because the production UI shows
  exactly 3 suggestions), reducing the risk of overfitting the evaluation.

## How to Set Up

This is an industrial system built on **proprietary production dialogue
logs** and a live serving environment; **no code or dataset is released**,
and the authors state this explicitly as a reproducibility limitation. What
the paper does specify, for anyone reimplementing the approach:

- **Base models**: the main experiments use a production-scale LLM as the
  policy; a scalability check is run against Qwen3-235B-A22B (with a
  smaller Qwen3-30B-A3B mentioned as an earlier-scale baseline point).
- **Training infrastructure**: a cluster of 256 NVIDIA H100 GPUs; SFT uses
  AdamW with a linear schedule (lr 1e-5, batch size 128); RL uses AdamW
  (lr 2e-6, batch size 64, KL coefficient 0.05, 8 rollouts per prompt,
  clip range [0.2, 0.28], 2 epochs).
- **Reward mixture**: rubric weight α = 0.6, CTR weight β = 0.4, query-level
  discount γ = 0.95, fixed slate size K = 3 — all fixed rather than tuned
  on held-out data.
- **Evaluation rubric**: a four-dimension human evaluation standard (Content
  Quality, Requirement Satisfaction, Text Quality, Information Gain), each
  with specific pass/fail criteria (e.g. character-count limits, timeliness,
  over-assumption about the user, logical consistency with prior turns),
  plus an annotation pipeline requiring >90% annotator agreement against
  gold-standard samples before production labeling.

## Details

### Problem framing

Conversational query suggestion recommends 2–5 short follow-up queries
after each assistant turn. The paper frames the core difficulty as a
tension between two objectives that are easy to satisfy individually but
hard to satisfy jointly: making each suggested query individually useful,
and making the *slate* as a whole cover different, non-redundant user
intents (rather than three phrasings of the same idea).

### Method

**Stage 1 — Intent-aware diversity modeling.** SFT data is built in three
progressive stages: (i) `SFT-Candidate` trains on LLM-generated candidate
queries; (ii) `SFT-Refined` adds human-AI collaborative refinement on top;
(iii) `SFT-Hybrid` mixes chain-of-thought intent-reasoning traces with
direct queries. Each stage measurably improves over the last (`SFT-Refined`
improves a GSB-style human-preference score by 0.08 and intent coverage by
0.14 over `SFT-Candidate`; `SFT-Hybrid` adds a further 0.12 to intent
coverage), and `SFT-Hybrid` is adopted as the RL cold-start model. An
Intent-Aware Diversity Reward (IAD-R) is used both to select/construct this
data and later as an RL reward term.

**Stage 2 — Query-level credit assignment (RL).** For each prompt, the
policy samples several candidate slates of K queries. Each query in a slate
gets its own reward, a weighted mix of a rubric-based quality reward and a
CTR-based engagement reward; these per-query rewards are normalized and
turned into a discounted, query-level advantage (later queries in the slate
are discounted by γ, reflecting production ranking). Separately, a
slate-level diversity reward is computed and normalized across the group of
sampled slates. The two advantage signals are combined (query-level and
diversity, roughly averaged with an √2 normalization) when the slate passes
basic validity constraints, and a fixed penalty applied on failure; the
combined advantage for a query is then broadcast uniformly to every token
of that query before a PPO-style clipped policy-gradient update with a KL
penalty against a reference policy. The key structural idea is that
diversity is a *slate*-level property (it has to be scored relative to the
other queries in the same slate) while quality is a *query*-level property,
and the credit-assignment scheme keeps both granularities intact rather
than collapsing everything into one sequence-level reward.

### Experiments and results

Evaluation combines: (a) a live one-week online A/B test measuring
click-through rate; (b) offline human evaluation against the four-dimension
rubric described above, aggregated into a GSB-style relative comparison;
(c) an "LLM Critic" score (a rubric-based LLM-as-judge metric) and
Self-BLEU (lower = more lexically diverse slate) as automatic proxies.

**Ablations on the RL stage** (relative to the full method): removing the
diversity reward causes the largest single drop in intent coverage (0.91 →
0.71), and training curves show the full method converges faster and to a
higher plateau on this metric. Removing the rubric-based quality reward
drops the LLM Critic score from 0.88 to 0.62; removing the CTR reward drops
the GSB-style score by 0.11. Query-level credit assignment beats a
sequence-level-reward RL baseline throughout training (e.g. an LLM Critic
score of ~0.86 vs. ~0.75 at an early checkpoint, converging to 0.88 vs.
0.83), not just asymptotically.

**Scalability.** Re-running the same SFT+RL recipe on Qwen3-235B-A22B
(evaluated offline due to deployment constraints) shows the prompt-only
baseline already starts stronger on this larger model, but the full
method still recovers 61% of the relative LLM Critic gain and 62% of the
relative intent-coverage gain seen at the original model scale, with
Self-BLEU also improving — indicating the recipe is not purely an artifact
of one backbone size.

**Sensitivity.** A targeted sweep over the query-level discount factor γ
(0.90, 0.95, 0.99, 1.00) shows both the LLM Critic score and Self-BLEU stay
within a narrow band, supporting the choice of a fixed, untuned γ = 0.95.

### Limitations (as stated by the authors)

- Training/evaluation data comes from proprietary production logs, which
  the authors say limits direct reproducibility; they plan to release a
  sanitized evaluation subset "when compliance permits."
- Online CTR is treated as an engagement proxy, not a direct measure of
  user satisfaction; the online result is a single one-week experiment
  without reported confidence intervals or repeated-window variance.
- Intent Coverage and the LLM Critic metric share a rubric family with the
  training reward, and the same judge model participates in both training
  and evaluation — so these are not fully independent evidence, which is
  why the paper foregrounds online CTR and human GSB as the primary
  evidence.
- Human evaluation uses majority voting without a reported chance-corrected
  inter-annotator agreement statistic.
- A full sweep over the quality/diversity reward weights and repeated
  full-scale RL runs were judged computationally prohibitive; only a
  targeted discount-factor sensitivity study was run.
- The paper does not measure whether broader intent coverage improves
  multi-turn engagement across distinct follow-up intents, and diversity
  remains a slate-level property even with query-level credit assignment
  (precise marginal per-query contribution to diversity is left as future
  work).

## Source

Liu, X., Ma, L., Qiao, J., Zhou, M., Li, L., Bian, X., Chen, H., Jiang, X.,
et al. (2026). *Generative Query Suggestion via Intent Coverage and
Query-Level Credit Assignment*. arXiv:2609.19209 [cs.LG].
https://arxiv.org/abs/2609.19209
