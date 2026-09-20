# Dense Feature Representation over Sequence Modeling: A Solution to the KDD Cup 2026 UniRec Challenge

## TL;DR

A 10th-place solution report from the KDD Cup 2026 Tencent UniRec Challenge
(industrial post-click conversion-rate prediction over 34.82M records) that
asks which mechanisms actually explain a leaderboard AUC gain, rather than
just chasing a bigger architecture. Using a 15-step single-variable upgrade
chain plus a separate leave-one-out ablation from the final model, the
authors find that reworking how *dense* (non-sequential) features are
represented, plus using an orthogonalized optimizer, account for nearly all
of a +0.0146 AUC improvement — while more elaborate sequence-modeling
components contribute almost nothing. They also document a validation-split
hazard: because the competition's train/validation split isn't time-based,
offline validation AUC is an inflated and sometimes sign-inverted proxy for
the true held-out leaderboard score.

## Main Contributions

- Separates "what was adopted" from "what actually caused the gain" using
  two different measurements: a chain of 15 single-variable adoption steps,
  and a leave-one-out ablation from the final model — and shows the two can
  disagree substantially about a component's importance (a component added
  early in the chain, on a weak baseline, can look unimportant there yet
  cost a lot when removed from the final model, and vice versa).
- A concrete dense-feature representation recipe (subgroup-tokenizing
  heavy-tailed user/item dense fields, `log(1+x)` transforms, aligned-pair
  projections through a shared tag-embedding table) that the ablation
  identifies as the single largest driver of the AUC gain.
- Evidence that an orthogonalized optimizer (AMUSE, a Muon-family optimizer)
  for dense parameters is the second-largest driver — ahead of any
  sequence-modeling change tried.
- Documents a generalization hazard from a non-temporal train/validation
  split: an adaptive sparse-ID regularizer and high-cardinality embedding
  scaling both flip sign between validation AUC and the true held-out
  leaderboard AUC, and a naive out-of-time re-split doesn't fully repair the
  mismeasurement either.

## Main Benefits

- Reallocates engineering effort: on this class of industrial CVR model,
  dense-feature engineering and optimizer choice look far higher-leverage
  than more elaborate sequence encoders.
- Offers a general auditing template — track both a step-by-step adoption
  chain *and* a separate leave-one-out ablation from the final model — for
  answering "where did our gain actually come from" on any production
  ranking model, since chain-position bias alone can mislead.
- Flags a concrete, transferable pitfall: a non-temporal (e.g. row-group)
  validation split can inflate and even invert the sign of offline metrics
  relative to true held-out performance, which is directly relevant to any
  team using row-based rather than time-based train/validation splits.

## How to Set Up

This is a competition solution report on a proprietary industrial dataset
(the KDD Cup 2026 Tencent UniRec Challenge's Round-2 UniRec CVR dataset,
34.82M click records across 57,691 row groups); **no public code or dataset
release is indicated.** There's no repo to clone or pipeline to run
end-to-end. The paper does give enough detail to reimplement the core ideas
against another CTR/CVR stack:

- **Dense-feature stack**: split heavy-tailed user/item dense fields into
  subgroup tokens, apply `log(1+max(x,0))` to heavy-tailed/raw-statistic
  columns, and add "aligned-pair" tokens that pool a shared tag-embedding
  table weighted by log-count.
- **Optimizer**: an orthogonalized, Muon-family optimizer (e.g. AMUSE) for
  dense parameters, paired with an adaptive regularizer (AdagradAR-style)
  for sparse embeddings, plus an EMA of the dense weights for checkpoint
  selection.
- **Training protocol**: multi-GPU data-parallel training, batch size 1024,
  a fixed-seed run (the paper explicitly flags the lack of multi-seed
  estimates as a limitation), and the specific hyperparameters listed in
  the paper's appendix tables.

## Details

### Problem and baseline

The task is post-click conversion-rate (pCVR) prediction for the KDD Cup
2026 Tencent UniRec Challenge, starting from the organizers' official
`PCVRHyFormer` baseline (test AUC 0.813237) on the Round-2 UniRec CVR
dataset — 34.82M click records across 57,691 row groups, split by row-group
order (not time) into training/validation, with a separate held-out
leaderboard test set from a different data dump.

### Method

Three mechanism families are explored:

