# Agentic ML Exploration (A-MLE) for Ads Ranking

## TL;DR

Meta's ads ranking stack contains dozens of differentiated models, and the
real bottleneck to improving them is no longer model capacity or training
compute — it's the throughput of human ML iteration (research, implement,
train, debug, evaluate, launch), which takes a senior engineer days to
weeks per model. A-MLE is an autonomous LLM-agent system that runs this
iteration loop itself across a whole model portfolio: it generates
hypotheses, plans experiments, executes and monitors training runs,
analyzes results, and writes proposals, with humans reviewing at fixed
checkpoints instead of driving each step. Deployed across a real ads
ranking portfolio, it multiplied iteration throughput, delivered
measurable offline metric gains (up to +2.56% relative improvement in one
headline result), and exposed sizeable differences in reliability and
"exploration aggressiveness" across Claude, Gemini, and GPT model
families run through the same agent harness.

## Main Contributions

- Identifies and formalizes the **manual ML iteration bottleneck** in
  industrial ads ranking as the system-level constraint worth optimizing,
  rather than individual model architecture.
- Presents the **A-MLE architecture**: a single LLM agent orchestrating
  five stages (hypothesis generation, exploration strategy, experiment
  execution, result analysis, and a shared knowledge substrate) over a
  shared skill library and sandboxed execution layer, with human-in-the-loop
  checkpoints at each stage boundary.
- Deploys A-MLE across a representative model portfolio and evaluates it
  with a **tiered capability framework** — L1 tool availability, L2
  autonomous workflow execution, L3 open-ended exploration — including a
  headline model-improvement result and a **controlled cross-LLM
  comparison** (Claude Sonnet, Gemini, GPT families) using a fixed agent
  loop.
- Documents the **dominant failure modes** (hallucinated APIs, baseline
  drift, infrastructure fragility, over-confident triage, LLM-specific
  behaviors) and argues that orchestration-harness quality, not raw base
  model capability, is what governs reliability in practice.

## Main Benefits

- **Throughput**: multiple times the completed iterations per
  engineer-week versus a manual baseline, and clearly ahead of a
  semi-automated (scripted-helper) baseline — the gain comes from chaining
  phases end-to-end without engineer-mediated handoffs, not from
  automating any single phase.
- **Training reliability**: meaningfully higher training success rate on
  agent-triggered runs after automated debugging/retry, versus the
  baseline.
- **Proposal quality**: A-MLE-authored proposals pass human review gating
  at a much higher rate, attributed to more rigorous statistical analysis,
  cleaner documentation of null results, and explicit segment-level
  decomposition.
- **Long-tail coverage**: the biggest wins land on the long tail of models
  that historically get little senior engineering attention, since proven
  techniques can now transfer across structurally similar models
  automatically.
- **Concrete offline gains**: a multi-source exploration configuration
  (combining architecture and training-efficiency hypothesis generators)
  produced a +2.56% relative offline improvement on the paper's
  experimental benchmark model with a neutral/slightly positive training
  throughput impact (+0.42% QPS), well above single-hypothesis or
  multi-round single-source variants (+0.44% and +0.58% respectively).

## How to Set Up

This is an internal Meta research paper describing a production system;
**no public code, model weights, or reproduction package is released.**
There is nothing here to install or run directly. That said, the paper is
explicit enough about the pieces involved that the architecture could be
reimplemented against a different stack:

- **Agent loop**: any tool-using LLM agent framework (the paper's own
  cross-LLM study swaps in Claude Sonnet, Gemini 2.5, and GPT-4/5 behind
  the same fixed agent loop and prompts).
- **Skill library** (Appendix A of the paper): typed procedures for
  codebase navigation, training-config read/edit/validate, job
  launch/monitoring with infra-vs-divergence discrimination, offline
  evaluation with statistical-significance testing, and proposal
  authoring.
- **Sandboxed execution layer**: an isolated copy of the training
  codebase/infra where the agent can edit configs or architecture code,
  run type checks/unit tests, build, smoke-test, and submit full training
  jobs.
