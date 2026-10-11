# LITERATURE_MAP — ARC-AGI approaches, state as of 2026-10-12

Compiled 2026-10-12 by a research agent from primary sources, then kept by hand. **Legend:** V = verified
(URL fetched this session); R = seen only in search snippets. Scores are *author-claimed* unless marked
*ARC-verified* (ARC Prize semi-private, pass@2). Licences checked via the GitHub API on 2026-10-12.
Every row must keep its status tag; nothing here is a fact until it is V.

## 0. State of play (V)
- ARC-AGI-2 frontier (arcprize.org/results): GPT-6 95.0%, GPT-6.1 Sol 94.2%, Claude Opus 5.5 93.3%,
  Fable 5.1 90.0%; open-weight Qwen3.8-27B 42.4%, DeepSeek V4.1 Flash 72.9%.
- Kaggle ARC-AGI-2 2026 public LB (Kaggle API, 2026-10-12): Tufa Labs 88.06, rabbithole 80.56,
  Yi-Chia Chen 77.22, nvbanana 77.08. (The $150k bonus needs ≥85% on the *private* set.)
- Kaggle ARC-AGI-3 LB (2026-10-12): Yi-Chia Chen 62.96, Tufa Labs 56.52, mtg 45.00, NVARC3 40.97.
- Paper Track: $450k; six equal 0–5 criteria; must link a Kaggle ARC-AGI-2 or -3 submission (any score);
  "do not report train-set performance"; 1,500 words; CC-BY 4.0. 247 teams entered.

## 1. Test-time training of small models
| Entry | Contribution | Benchmark/protocol → result | Code/licence | Unsolved | |
|---|---|---|---|---|---|
| NVARC, Sorokin & Puget, Nov 2025 (2025 Kaggle 1st) | Qwen-4B, 16-token vocab; ~100k GPT-OSS-generated puzzles; 256 augs; TTT | Kaggle private 24.03% pass@2, $0.20/task, 12 h/4 GPUs; public 27.64% | Kaggle notebook; licence unverified | no failure analysis; TTT ensembling dropped | V |
| ARChitects 2025, Franzen/Disselhoff/Hartmann | LLaDA-8B masked diffusion + 2D RoPE; soft-mask recursive refinement; visit-count selection; LoRA pretrain + per-task TTT on L4 | private 16.53%; public best 21.67% ("overfitting to eval") | github LambdaLabsML/…; licence not stated | shape-model error multiplies | V |
| MindsAI/Tufa, Cole & Osman, arXiv 2506.14276 | TTFT + AIRV (augment-infer-reverse-vote) | ARC-1 private 58% (claimed); 2025 Kaggle private 12.64% | Kaggle notebook | ARC-2 transfer weak | V |
| "ARC-AGI-2 Technical Report", Oliveira et al., arXiv 2603.06590 | 200M LongT5, 2.3M synthetic tasks, per-task LoRA, 18 views × beam 10 | Kaggle semi-private 27.08%; no-TTT ablation 46→13.6 on own set | no code; CC BY-NC-ND | evaluated on home-made set | V |
| VARC, Hu…Andreas, He, arXiv 2511.14761 | ARC as image-to-image; ViT from scratch + TTT | ARC-1 60.4% (510-view vote, R) | lillian039/VARC, MIT | ARC-2 not in abstract | V |
| Multi-Perspective Transformers, Talley et al., arXiv 2605.01154 | TinyLM + TTT + product-of-experts | ARC-2 "evaluation set" 21.7% (split unclear) | none | size/compute unstated | V |
Lineage: Akyürek et al. 2024 (2024 paper 2nd, 47.5% ARC-1 semi-private).

