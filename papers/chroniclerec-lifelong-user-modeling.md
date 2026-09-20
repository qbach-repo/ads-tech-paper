# ChronicleRec: Pre-training Temporally Anchored Tokens for Lifelong User Modeling

## TL;DR

A framework for compressing a user's entire (thousands-of-actions-long)
behavior history into a small, reusable set of "Chronicle Tokens" that can
be cached per user and reused across candidate-scoring calls, instead of
either truncating the history (losing long-range signal) or retrieving
target-relevant behaviors fresh for every candidate (coupling long-sequence
modeling to online candidate scoring and adding repeated cost). Unlike
prior target-independent compression methods, ChronicleRec compresses the
sequence once into a *chronologically ordered* set of tokens — interleaving
summary tokens among the actual history and using a causal encoder so each
summary token only reflects the history up to its own point in time —
rather than lumping everything into a single bidirectionally-encoded,
unordered summary. On KuaiRand and Tencent AdLive it outperforms
recent-window and single-pass compression baselines, approaches
full-attention performance, and a seven-day online A/B test confirmed
significant production gains.

## Main Contributions

- Diagnoses a structural weakness in recent target-independent sequence-
  compression methods: they append query/summary tokens at the *end* of
  the sequence and encode bidirectionally, which produces summaries that
  are unordered and redundant and discard the sequence's temporal
  structure.
- Proposes **Chronicle Tokens**: rather than one summary appended at the
  end, query tokens are *interleaved* with the merged behavior sequence and
  processed with a **causal encoder**, so each token summarizes only the
  history that occurred before its own temporal position — producing a
  chronologically ordered set of summaries instead of one undifferentiated
  blob.
- A **recency-aware multi-granularity merge**: recent behaviors are kept
  at high resolution while distant history is progressively coarsened,
  rather than treating all historical actions at uniform granularity.
- A **multi-horizon pre-training design** that masks different
  recent-history windows across parallel branches, teaching the compressor
  to learn complementary long-range interests rather than a single fixed
  notion of "recent."
- A **mask-and-predict pre-training objective**: the compressor is trained
  to reconstruct held-out recent behaviors from the compressed older
  history, explicitly aligning what gets preserved in the compressed
  representation with what's predictive of near-present user intent.
- Because Chronicle Tokens are **target-independent**, they can be
  computed once and cached per user, decoupling expensive ultra-long-
  sequence modeling from the latency-sensitive online candidate-scoring
  path — unlike lifelong-interest methods that retrieve target-relevant
  behavior per candidate.

## Main Benefits

- **Removes a real production trade-off**: teams no longer have to choose
  between truncating user history (cheap but lossy) and per-candidate
  target-relevant retrieval (expressive but expensive and repeated online);
  Chronicle Tokens are computed once per user and reused.
- **Empirically closes most of the gap to full attention**: on KuaiRand and
  Tencent AdLive, ChronicleRec outperforms recent-window and single-pass
  compression baselines and approaches full-attention performance, which
  is normally infeasible to run online at ultra-long sequence lengths.
- **Interpretable structure**: token-level analysis shows the learned
  Chronicle Tokens are temporally organized and complementary rather than
  redundant, which is the property the method was specifically designed to
  produce (in contrast to prior bidirectional, end-appended summarization).
- **Validated in production**: a seven-day online A/B test confirmed
  significant gains, not just offline metric improvements.

## How to Set Up

This is a research paper evaluated on a mix of a public benchmark
(**KuaiRand**) and a proprietary industrial dataset/system
(**Tencent AdLive**, including a live seven-day A/B test); **no code
release is indicated** in the abstract. KuaiRand itself is a publicly
available recommendation dataset (from Kuaishou) commonly used in the
recommender-systems literature, so the offline half of the evaluation
could plausibly be reproduced against that dataset if the authors' training
code/configuration becomes available; the online A/B test portion is not
reproducible outside Tencent's production environment. From the abstract,
the reusable design elements are:

- **Chronologically-ordered compression**: interleave query/summary tokens
  within the sequence (not just appended at the end) and encode causally,
  so each summary token only sees history up to its own temporal anchor.