- **Shared knowledge substrate**: version-controlled Markdown "track
  record" documents, per technique and per model, that record what was
  tried and what happened, with eligibility annotations so future
  sessions can match a target model against prior evidence from
  architecturally similar models.
- **Human-in-the-loop checkpoints**: gating approvals after hypothesis
  generation, after exploration strategy/compute-allocation planning,
  after experiment execution/results, and after proposal authoring.

## Details

### Problem: the manual iteration bottleneck

A single manual iteration on one ranking model runs through six phases —
ideation, candidate prioritization under a compute budget, implementation,
training with failure recovery, evaluation triage against a rolling
baseline, and proposal preparation — each gated by a different bottleneck
(engineer familiarity, trade-off judgment, codebase complexity,
infrastructure stochasticity, metric variance). End to end this takes a
senior engineer days to weeks per model, and with a finite engineering
pool only a small subset of (model, technique) pairs ever get tried, so
proven techniques diffuse slowly and unevenly across a portfolio of
differentiated models.

### System design

A-MLE is a single tool-using LLM agent that walks five stages per session,
parameterized by a (model, objective, compute) triple:

1. **Hypothesis generation** — reads the model's recent training config,
   baseline metrics, and history of attempted techniques; proposes
   candidates from internal generators (model-internal-state analyzers,
   training-efficiency analyzers, literature retrievers) scored by an LLM
   critic for novelty/feasibility. Hypotheses are grounded in the model's
   *current* state rather than a stale snapshot, since techniques tuned to
   an old baseline often don't transfer after a refresh.
2. **Exploration strategy** — given a compute/run/wall-time budget, plans
   an experiment sequence that interleaves exploration (validating
   hypotheses in isolation) with exploitation (combining and pushing the
   most promising ones). This is negotiated with a human reviewer since
   aggressiveness-vs-compute trade-offs need explicit sign-off.
3. **Experiment execution** — edits config/architecture code in a
   sandboxed copy, runs checks/tests, builds, smoke-tests, then submits
   the full training job; monitors progress, distinguishes infra errors
   from genuine divergence, retries or reroutes remaining compute rather
   than abandoning the session on a single failed branch.
4. **Result analysis** — computes statistical significance against a
   *rolling* baseline (to avoid baseline-drift blind spots), decomposes
   metrics by segment to catch localized regressions, triggers an
   automatic re-run when within-run variance is too high, and produces a
   leaderboard that either feeds back into another strategy round or
   becomes a final proposal.
5. **Shared substrate** — each session reads and writes a long-lived,
   version-controlled Markdown knowledge base (per technique, per model)
   so outcomes on one model become discoverable evidence for another;
   models are matched to relevant prior evidence via structured
   eligibility annotations.

Every stage boundary is a human checkpoint — the paper frames this as
combining the agent's breadth (wide search-space coverage) with the
engineer's judgment (catching edge cases, trade-offs, hallucinated
changes) while bounding the blast radius of any one agent decision.

### Evaluation framework and results

Evaluation uses a three-tier capability framework:

- **L1 (tool availability)** — single-step questions over training
  config, eval strategy, metric stores, and infra. A domain-equipped A-MLE
  reached 68% accuracy vs. 16% for a generic ML agent (cross-portfolio
  tools, no domain knowledge) and 8% for a generic LLM with no tooling —
  the gap was largest on job-config modification, where only the
  domain-equipped agent solved all questions.
- **L2 (autonomous workflow execution)** — multi-step tasks (baseline
  refresh, variance testing across duplicate runs, a config-change
  experiment with side-by-side comparison, batch offline evaluation) that
  require submitting, monitoring, and summarizing asynchronous jobs. The
  domain-equipped agent completed all four representative tasks reliably,
  which the paper attributes to an explicit "wait for external event"
  operator, infra-vs-divergence discrimination, and robust summarization
  under noisy multi-run output.