## 2. Program synthesis / DSL search
| Entry | Contribution | Result | Code/licence | Unsolved | |
|---|---|---|---|---|---|
| Icecuber 2020 | brute-force C++ DSL search | ARC-verified 17.0% ARC-1 / 1.6% ARC-2 semi-private | MIT | combinatorial explosion | V |
| Hodel arc-dsl / re-arc | Python DSL + generators for 400 ARC-1 train tasks | — (standard synthetic source) | MIT | ARC-1 train only | V |
| Greenblatt, Jun 2024 | ~8k GPT-4o programs/task + revision | ARC-1 public 50% top-3; ~$40k | rgreenblatt/…, MIT | cost | V |
| CodeIt, Butt et al., ICML 2024 | hindsight replay self-improvement | 15% ARC-1 eval | BSD-3-Clause-Clear | low ceiling | V |
| SOAR, Pourcel/Colas/Oudeyer, ICML 2025 (2025 paper 2nd) | evolutionary search + hindsight fine-tuning | ARC-1 public test 52%; **no ARC-2 number** | flowersteam/SOAR, MIT | ARC-2 unreported | V |
| Pang, Sep 2025 | DreamCoder-style library, Grok-4 | ARC-2 semi-private 26.0% | no licence | 12 h limit | V |
| Berman, Sep 2025 | evolve NL instructions (Grok-4) | ARC-2 29.4% (R) | no licence | "dead reasoning zones" | V |
| Dyachenko, arXiv 2609.27242 | quantised Qwen3.5-4B seeds GA over closed DSL | 6/60 ARC-2 public tasks; GA alone 0 | none | 60 tasks only | V |
| ABPR, Qiu et al., arXiv 2603.20334 | LLM + Prolog meta-interpreter, algorithmic debugging | ARC-2 public pass@2 56.67% (Gemini-3-Flash) / 98.33% (GPT-5.5) | none | API models | V |
| Das et al., arXiv 2604.02434, ICML 2026 | object extraction + neural priors over DSL + cross-example consistency | ARC-2 public 16→24.4%; 30.8% with meta-classifier | CoreThink-AI/arc-agi-2-reasoner, Apache-2.0 | base LLM unnamed | V |
| aghasalim/arc-prize-2026 | object DSL + verifier search | 3.9% train, **0% public eval** | MIT | honest negative | V |
| Barbadillo, ironbar.github.io/arc25 | Python synthesis + TTT hindsight relabeling | 0 private ARC-2; transduction TTT 11.94 LB | no licence | RL collapse | V |

## 3. Compositional / induction vs transduction / hypothesis search
| Entry | Contribution | Result | Code/licence | Unsolved | |
|---|---|---|---|---|---|
| Li et al., arXiv 2411.02272 (2024 paper 1st) | Llama-3.1-8B induction vs transduction; ARC-Heavy 200k | ensemble 56.75 val; Kaggle private 19% | xu3kev/BARC, no licence | ARC-2 never run | V |
| Hypothesis Search, Wang et al., ICLR 2024 | NL hypotheses → Python | 30% on 100-task subset | MIT | small subset | V |
| Ouellette, arXiv 2507.15877 | controlled compositional-generalisation experiment | execution-guided synthesis composes; TTFT "elicits in-distribution knowledge" | none | — | V |
| Land, arXiv 2606.31543 | text/image/code modalities as search operators | ARC-2 semi-private 72.9% $38.99; templates and iterative refinement *hurt* | no licence | API-dependent | V |
| ArcMemo, Ho et al., arXiv 2509.04439 (runner-up) | concept-level lifelong memory | ARC-1 +7.5% relative | no licence | ARC-2 unreported | V |
| Moghe & Chin, arXiv 2607.06764 | Explorer-Definer orchestrator on DeepSeek V3.2 | ARC-1 public 67.25% $0.62; selection captures ~95% of ceiling | none | ARC-2 unreported | V |

