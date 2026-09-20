# VARG: Value-Aware and Ranking-Aligned Generative Retrieval for Dynamic E-commerce Search

## TL;DR

A generative retrieval system deployed in Tmall App search that generates
candidate item identifiers directly and feeds them straight into the
existing final ranker — rather than retrieving from a fixed index — while
explicitly encoding business value (not just relevance) into the generated
identifiers and the training signal. Item identifiers are built from
RQ-VAE semantic prefixes plus a "value-ordered" third token that encodes a
business-value prior, and a reinforcement-learning stage (Prefix-GRPO)
aligns candidate generation with both ranker feedback and search
relevance. A 14-day online A/B test on 20% of search traffic showed GMV up
1.45%, per-user item page views up 0.22%, and predicted CTR up 0.31%,
while using a smaller candidate quota than the incumbent approach.

## Main Contributions

- **VARG-ID**: an item-identifier scheme built from RQ-VAE semantic
  prefixes (for coarse-to-fine item addressing) plus bidirectional
  query-item contrastive learning (for search relevance) plus a
  **value-ordered third token** that encodes both fine-grained item
  addressing and a business-value prior in the same identifier — so
  business value isn't bolted on after retrieval, it's part of the address
  space itself.
- A **three-stage supervised fine-tuning curriculum** that progressively
  teaches item-to-identifier mapping, then query-semantic retrieval, then
  personalized retrieval, rather than training all of these jointly from
  the start.
- **Local ordinal supervision (LO-SFT)**: a training signal that teaches
  the model the correct *local, within-cluster* ordering encoded by the
  value-ordered third token, combined with value-aware and
  hierarchy-aligned supervision and expanded user context for
  personalization.
- **Prefix-GRPO**: a group relative policy optimization variant that
  combines gated rewards (output legality, user behavior, ranker
  advantage, and search relevance) with prefix-aware token weighting, so
  reinforcement learning shapes candidate generation toward both business
  value and the ranking objective it will ultimately be judged on.
- A **coordinated daily update procedure** for products and the model that
  preserves existing item addresses while incorporating new products and
  fresh behavioral feedback — addressing the practical problem that a
  generative retrieval system's identifier space has to stay usable as
  inventory and behavior data shift day to day.

## Main Benefits

- **Directly admits generated candidates to the existing final ranker**,
  integrating recall and pre-ranking rather than treating generative
  retrieval as a separate parallel candidate source.
- **Production results** from a 14-day online A/B test covering 20% of
  search traffic: GMV +1.45%, per-user item-page views (IPV) +0.22%, and
  predicted CTR (PCTR) +0.31%.
- **Smaller candidate quota, competitive relevance**: online shopping-guide
  query evaluations show VARG maintains competitive relevance while
  requesting fewer candidates than the baseline needs, which matters for
  downstream ranking latency/cost.
- **Offline validation at scale**: experiments on tens of millions of
  products confirm identifier stability (addresses don't need to be
  reassigned wholesale as the catalog changes) and show retrieval-quality
  and head-level value-recall gains from both the SFT strategies and
  Prefix-GRPO over their respective baselines.

## How to Set Up

This is a production system built for **Tmall App search**, evaluated on a
proprietary catalog of tens of millions of products and a live 14-day
A/B test; **no code, model, or dataset is released.** There's no public
repository to reproduce. The paper's specified components can be used as
a blueprint for a similar generative-retrieval-into-ranker pipeline:

- **Identifier construction (VARG-ID)**: build semantic prefixes with
  RQ-VAE, add bidirectional query-item contrastive learning for relevance,
  and append a value-ordered token that jointly encodes fine-grained item
  address and a business-value prior.
- **Three-stage SFT curriculum**: (1) item-to-identifier mapping, (2)
  query-semantic retrieval, (3) personalized retrieval — trained
  progressively rather than jointly from scratch.
- **Personalization training**: combine value-aware and hierarchy-aligned
  supervision with expanded user context, plus local ordinal supervision
  (LO-SFT) for the within-cluster ordering encoded by the value token.
- **RL alignment (Prefix-GRPO)**: gate rewards on output legality, user
  behavior, ranker advantage, and search relevance, with prefix-aware
  token weighting.
- **Daily refresh procedure**: coordinate product-catalog updates and
  model updates so existing item addresses are preserved while new
  products and fresh behavioral feedback are incorporated.

## Details

This is a short industrial systems paper; the abstract lays out the
architecture, training curriculum, and evaluation results at a high level
without full hyperparameter or infrastructure detail. Within that scope:

**Problem framing.** Integrating recall and pre-ranking in e-commerce
search means candidate generation has to account for relevance,
personalization, and business value simultaneously, before the final
ranker ever sees the candidates — if any of those three is missing from
candidate generation, the final ranker can only rank what it was given,
not recover candidates that were never generated.

**Identifier design.** VARG-ID builds each item's identifier from an
RQ-VAE semantic prefix (a coarse-to-fine, residual-quantized encoding
commonly used for generative retrieval identifiers), strengthened for
search relevance via bidirectional query-item contrastive learning. A
value-ordered third token is appended to this prefix, giving each
identifier both a fine-grained address and an explicit business-value
signal in one representation, rather than requiring a separate value-
scoring step after candidates are generated.

**Training curriculum.** Three supervised fine-tuning stages progressively
teach: (1) the mapping from items to their generative identifiers, (2)
query-to-semantic-identifier retrieval, and (3) personalized retrieval
conditioned on user context. Personalized training specifically combines
value-aware and hierarchy-aligned supervision with expanded user context,
and uses local ordinal supervision (LO-SFT) so the model learns the
correct local, within-cluster ordering that the value-ordered third token
is meant to encode.

**Reinforcement learning (Prefix-GRPO).** On top of the SFT stages,
Prefix-GRPO further aligns candidate generation with business value and
the ranking objective, using gated rewards for output legality, observed
user behavior, advantage relative to the downstream ranker, and search
relevance — combined with prefix-aware weighting so the reward signal is
distributed sensibly across the generated identifier's tokens rather than
applied uniformly.

**Operational design.** Because both the product catalog and user
behavior shift continuously, the system uses a coordinated daily update
procedure for products and the model that is explicitly designed to
preserve existing item addresses (so downstream systems and cached
mappings don't break) while still incorporating new products and fresh
behavioral feedback.

**Results.** Offline, on a catalog of tens of millions of products, the
paper reports identifier stability and gains in retrieval quality and
head-level value recall attributable to the SFT strategies and
Prefix-GRPO, each measured against their respective baselines. Online, a
14-day A/B test on 20% of Tmall App search traffic — with VARG's generated
candidates admitted directly to the existing final ranker — produced GMV
+1.45%, per-user IPV +0.22%, and PCTR +0.31%, and separate shopping-guide
query evaluations showed VARG holding competitive relevance while using a
smaller candidate quota than the baseline.

**What isn't in the abstract**: the exact RQ-VAE configuration (codebook
size/depth), the reward weighting scheme inside Prefix-GRPO, model scale
and training infrastructure, and a breakdown of which specific baseline(s)
the offline "respective baselines" comparisons and the online A/B test's
control arm actually were.

## Source

Chu, X., Zhu, J., Jin, M., Wang, J., Fang, X., & Zhang, W. (2026). *VARG:
Value-Aware and Ranking-Aligned Generative Retrieval for Dynamic
E-commerce Search*. arXiv:2609.14493 [cs.IR].
https://arxiv.org/abs/2609.14493
