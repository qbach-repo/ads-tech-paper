# QueryFormer: Winning Solution for KDD Cup 2026 Tencent UniRec Challenge

## TL;DR

The 1st-place Industrial Track solution to the KDD Cup 2026 Tencent UniRec
Challenge, a post-click conversion-rate (pCVR) prediction task requiring
one architecture to jointly model non-sequential feature interactions and
sequential user behavior. The authors observe that existing "unified"
architectures generate the query tokens that bridge these two feature
types using simple projection MLPs, with no explicit attention refining
the query side. QueryFormer replaces that with a stackable field-sequence
block that generates queries via cross-attention and packs multiple
sequence queries into shared-parameter attention for efficiency. It won
the competition (test AUC 0.83254, later improved to 0.832713) and, per
their ablation, the query-generation mechanism is the single largest
contributor to that result — while keeping inference latency for 8 packed
queries to under 2x that of a single query.

## Main Contributions

- Diagnoses a specific architectural gap in prior "unified field-sequence"
  models for CVR/CTR prediction: they generate the query tokens used to
  read out sequence information via plain projection-based MLPs, without
  any explicit token-to-query attention step to refine the query
  representation itself.
- Proposes **QueryFormer**, centered on a stackable unified field–sequence
  block that bridges non-sequential multi-field features and behavioral
  sequences, generating queries via cross-attention rather than a
  projection MLP.
- Introduces **packed shared-parameter cross-attention**, which packs
  multiple sequence queries into one shared-parameter attention operation,
  keeping inference latency close to flat as the number of queries (view
  width *H*) grows.
- Runs a **latency-aware scaling study** across view width *H*, model
  width, depth, data, and compute — treating inference cost as a first-
  class constraint alongside accuracy, rather than optimizing offline AUC
  in isolation.

## Main Benefits

- **Competition-winning accuracy**: 1st place in the Industrial Track with
  an official test AUC of 0.83254, improved to 0.832713 with a modest
  post-competition scale-up.
- **Efficiency**: packed shared-parameter cross-attention keeps H=8
  inference latency to only 1.89x that of H=1 — i.e. generating 8x the
  query views costs well under 2x the latency, positioning the block as a
  genuinely stackable, efficient unit rather than one that trades accuracy
  for a proportional latency hit.
- **Ablation-confirmed source of gain**: query generation (the
  cross-attention mechanism, as opposed to the baseline's projection MLP)
  is identified as the largest single contributor to QueryFormer's
  accuracy improvement.
- **Favorable scaling**: within their experimental grid, scaling view width
  *H* improves validation AUC from 0.84540 to 0.84615 and beats the
  HyFormer baseline architecture at comparable compute budgets.

## How to Set Up

This is a competition solution report built on the **KDD Cup 2026 Tencent
UniRec Challenge's** industrial dataset; **no public code or dataset release
is indicated** in the abstract. There is no repository to clone. What the
paper does specify as reusable design elements:

- A **stackable unified field–sequence block** that takes both
  non-sequential multi-field features and behavioral sequences as input.
- **Cross-attention-based query generation** in place of a projection MLP,
  as the mechanism to build the query tokens that read out sequence
  information.
- **Packed shared-parameter cross-attention** to amortize the cost of
  multiple query "views" (controlled by width *H*) through one shared set
  of attention parameters, instead of paying a near-linear latency cost per
  additional view.
- A **latency-aware scaling methodology**: sweep view width, model width,
  depth, data volume, and compute together, and report both validation AUC
  and inference latency at each setting, rather than reporting accuracy
  alone.

## Details

This is a short competition-solution paper; the abstract covers the
architectural idea, the scaling study's headline findings, and competition
results, but not full training configuration. Within that scope:

**Problem framing.** Post-click conversion-rate (pCVR) prediction needs a
single model that handles both non-sequential, multi-field features (the
kind DCN- or FM-style architectures are built for) and long, sequential
user-behavior histories (the kind sequence/attention-based architectures
are built for). The KDD Cup 2026 Tencent UniRec Challenge specifically
calls for a *unified* architecture that does both well, rather than
treating them as separate sub-problems bolted together.

**Diagnosis of the baseline gap.** The authors observe that prior unified
architectures typically generate the "query" tokens — the representations
that pull information out of the behavioral sequence for a given candidate
— using simple, projection-based MLPs applied to the non-sequential
features. There is no explicit attention step where the query itself gets
refined by attending back to the token space before it's used to query the
sequence.

**Method.** QueryFormer's central component is a stackable unified
field–sequence block. Rather than a projection MLP, queries are generated
through cross-attention, letting the query representation be shaped by
attending over the relevant tokens before it is used. To keep this
affordable at inference time when multiple query "views" (width *H*) are
used, QueryFormer packs the sequence queries for all views into one
shared-parameter attention operation, rather than running *H* independent
attention computations.

**Scaling study.** The authors run a latency-aware scaling sweep over view
width *H*, model width, depth, data scale, and compute budget. Within their
grid, increasing *H* improves validation AUC from 0.84540 to 0.84615 and
outperforms the HyFormer baseline architecture at matched budgets, while
the packed shared-parameter attention keeps H=8 inference latency to 1.89x
that of H=1 — i.e., substantially sub-linear latency growth in the number
of query views.

**Results.** QueryFormer achieved 1st place in the Industrial Track of the
KDD Cup 2026 Tencent UniRec Challenge with an official test AUC of
0.83254; a modest post-competition scale-up pushed this to 0.832713. The
paper's ablation study identifies query generation (i.e. the cross-
attention mechanism replacing the baseline's MLP projection) as the
largest single contributor to the accuracy gain.

**What isn't in the abstract**: the exact dataset size/composition (though
it is presumably the same UniRec CVR dataset referenced by other KDD Cup
2026 Tencent UniRec Challenge papers), full hyperparameters, the specific
ablation table breaking down each component's contribution beyond "query
generation is largest," and training infrastructure/compute details.

## Source

Zhou, Y., & Zeng, Z. (2026). *QueryFormer: Winning Solution for KDD Cup
2026 Tencent UniRec Challenge*. arXiv:2609.16548 [cs.AI].
https://arxiv.org/abs/2609.16548