- **Recency-aware multi-granularity merging**: keep recent behavior at
  fine granularity, coarsen distant history.
- **Multi-horizon masking during pre-training**: mask different recent-
  history windows across parallel branches to learn complementary
  long-range representations.
- **Mask-and-predict pre-training objective**: reconstruct held-out recent
  behaviors from the compressed older history.
- **Cache the resulting tokens per user**, target-independently, so
  downstream candidate scoring doesn't need to re-run sequence compression
  per candidate or per request.

## Details

This is a research paper; the abstract describes the motivation,
architecture, and evaluation results at a level of detail typical for a
top-tier submission, though without full training/architecture
hyperparameters. Within that scope:

**Problem framing.** Modeling a user's ultra-long behavior history (often
thousands of historical actions) is valuable for both recommendation and
online advertising, but feeding that much raw history into a ranking model
for every scoring call is computationally prohibitive, while truncating it
discards long-range signal that can matter for lifelong-interest modeling.
Existing "lifelong-interest" methods address this by retrieving only the
behaviors relevant to each specific candidate — but this couples long-
sequence modeling to candidate scoring itself, meaning the expensive
retrieval step has to run again, online, for every candidate. More recent
target-independent compression methods avoid that coupling by producing a
cached, reusable user summary — but the paper identifies a specific flaw
in how they do it: they append query/summary tokens at the end of the
sequence and encode the whole thing bidirectionally, which produces
summaries that are unordered and redundant, throwing away the sequence's
inherent temporal structure.

**Method.** ChronicleRec is a pre-train-and-transfer framework that
compresses a user's ultra-long behavior sequence exactly once into a
chronologically ordered set of Chronicle Tokens:

- A **recency-aware multi-granularity merge** preserves recent behaviors
  at high resolution while coarsening distant history, rather than
  compressing everything uniformly.
- Query tokens are **interleaved with the merged sequence** (not appended
  at the end) and processed with a **causal encoder**, so each query token
  ends up summarizing only the history that precedes its own temporal
  anchor position — giving the resulting tokens an explicit, ordered
  temporal structure rather than one undifferentiated summary vector.
- A **multi-horizon design** masks different recent-history windows across
  parallel branches during training, so the model learns several
  complementary views of "what's recent" rather than a single fixed
  window.
- The compressor is **pre-trained with a mask-and-predict objective**:
  held-out recent behaviors are reconstructed from the compressed older
  history, which aligns what the compression keeps with what's actually
  predictive of near-present user intent.

Because the resulting Chronicle Tokens don't depend on which candidate item
is being scored, they can be computed once and **cached per user**,
decoupling the expensive ultra-long-sequence compression step from the
latency-sensitive online candidate-scoring path — in contrast to
lifelong-interest methods that must retrieve target-relevant behavior
freshly for every candidate.

**Results.** On the public **KuaiRand** benchmark and the industrial
**Tencent AdLive** setting, ChronicleRec outperforms both recent-window
and single-pass compression baselines and approaches the performance of
full attention over the uncompressed sequence — which is generally
infeasible to run online at these sequence lengths. Token-level analysis
of the learned Chronicle Tokens shows they are temporally organized and
complementary (i.e., different tokens capture different, non-redundant
aspects of the user's history), which is the specific property the causal,
interleaved design was intended to produce, in contrast to the unordered,
redundant summaries the paper attributes to prior bidirectional,
end-appended approaches. A seven-day online A/B test on production traffic
confirmed the gains carry over beyond offline evaluation.

**What isn't in the abstract**: the exact merge/coarsening schedule
(how granularity decreases with recency), the number and size of Chronicle
Tokens produced per user, model architecture/scale, training compute, and
the specific offline metrics and magnitudes reported on KuaiRand/Tencent
AdLive beyond the qualitative "outperforms baselines, approaches
full-attention" description.

## Source

Huang, C., Sheng, Y., Guo, L., Liu, H., Pan, J., Zhang, S., Feng, Z., Zhou,
C., et al. (2026). *ChronicleRec: Pre-training Temporally Anchored Tokens
for Lifelong User Modeling*. arXiv:2609.12375 [cs.IR].
https://arxiv.org/abs/2609.12375