## 4. Object-centric / neuro-symbolic / learned search
| Entry | Contribution | Result | Code/licence | |
|---|---|---|---|---|
| VSA, Joffe & Eliasmith, arXiv 2511.08747 (runner-up) | vector-symbolic object programs | ARC-1 eval 3.0% | MIT | V |
| LPN, Macfarlane & Bonnet, NeurIPS 2025 | latent program space + gradient test-time search | "doubles OOD" | Apache-2.0 | V |
| NSA, Batorski et al., ESANN 2026 | transformer-guided DSL search | "+27%" relative | — | V |
| TraceViT, Liu et al., arXiv 2607.29586 | looped ViT with intermediate-grid supervision | ARC-1 67.8% / ARC-2 24.3% pass@2 (split unstated) | "will be available" | V |
| CompressARC, Liao & Gu, arXiv 2512.06104 (2025 paper 3rd) | 76K-param MDL per puzzle, no training set | ARC-1 eval 20%; ARC-2 4% (R) | MIT | V |
| ARC-NCA, Guichard et al., arXiv 2505.08778 (runner-up) | neural cellular automata | unquantified | — | V |

## 5. Small recurrent / loop models
| Entry | Contribution | Result (protocol) | Code/licence | |
|---|---|---|---|---|
| HRM, Wang et al., arXiv 2506.21734 | 27M two-timescale recurrent net | ARC-verified 32% ARC-1 / 2% ARC-2; ARC blog: same-size transformer within ~5pp; puzzle-ID embedding means eval tasks must be in training | Apache-2.0 | V |
| TRM, Jolicoeur-Martineau, arXiv 2510.04871 (**2025 paper 1st**) | 7M single 2-layer net | ARC-1 45%, ARC-2 8% (pass@2, augmented voting); not ARC-verified | MIT | V |
| Roye-Azar et al., arXiv 2512.11847 | TRM ablations: blank puzzle-ID → 0%; 1000-vote ≈ +11pp | none | V |
| McGovern, arXiv 2511.02886 (HM) | pretrain TRM then post-train under Kaggle limits | ~10% public; 6.67% semi-private; **3.33–6.67 run variance** | none | V |
| Ren & Liu, arXiv 2601.10679 | HRM mechanistics: multiple fixed points, "guessing" | no ARC numbers | V |
| TARM, Rauba et al., ICLR'26 WS | autoregressive TRM | "no reliable gains" (negative) | V |
| PTRM, arXiv 2605.19943 | noise-injected recursion, Q-head selection | ARC-2 7.8→8.47 pass@1 (R) | V |
| BDH-CQ, Engdahl et al., arXiv 2608.09888 | 150M recurrent-latent ICL | ARC-1 public 29.5% pass@2 | pathwaycom/arc-task-gen, MIT | V |

## 6. Frontier LLMs and refinement systems (V)
Poetiq (generate→critique→refine→verify, Gemini 3 Pro): ARC-verified 54% $30/task, MIT but API-bound.
Berman / Pang / Land: 29.4 / 26.0 / 72.9, all frontier-API. Moghe & Chin: open-weight harness, no code.
None is Kaggle-eligible as published (no internet at evaluation).

## 7. ARC-AGI-3 (interactive)
| Entry | Contribution | Result | Code/licence | Unsolved | |
|---|---|---|---|---|---|
| Tech report, ARC Prize Foundation, arXiv 2603.24621 | 25 public / 55 semi-private / 55 private envs, ≥6 levels; S = min(1.15, h/a)²; level-weighted; **5n action cap**; 64×64×16 frames | launch: Opus 4.6 0.50%, Gemini 3.1 Pro 0.40% | ARC-AGI-3-Agents MIT | private set OOD from public | V |
| Human dataset post (2026-04-14) | 342 replays / 145 solves on the 25 public games; baseline = median human; cap 115% | — | dub.link release, licence unstated | — | V |
| ARC blog 2026-05-01 | failure modes: local-effect/false world model; wrong training analogy; "solved level, didn't learn game" | GPT-5.5 0.43% | — | — | V |
| GPT-6 Astra post (2026-09-03) | standard harness 62.7%; provider adapter 99.9% | GPT-6.1 Sol 52.73 / 96.37 | — | adapter state opaque | V |
| Milestone #1 (2026-07-06) | 1st Tufa "Duck": Qwen 3.6 27B FP8 coding agent in a REPL; 2nd Reki: Gemma-4-31B VLM → JSON actions + numpy click heuristic; 3rd forge | scores not on page | Kaggle notebooks | T4×2 default, RTX 6000 option | V |
| AERA, Liew, arXiv 2605.25931 | **all 25 public games fall to non-intelligent strategies; a null-coordinate bug bypasses 18** | RHAE 0.2116 with Qwen2.5-0.5B; private 0.30 | CC0 | public set non-discriminative | V |
| Tycho, Lehmann et al., arXiv 2607.28287 | programmatic world models (Moore machines), active abstraction | mean RHAE 88.49 (Opus 4.8); 100 with GPT-5.6 | Apache-2.0 | public only | V |
| Twin, Skoutnev…Ellis, Drori, arXiv 2608.14490 | test-time executable world model, replay-consistency repair | 93.3% on 25 public, 179/183 levels; **"goal inference is the hard part"** | MIT | public only | V |
| PRO-LONG, Fox et al., arXiv 2607.20064 | structured log + coding-agent search | 76.1% pass@1; 97.4% best@2 with Fable 5, $1,750 | MIT | public only | V |
| Rodionov, arXiv 2607.15439 | ablates executable WM / simplification / verification | gains from model generation > harness; warns of public-set saturation | none | held-out untested | V |
| Preview 2025 + Rudakov et al. arXiv 2512.24156 | StochasticGoose 12.58% (CNN+RL), Blind Squirrel 6.71%, graph-exploration 3.64% | — | just-explore MIT | — | V |