- **L3 (open-ended exploration)** — given a model, objective, and compute,
  find the best improvement. On the paper's benchmark model, a
  multi-source hypothesis strategy (architecture + training-efficiency
  generators) reached +2.56% relative offline improvement with neutral
  training-throughput impact, well above single-hypothesis or
  multi-round single-source variants.

A **cross-LLM study** held the agent loop/skills/prompts fixed and swapped
the underlying model. At L2, Sonnet ≥3.5, Gemini 2.5, and GPT-5 clustered
in the 90s for task completeness; other models frequently hallucinated
workflow IDs or failed to handle asynchronous waits. At L3, Gemini 2.5 and
GPT-5 explored more aggressively under a basic prompt, while the Sonnet
family was more conservative by default — but under a "stressful,
competitive" prompt, Sonnet 4.0 produced the single largest improvement of
any configuration, while GPT-5 became *more* conservative and gave back
most of its basic-prompt gains. The paper reads this as evidence that
prompt sensitivity and exploration aggressiveness are model-family
specific and don't move monotonically with prompt pressure.

Across the deployed portfolio, A-MLE surfaced and validated techniques in
five families: self-supervised pretraining, optimizer/loss tweaks,
embedding-based features, token-mixing architectures, and architecture
scaling — with the strongest results coming from *technique transfer*
(porting a technique already validated on one model to a structurally
similar model that hadn't tried it yet).

### Failure modes

The paper documents five recurring failure modes: hallucinated APIs
(caught by pre-flight checks, but wasting compute), baseline drift
(mitigated but not eliminated by rolling-baseline comparison),
infrastructure fragility mistaken for training divergence (addressed by
extending the retry/discrimination loop), over-confident triage on a
single noisy seed (addressed by an auto re-run rule), and LLM-specific
failures such as hallucinated workflow IDs or non-monotone behavior
change under prompt stress in weaker or less-aligned base models.

### Discussion and future work

The authors' central takeaway is that agent reliability is governed more
by the surrounding orchestration harness — skill-library coverage,
statistical rigor of the eval pipeline, resilience to infra noise — than
by the raw reasoning capability of the underlying LLM, and they expect
this gap to persist even as base models improve. Future work outlined:
deepen resilient execution (better infra-noise vs. divergence
discrimination), strengthen hypothesis generation with richer
domain-specific skills, and extend from a "breadth" regime (scaling
proven techniques across many models) toward a "depth" regime where the
agent participates in designing new architectures/pipelines with the
engineer as architect-in-chief.

### Limitations / caveats

- All results are internal, on a proprietary industrial ads ranking
  portfolio at Meta; no public benchmark, dataset, or code is released, so
  the reported numbers are not independently reproducible.
- Several headline metrics (throughput multiplier, training success rate,
  proposal acceptance rate) are reported qualitatively/relatively rather
  than with exact figures in the text.
- Model identities in the portfolio are anonymized (M₁, M₂, …), and most
  detailed ablations are run on a single experimental model (M*), so
  generalization across the full portfolio is asserted rather than shown
  in full detail.

## Source

Gao, E., Sunkara, V. K., Guan, J., Jia, Q., Xu, H., Ji, X., Wong, S.,
Chavali, S. T., Vaishnavi, P., Pandhi, A., Deng, X., Wang, Z., Inani, S.,
Yang, F., Moberg, J., Zu, Z., Bievre, N., Khenissi, S., Jaspal, A.,
Fakharizadi, E., Viswanathan, S., Sun, D., Vanam, A., Iyer, S., Yadawad,
S., Chen, W., Nahum, G., Gu, J., Chu, P., Liu, Y., Zhao, X., Cid, V.,
Chen, C., Pappu, V., Kumar, A., Chen, W., Schulte, B., Chandra, D., &
Tewari, R. (2026). *Agentic ML Exploration (A-MLE) for Ads Ranking*. Meta
Platforms, Inc. https://arxiv.org/html/2609.08248v1