- **Dense-feature representation** (largest contributor): the baseline
  pools user dense fields into a few tokens and leaves heavy-tailed columns
  (magnitudes up to 10^9) untransformed. The paper instead splits pooled
  user dense fields into five subgroup tokens, applies `log(1+x)` to
  heavy-tailed columns, and adds aligned-pair projections (dense columns
  paired with tag IDs, pooled through the categorical tag-embedding table)
  plus item-side dense splitting and raw-statistic channels.
- **Merged single-stream sequence modeling**: rather than one sequence
  encoder per behavior domain (which stops cross-domain events from
  attending to each other in time order), all domains are merged into one
  timestamp-ordered stream and encoded with stacked blocks that compress
  the sequence through decreasing top-*k* retention (following the LONGER
  architecture), read out via global tokens. A target-conditioned polarity
  gate (ported from TAPF) distinguishes exposure/click/conversion events of
  opposite polarity, and a masked-action-modeling (MAM) auxiliary head adds
  a denoising regularizer during training.
- **Optimization**: dense parameters use AMUSE, a Muon-family optimizer
  that orthogonalizes updates, with an EMA of dense weights for best-model
  selection; sparse embeddings use AdagradAR, an Adagrad variant with an
  adaptive regularizer that penalizes memorizing rare IDs.

A separate scaling study (model width 160→320, and extending the
per-domain/merged sequence budget) finds width scaling gives only small,
within-noise-band gains and sequence-length scaling gives none — capacity
was not the bottleneck.

### Experiments and results

Training uses 7 GPUs (six-way data parallelism), 5 epochs, and a 530M
parameter model (179M dense, 351M sparse). A single seed-replication run
established a ±0.0004 "seed band" used as a rough noise floor (no
per-step multi-seed estimates were run — an explicit limitation).

The 15-step single-variable adoption chain moves test AUC from 0.813237 to
0.827816 (+0.014579 total); splitting user dense fields into subgroup
tokens alone contributes +0.007988 (55% of the total gain), and the four
dense-representation steps together contribute +0.011183, while no
sequence/training-objective step (LONGER, MAM, merged backbone, TAPF) adds
more than +0.0003. The final leaderboard submission (adding a per-token
FFN and training on the full data without a validation holdout) reaches
0.828535 test AUC, placing 10th.

Because adoption order can bias a chain's deltas (an early-adopted
component is judged against a weaker baseline), a **leave-one-out
ablation** from the full final model gives a cleaner attribution: removing
the dense-representation stack costs 0.009496 AUC (an order of magnitude
larger than anything else); replacing the orthogonalized optimizer with
AdamW costs 0.002821; removing the AdagradAR sparse regularizer costs
0.000890; every other individual component falls within or adjacent to the
±0.0004 seed band. This correction flips some components' apparent
importance relative to the chain (e.g. the optimizer looked minor when
added early in the chain but is the second-largest factor by leave-one-out).

### The validation-split hazard

Because training and validation share one time window under the
competition's row-group split, validation AUC is an inflated and sometimes
misleading proxy: the full model scores 0.842 on validation but only 0.828
on the true held-out leaderboard test set — a ~0.014 gap. Worse, some
changes *invert sign*: the AdagradAR regularizer lowers validation AUC
(0.84150→0.84119) while raising test AUC (0.826596→0.827227), and
enlarging high-cardinality ID embeddings shows the mirror pattern in
earlier-round data (validation up, test down) as memorized IDs help
in-window but misfire on a different data dump. An out-of-time re-split
recovers a more honest overall scale but still doesn't recover the correct
sign for the regularizer change, pointing to dump-to-dump distribution
shift rather than pure time-ordering as the underlying cause. The paper's
conclusion: verdicts must come from the true held-out leaderboard, not
in-dump validation.

### Negative results and limitations

Several plausible techniques did not survive: an explicit DCN-v2
feature-crossing bypass, a target-conditioned query gate, and a
category-level target-attention retrieval module all hurt validation AUC
enough to be judged negative-expected-value without a leaderboard
submission; a gated self-attention sequence encoder and hand-built
behavior features (time-of-day, intent, price ordinals) were tested on the
leaderboard directly and produced no gain beyond the dense-and-optimizer
stack. The authors flag as limitations: single-run (not multi-seed) deltas
throughout, a capped number of daily leaderboard submissions, and a
validation split whose bias is only partially correctable by a
time-ordered re-split.

## Source

Zhang, Y., & Ji, W. (2026). *Dense Feature Representation over Sequence
Modeling: A Solution to the KDD Cup 2026 UniRec Challenge*.
arXiv:2609.19787 [cs.IR]. https://arxiv.org/abs/2609.19787
