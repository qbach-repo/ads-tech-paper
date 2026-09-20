# ANGLE: One-Step Retrieval Framework for Real-Time Sponsored Search Ads Using Hierarchical Text Representations

## TL;DR

A generative ad-retrieval system for real-time sponsored search that
replaces two separate weaknesses in current approaches: traditional
multi-stage cascades (where each stage is optimized independently and can
prematurely drop good candidates) and recent LLM-based generative retrieval
methods (which retrieve ads via discrete semantic IDs the LLM never
actually "understands," requiring brittle memorization and struggling to
generalize to new ads). ANGLE instead has an LLM generate hierarchical
*textual* representations of each ad — a high-level "commercial intent"
and a fine-grained "ad abstract" — and performs retrieval, relevance
scoring, and ranking inside a single LLM. In production it delivered a
1.81% increase in consumption and a 2.16% increase in GMV, and beat seven
offline baselines on retrieval-quality metrics.

## Main Contributions

- Identifies a concrete failure mode of prior LLM-based generative ad
  retrieval: discrete semantic identifiers (SIDs) are not part of the base
  LLM's learned vocabulary, so the model must memorize large numbers of
  SID-to-ad mappings during fine-tuning, which generalizes poorly to unseen
  ads, is costly to keep updated, and produces an inefficient one-to-one
  decoding process.
- Proposes generating **hierarchical textual representations** for ads
  instead of opaque IDs — a coarse "commercial intent" summary plus a
  finer-grained "ad abstract" — so retrieval operates over text the LLM
  natively understands rather than an artificial ID space.
- Unifies **retrieval, relevance, and ranking in a single LLM** (the ANGLE
  framework: "unified generation-discriminative-ranking real-time
  retrieval"), rather than retrieving candidates with one model and scoring
  commercial value with a separate small reward model (e.g. a pCTR model),
  which the paper argues limits how well the system can assess an ad's full
  commercial value.
- Validates the approach with both a live production deployment and a
  seven-baseline offline comparison, rather than offline metrics alone.

## Main Benefits

- **Production impact**: a 1.81% increase in consumption and a 2.16%
  increase in gross merchandise volume (GMV) when deployed to real-world
  sponsored search traffic.
- **Offline superiority**: outperforms all seven compared baselines on
  hit-rate (HR) and average-click-rate-style (ACR) retrieval-quality
  metrics.
- Addresses the generalization and maintenance cost of ID-based generative
  retrieval directly, which matters for ad inventory that changes
  continuously (new ads have no learned SID, but do have text a language
  model can reason about).
- Folds relevance and ranking into the same model that performs retrieval,
  removing the objective mismatch between an independently-optimized
  cascade of retrieval → relevance → ranking stages.

## How to Set Up

This is an industrial system built for a specific sponsored-search
platform's real-time serving stack; **no code, model weights, or public
dataset are released.** The abstract does not specify the base LLM,
training data, or infrastructure used, so there isn't enough public detail
to reproduce ANGLE end-to-end. What can be taken from the paper as a
design pattern rather than a runnable recipe:

- Generate a **two-level textual representation** per ad (a short
  commercial-intent summary and a longer, fine-grained ad abstract) instead
  of a discrete semantic ID, so retrieval matching happens in natural
  language space.
- Route **retrieval, relevance scoring, and ranking through one LLM**
  rather than a small downstream reward/ranking model, if the serving
  latency budget allows it.
- Benchmark against a **multi-stage cascading architecture** and against
  ID-based generative retrieval baselines on both offline hit-rate/ranking
  metrics and a live A/B test, as this paper does.

## Details

This paper is a short industrial systems paper; the available abstract
covers the motivation, architecture at a high level, and headline results,
but not full training/serving implementation details. Within that scope:

**Motivation.** Two families of existing approaches are critiqued. Multi-
stage cascading architectures (MCA) optimize each stage (retrieval,
relevance, ranking) independently, which creates inconsistent objectives
across stages and can eliminate high-potential ad candidates before they
ever reach the ranking stage. Recent LLM-based *generative* retrieval
methods solve the end-to-end objective-consistency problem but introduce a
new one: they represent ads as discrete semantic identifiers (SIDs) that
the base LLM was never pretrained to understand, so the model has to
memorize a large number of SID-to-ad mappings during supervised
fine-tuning. This hurts generalization to ads that weren't in that mapping
table, is expensive to keep current as inventory changes, and — because
the SID-to-ad mapping is one-to-one — makes decoding inefficient. These
methods also typically hand off commercial-value scoring to a small,
separate reward model (e.g. a pCTR predictor), which the authors argue
caps how well the overall system can judge an ad's commercial value.

**Method.** ANGLE (A uNified Generation-discriminative-ranking reaL-time
rEtrieval) replaces the SID representation with LLM-generated hierarchical
*text*: a high-level commercial-intent overview and a fine-grained ad
abstract, both consumed as natural language rather than opaque tokens.
Retrieval, relevance judgment, and ranking are then performed within a
single LLM, rather than being split across a retrieval model plus a
separate small ranking/reward model — the stated goal being to let the
full capability of the LLM inform commercial-value assessment rather than
bottlenecking it through a small auxiliary model.

**Results.** In real-world search deployment, ANGLE produced a 1.81%
increase in consumption and a 2.16% increase in GMV. In offline evaluation
against seven baseline systems, ANGLE outperformed all of them on hit-rate
(HR) and ACR-style ranking-quality metrics.

**What isn't in the abstract**: specific architecture details for how the
hierarchical text representations are generated and indexed, the training
objective(s) used to jointly learn retrieval/relevance/ranking, the base
LLM and its scale, latency figures for serving this at real-time sponsored-
search volumes, and the composition of the seven offline baselines beyond
"traditional MCA and ID-based generative retrieval" framings implied by the
motivation section.

## Source

Liu, T., Zhang, R., Ding, J., Guo, H., Yang, X., Wei, H., Li, Z., & Wu, H.
(2026). *ANGLE: One-Step Retrieval Framework for Real-Time Sponsored
Search Ads Using Hierarchical Text Representations*. arXiv:2609.18296
[cs.IR]. https://arxiv.org/abs/2609.18296