## 8. ARC Prize 2025 awards (V)
Kaggle: NVARC 24.03, ARChitects 16.53, MindsAI 12.64. Papers: 1st TRM ($50k), 2nd SOAR ($20k),
3rd CompressARC ($5k); runners-up VSA, Berman, Pang, ARC-NCA, ArcMemo; HMs incl. VARC, PoE, McGovern.
90 papers submitted. Pattern: existence proofs with a theory, paradigm comparisons, honest negative or
variance work. The 2026 rubric makes Theory + Universality a third of the score.

## 9. Evaluation methodology (V)
- ARC-AGI-2 Kaggle = 240 unseen tasks (120 semi-private + 120 private, inferred); human calibration: task
  kept if ≥2 of 407 solvers within 2 attempts; median 2.3 min.
- ARC-verified policy: single run, $10k cap; public vs semi-private agreement within ±3 pts (ARC-2), ±15 (ARC-3).
- Contamination: NVARC 27.64 public → 24.03 private; ARChitects 26 expected → 21.67 public; ARC-3 public
  set saturated (AERA, Rodionov).
- Why models fail on ARC-2: multi-rule, multi-step, contextual rule application, in-context symbol
  definition; PotARCin (arXiv 2609.27288): 25–52 pp gap between output accuracy and rule understanding.

## 10. GAPS a small team could close in 3–4 weeks (one GPU or Kaggle quota)
1. **ARC-AGI-3 public-set discriminativeness** — null-strategy battery vs published agents; Spearman of
   public RHAE vs Kaggle hidden score. CPU only. (AERA has the null-strategy half already.)
2. **Human replays as an exploration prior** — 342 released replays are used only for baselines.
   H: a prior distilled from human first-run traces cuts actions-to-first-level ≥30% vs uniform exploration.
3. **How transductive is TRM?** — per-task TRM from test demos alone vs 45% with ID embedding. One GPU.
4. **Seed variance of Kaggle-class TTT on ARC-AGI-2** — only McGovern's 3.33–6.67 exists. 5 seeds × 12 h.
5. **Synthetic-overlap audit** — remove nearest synthetic tasks, measure the drop. VARC-scale retrain.
6. **Per-axis complementarity on ARC-AGI-2** — Jaccard of solved sets across families. CPU + released preds.
7. **Open-weight refinement loop under Kaggle limits** — Poetiq-style loop on a 4-bit 27B within 12 h.
8. **Metric sensitivity of ARC-AGI-3 scoring** — re-score released replays under both baselines.

**Unverified items flagged:** per-task costs quoted from X posts; ARCANA 32.5%; VARC ARC-2; 2026
ARC-AGI-2 Kaggle hardware beyond "L4×4, 12 h" (confirmed separately from the Kaggle overview page).
