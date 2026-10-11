# BoltzGen performance work: process and evidence

Review date: 11 October 2026.

The objective was to reduce execution time while preserving the scientific
results. The main campaign ran from 7 to 11 October 2026. It established a
repeatable baseline, profiled the pipeline, and qualified changes to model
initialization and repeated GPU execution. Earlier ESMFold2 performance work
was already part of the upstream build used as the baseline.

The final recorded comparison with original upstream is about 51.5 to 35.8 min
for the benchmark suite, or 30.5% less recorded processing time. This is a
historical cumulative comparison on the tested H100. The latest change also
has a contemporary comparison: 43.69 to 35.81 min, or 18.04% less time. These
percentages use different references and must not be added. Scientific outputs
matched exactly under the suite's comparison rules. The timing scope and the
limits of that claim are described below. Sources: [overview][overview],
[follow-up report][followup], and [completion audit][followup-completion].

This document reconstructs the work from the plans, reports, progress log,
tooling, Git history, and saved results. It does not report a new benchmark run.
Implementation details remain in the linked technical reports.

## What the initial outline gets right, and what needs qualification

| Initial description | What the records establish |
| --- | --- |
| Build quality and speed checks, then check every step | Yes, with different scopes. Harness tests, focused contracts, numerical screens, stage replays, and full pipeline checks served different purposes. Full qualification applied to frozen builds. Not every idea received a full benchmark. |
| Collect a wide range of inputs | Yes. The manifest covers 11 computational cases and several protocol branches. It is a functional coverage suite, not a representative sample of production job sizes or biological efficacy. |
| Profile deeply and turn observations into hypotheses | Yes. Pipeline ownership and process boundaries were mapped first. Broad timing, CPU profiles, GPU timelines, and selective kernel profiling produced a ranked hypothesis table. |
| Work through the hypotheses one by one | Partly. Initialization and GPU replay were qualified in separate campaigns. Some alternatives failed a numerical screen. Other ideas were deferred or required a different workload. The ranked list was not exhausted. |
| Report the change step by step and compare upstream with the fork | Yes. Separate reports cover each qualified campaign, with raw data and plots. A later overview gives the cumulative upstream comparison. Git alone does not contain the full experiment history. |
| Keep the machine in mind so the work can be rerun | Yes, but portability is incomplete. Runtime inventories, hashes, assets, and recovery checks were recorded. Important tooling and the latest patch remain untracked, and campaign helpers contain local paths. Another VM needs a fresh matched baseline. |

The repeated machine item in the initial outline describes the same practice.
The additional work included testing the measurement system itself, auditing
build identity, recovering from infrastructure failures, measuring memory,
checking unaffected stages for drift, and validating the published report.

## Timeline and phase summaries

Dates are UTC. The [progress log][lessons], saved report timestamps, and Git
history establish this sequence. Older pending-work entries in the progress log
are superseded by its final outcomes.

| Date | Phase | One-line summary | Main evidence |
| --- | --- | --- | --- |
| 5–6 October 2026 | Earlier component work | ESMFold2 acceleration and analysis-worker improvements entered the upstream build before this campaign. | Commits `0c22d04`, `889a76e`, `f595c9a`, `cdcb2d9`, `f838393`; [H200 report][esm-performance]. |
| 7 October 2026 | Prepare the contract and runtime | Build and test the harness, select fixtures, provision assets, and qualify the installed environments. | [Suite guide][suite-guide], [prepared plan][prepared-plan], `results/setup/`. |
| 7–9 October 2026 | Establish the baseline | Preserve interrupted evidence, restart after a GPU identity change, and complete a repeatable full capture. | [H100 baseline][baseline-report]; [raw capture][historical]. |
| 9 October 2026 | Map and profile | Separate startup, model work, preparation, and reporting, then rank possible improvements. | [Profiling report][profile], [profiling plan][profile-plan]. |
| 9–10 October 2026 | Qualify initialization | Reject numerically different alternatives and retain an exact change after full checks and alternating controls. | [Initialization report][initializer], commit `312bfe2`, [experiment ledger][initializer-ledger]. |
| 10–11 October 2026 | Qualify GPU replay | Reprofile the accepted build, validate the next change, and measure it against that starting build. | [Follow-up report][followup], [experiment ledger][followup-ledger], [saved patch][followup-patch]. |
| 10–11 October 2026 | Report and audit | Generate plots from records, inspect the served reports, archive the previous report, and publish cumulative context. | [Completion audit][followup-completion], [overview][overview]. |

Original upstream is commit `a07fea1`. The initialization change is commit
`312bfe2`. The latest qualified build is that commit plus the saved follow-up
patch. At this review, the latter application changes and much of the supporting
material are still uncommitted. The relevant commit messages identify changes;
the numerical campaign evidence is mainly in reports, logs, and JSON files.

The earlier ESMFold2 work used a separate worker benchmark. It separated model
loading from request execution, checked deterministic outputs and random state,
and tested memory across changing inputs. A larger fixture became slower with
graph capture, so automatic execution was bounded by measured input size.
Timing observations affected by competing checkpoint loading were excluded from
the performance claim. The optional fused mode used a different numerical
backend and was reported separately. These decisions produced the
[H200 component report][esm-performance] and its benchmark tool; they are not
additional gains in the later H100 comparison. Earlier analysis-worker work was
also already upstream. The serial H100 suite does not measure worker scaling.

## Establish the workload before optimizing

The preparation phase defined what had to remain unchanged. It fixed the input
manifest, assets, model settings, numerical policy, and expected output
structure. The benchmark retained normal sampling work. It did not introduce a
reduced-step workload to make experiments cheaper.

| Contract item | Recorded setting |
| --- | --- |
| Inputs | 11 cases; most request 2 designs, the medium protein case requests 4 |
| Randomness | Seed `20261007`; deterministic execution; exact comparison with `atol=rtol=0` |
| Design schedule | 3 recycles and 500 sampling steps |
| Folding schedule | 200 sampling steps and 5 samples |
| External ESM schedule | 20 loops, 200 requested steps, and 5 samples; effective schedule preserved |
| Parallelism | 0 loader workers, 1 CPU math thread, 1 analysis process |
| Timing | 1 excluded warmup and 5 measured repetitions per case and build |
| Slowdown gate | No median slowdown greater than 5% for any applicable stage or complete case |

Sources: [suite guide][suite-guide], [case manifest][cases], and [raw baseline
settings][historical]. These choices define the experiment. They do not establish
performance under other worker counts, batch policies, or numerical settings.

Input selection followed behavior coverage. It included small monomers,
variable-length protein and peptide designs, deposited structures, scaffold
insertion, cyclic and disulfide constraints, cropped and partially hidden
targets, DNA, RNA, small molecules, covalent constraints, and inverse folding
without generation. Existing repository examples were reused. Additional
sequence fixtures filled gaps. The manifest recorded dependent structures and
scaffolds; tests checked that these indirect references were included.

The resulting [input lock][input-lock] records fixture and configuration hashes.
This made the workload reviewable before inference. It also prevented an input
or default-setting change from being mistaken for a speed improvement.

Preparation included real environment work. The initial VM lacked the runtime
and cached checkpoints. The installed environment needed compatible Torch and
accelerator packages, Python development headers, and a separate pinned ESM
runtime. Assets were downloaded before timing. The final H100 setup used Python
3.12.3, Torch 2.11.0, CUDA 13.0, and driver 580.173.02. Exact package freezes and
setup logs were saved. See [runtime preparation][suite-guide] and the
[baseline reproducibility record][baseline-json].

For another project, the output of this phase should be an explicit workload
contract, a coverage manifest, a dependency and asset inventory, and a decision
about which costs belong in the measurement.

## Validate the checks, then capture a baseline

The harness itself was tested before its verdicts were trusted. Its tests cover
missing and extra outputs, corrupted archives, non-finite predictions, identity
and rank changes, seeding, provenance, stage replay, warmup exclusion, and
per-case regression detection. They also check that a quality failure prevents
performance measurement and cannot be bypassed through recovery.

The saved logs distinguish stages of validation:

| Qualification | Recorded result | Evidence |
| --- | --- | --- |
| Initial harness qualification with scientific dependencies | 32 passed | [Harness log](../results/setup/contracts-harness-qualified.log) |
| Harness after recovery coverage was added | 34 passed | [Recovery test log](../results/setup/contracts-harness-recovery.log) |
| Aligned application environment before baseline capture | 858 passed, 36 skipped | [Application log](../results/setup/contracts-aligned.log) |
| Separate ESM environment before baseline capture | 49 passed | [ESM log](../results/setup/contracts-esm.log) |
| Initialization candidate | 947 passed, 36 skipped; separate ESM run: 49 passed | [Initialization report][initializer] and its retained logs |
| Follow-up candidate | 965 passed, 36 skipped; separate ESM run: 49 passed | [Follow-up report][followup] and its retained logs |

These are separate recorded test runs. Skips are not passes. The harness tests
establish the behavior of the checking system; model-backed runs establish
repeatability of the application on the selected inputs.

The initial capture was interrupted by VM restarts. Its quality references,
11 warmups, and 4 measured case runs were retained as partial evidence. The
physical GPU changed, so those timings were not combined with the later
capture. A fresh full capture on the final GPU completed on 9 October.

That capture has 11 quality references, 11 excluded warmups, and 55 measured
case runs. Every rerun passed exact comparison. Across them, 2,748 scientific
files matched after decompression: 2,682 were byte-identical, and the remaining
66 compressed analysis tables had identical decompressed bytes. The median
suite pass was 51.53 min, with a 50.68–51.87 min range. Sources:
[baseline report][baseline-report] and [suite preparation history][suite-guide].

The transferable rule is to prove unchanged-build repeatability first. A
candidate comparison has little meaning if the reference itself changes
unpredictably, produces incomplete output, or spans different machines.

## Map costs and turn profiles into hypotheses

Profiling was a separate investigation with application changes out of scope.
It first mapped stages, process boundaries, intermediate files, model lifetime,
CPU and GPU responsibilities, and ownership of local and external code. This
showed which costs could be changed locally and which changes would affect
several protocol branches.

Detailed profiling used small, medium, and ligand workloads from the full suite.
The evidence streams were kept separate:

| Evidence stream | Purpose | Interpretation |
| --- | --- | --- |
| Uninstrumented controls | Check the current environment and observe stage latency | A single control is a screen, not a repeated performance result. |
| Lightweight boundaries | Locate loading, preparation, model, and writing costs | Inclusive host intervals can overlap asynchronous device work. |
| CPU profiles | Find expensive initialization and postprocessing | Profiler overhead prevents using these times as benchmark results. |
| Nsight Systems | Relate host dispatch, device activity, transfers, and idle gaps | Device activity is not a direct measure of useful utilization or removable latency. |
| Selective Nsight Compute | Investigate a justified expensive operation family | Local observations do not establish a pipeline speedup. |

The completed investigation records 58 stage executions and 14 exact case
comparisons. It includes 8 Systems traces, 7 CPU-profiled stages, and a
selectively profiled Compute stage. All comparisons passed. The instrumentation
and baseline were audited separately. See the [profiling report][profile],
[timeline data][profile-json], and [CPU data][cpu-json].

The report converted observations into a ranked table. Each hypothesis named
the affected workloads, ownership, measured cost or estimated opportunity,
correctness hazards, and next experiment. Estimates were explicitly conditional
and overlapping. They were not added into a promised total saving.

For example, initialization occupied 17.39 s of inclusive CPU profile time in
short folding. That justified an experiment; it was not an achieved saving.
Repeated score evaluation occupied 50.11 s of inclusive host time versus
4.96 s of summed device kernel time in the short-design trace. That supported
investigating dispatch overhead. These are different timing boundaries under
instrumentation, not quantities to subtract into a guaranteed benefit.

This stage also ruled out misleading priorities. A backend warning did not show
that the warned-about operation dominated runtime. Observed synchronization API
time did not explain the entire host/device gap. Reports and initialization
were real request costs even though neither was model arithmetic. Details and
the deferred hypotheses remain in the [profiling report][profile].

## Work through small experiments and qualify retained changes

The [optimization plan][optimization-plan] defined an experiment loop:

1. State a mechanism, the affected workload, a bounded opportunity, and the
   correctness risks.
2. Preserve the reference and freeze the candidate with source and test hashes.
3. Run focused contracts and exact representative output screens.
4. Measure uninstrumented repeated runs with a contemporary control.
5. Keep a supported change, reject a failed one, or record why an idea is deferred.
6. Recheck the final combined build across the full pipeline.

Commands, working directories, logs, failures, and decisions went into an
append-only experiment ledger. Progress summaries recorded the current state
and next action. This made long runs recoverable without treating an old
pending entry as unfinished work after qualification had completed.

### Initialization campaign

The first retained change reduced repeated initialization work while preserving
initialized values and random-state consumption. Focused tests checked exact
values and subsequent random state. Whole-model checks compared initialized
and restored state, checkpoint coverage, and random streams across the affected
model types. Initialization was preserved for training as well as inference.

Two algebraic alternatives were rejected before an application patch or timing
campaign. In a screen of 1,000,000 uniform draws, one differed in 394,419 float64
values and the other in 3,272. Both happened to match in float32 in that screen.
The record explicitly labels this a numerical rejection, not a measured
end-to-end candidate. See the [rejection record][algebraic-screen].

The retained candidate passed stage screens, contracts, and full integrated
checks. Both builds completed 11 quality cases and 66 independently checked
reruns. Both also matched the historical quality references directly. The
recorded suite medians were 52.92 to 44.78 min. However, unchanged analysis,
filtering, sequence sampling, and external ESM stages also became faster.
That full difference could not be attributed solely to initialization.

Alternating folding controls then supplied narrower evidence:

| Case | Upstream folding median | Candidate folding median | Saved |
| --- | ---: | ---: | ---: |
| Short monomer | 48.99 s | 44.50 s | 4.49 s |
| Medium protein | 74.54 s | 70.40 s | 4.14 s |
| Large ligand case | 76.99 s | 72.51 s | 4.48 s |

All 36 replays passed exact comparison. These stage gains supported retaining
the change, which became commit `312bfe2`. They are not full-request savings.
Sources: [initialization report][initializer] and [alternating controls][initializer-bracket].

### Follow-up campaign

The next campaign started from the accepted initialization build. It used
explicit labels for original upstream, starting build, and new candidate. This
prevented the earlier saving from being counted again.

A fresh profile confirmed that repeated host dispatch remained expensive.
The experiment reused a captured GPU execution sequence within a bounded
inference lifetime. Setup and capture remained inside stage timing. Focused
contracts checked exact outputs and random state, changing shapes and inputs,
changed weights, output independence, supported numerical modes, and training
behavior. The final focused suite contained 18 contracts. No scientific
candidate mismatch was recorded in this campaign.

Representative screens and a ligand-affinity screen preceded full qualification.
Alternating controls included changed stages and unchanged analysis/filtering.
This moved the drift check earlier than in the initialization campaign.

| Alternating control | Starting median | Candidate median | Interpretation |
| --- | ---: | ---: | --- |
| Short design | 65.33 s | 31.47 s | Clear observed reduction in the targeted workload |
| Medium design | 69.64 s | 38.46 s | Benefit extends beyond the smallest case |
| Large ligand design | 77.35 s | 50.91 s | Benefit in a different protocol branch |
| Large ligand folding | 69.58 s | 69.60 s | No material gain established |

All 36 alternating replays passed exact comparison, covering 144 stage
executions. Analysis/filtering medians moved by less than 0.7% in these controls.
A candidate profile separately confirmed that the intended execution mechanism
was active. Neither that trace nor the frozen-input replays replaced the
integrated pipeline check. Sources: [follow-up report][followup],
[controls][followup-bracket], and [mechanism record][mechanism].

The final full comparison passed all 83 case/stage gates at the unchanged 5%
threshold. Each build completed 11 quality cases and 66 checked reruns. The
completion audit checked 154 integrated comparison files and 22 direct
historical quality verdicts. The suite median changed from 43.69 to 35.81 min;
the recorded reduction was 18.04%. The qualified patch remained local and
reviewable. See the [completion audit][followup-completion].

### Disposition of the remaining ideas

| Idea | Recorded decision | What was actually established |
| --- | --- | --- |
| Skip initialization before restoring weights | Rejected as a shortcut | Identical restored weights would not ensure the same later random stream. No timed candidate established a safe gain. |
| Simplify the initializer's algebra | Rejected by numerical screen | Exact float64 values changed. No application patch or end-to-end timing was accepted for these variants. |
| GPU replay | Deferred in the first campaign; retained in the follow-up | A deferred idea became a new experiment with its own contracts and full qualification. |
| Narrow preparation reuse, compilation, deeper caches, larger-workload operation tuning, or cheaper reporting | Deferred | No qualified gain was recorded for these additional changes. Some opportunities overlap replay; others need new evidence or stronger invalidation checks. |
| Keep models resident, increase concurrency, or omit reports | Requires a separate workload | These change what the current fresh-process comparison measures. |
| Reduce sampling or change numerical/backend policy | Outside the main comparison contract | The accepted changes retained the scientific work and numerical policy. |

Sources: [initialization report][initializer], [follow-up report][followup], and
[handoff decisions][followup-plan]. This was a selective experiment process,
not a sequence of fully implemented candidates for every profile lead.

## How correctness was enforced, and what it does not prove

Correctness was an acceptance condition at several levels.

First, the workload and runtime were locked. Candidate checks inherited the
reference settings and rejected changed fixtures, assets, dependencies, harness,
or hardware. Source changes were expected, recorded, and frozen for qualification.
Import checks established that each interpreter used the intended build.

Second, randomness was controlled beyond a single top-level seed. The harness
seeded the language and numerical libraries, handled generators that otherwise
draw fresh entropy, seeded molecular conformer generation, and adapted the
isolated ESM worker while retaining its interpreter isolation. Fixed worker and
thread counts made execution order more reproducible. These adapters belonged
to the harness and were hashed with it.

Third, comparisons examined the scientific output set. They checked file
inventory, output counts, paired artifacts, structures, array keys and shapes,
data types, masks, values, metric rows, sequences, ranks, filter decisions, and
selected samples. Provenance was validated locally before permitted derived
hash differences were excluded. A successful subprocess with missing samples
could not pass.

Fourth, the initial quality run, every warmup, and every timed repetition were
checked. Timing started only after quality passed. Focused tests added evidence
for risks that final output comparison alone might miss, such as later random
state, training gradients, or reuse across changed inputs.

Exact scientific equivalence is not byte identity of the whole output directory.
Compression metadata and normalized output paths can differ. Configuration,
logs, generated input caches, PDFs, and plot assets are excluded from scientific
comparison, although their production remains timed where it occurs in a stage.
The checks also do not establish biological effectiveness, every supported input,
or exact behavior on every GPU. See the [comparison contract][suite-guide] and
[comparator tooling][comparator].

The process did not relax tolerances after a failed experiment. A separate
seeded, tolerant baseline is supported by the harness, but the reported H100
campaigns used exact comparison throughout.

## How speed was measured and noise was handled

The workload used a cached installation and fresh processes. Each stage loaded
what it needed and wrote its normal outputs. Downloads, asset hashing,
configuration, contract tests, and scientific comparison were outside stage
timing. Startup, construction, loading, preparation, inference, synchronization,
writing, and stage reports were included. Model-task timing was recorded
separately from parent-observed stage wall time.

Consequently, a complete-case total is the sum of its recorded stage wall times.
It is not literal elapsed time for the complete user CLI invocation. A future
change to configuration needs a separate measurement that includes configuration.

The campaigns reduced interference through serial GPU execution, idle-device
checks, fixed settings, excluded warmups, fresh output directories, and fixed
dependencies and assets. Filesystem and compiled-kernel caches were not cleared.
Warmups did not make the next process retain a loaded model. Read-only telemetry
recorded GPU identity, clocks, temperature, power, and memory at 1 min intervals.

Noise was not eliminated. Clocks remained unlocked. The historical medium case
ranged from 376.90 to 398.71 s. During initialization qualification, unchanged
contemporary upstream failed 11 historical stage gates, with about 0.4–0.56 s
or 5.1–6.3% slowdowns in affected stages. Sources: [baseline report][baseline-report]
and [drift investigation][lessons].

The response was to preserve historical timing failures and select a newly
captured contemporary upstream reference before candidate measured repetitions
had completed. Historical quality remained an independent exact check.
Thresholds were not weakened. Alternating build order provided a closer timing
comparison. Full integrated captures still ran as separate build runs; they
were not fully randomized or interleaved.

The performance gate checked stages and complete cases independently. An overall
gain could not hide a stage regression. Passing the 5% gate meant the candidate
avoided a disallowed slowdown; it did not itself demonstrate a speedup. The
reports retained every valid sample, showed variability, and did not claim
statistical significance from 5 observations.

## Report results without changing their meaning

The report generators read saved measurements and produced Markdown, JSON/CSV,
and standalone SVG/PNG plots. Each campaign included complete-case latency,
individual repetitions, per-case savings, representative stage comparisons,
and a stage heatmap. Quality and regression verdicts accompanied the timings.

The aggregation rules were explicit:

| Measure | Rule |
| --- | --- |
| Complete-case latency | Sum stage wall times within each run, then take the median across measured runs |
| Suite latency | Sum all case totals within each measured pass, then take the median across passes |
| Seconds saved | Reference median minus candidate median |
| Latency reduction | `100 * (reference - candidate) / reference` |
| Speedup | Reference median divided by candidate median |
| Geometric mean case speedup | Exponentiate the mean of the logarithms of case speedups |

Independent stage medians were not summed into a supposed complete-case median.
Ranges were not labeled confidence intervals. Absent stages were marked as not
applicable. Stage savings and campaign percentages were not added together.
See the [report generator][report-tool] and [machine-readable comparison][comparison].

The original-upstream overview is useful cumulative context. It is less tightly
controlled than the contemporary comparison of the latest change, since its
upstream observations were collected earlier. Both comparisons are reported;
neither replaces the other.

Memory was part of the result. The final overview records large-ligand reserved
memory rising from 6.84 to 9.56 GiB during folding and from 8.64 to 11.52 GiB
during affinity, compared with original upstream. These are separate stages.
Allocated and reserved memory overlap and must not be added. Ordinary harness
measurements do not capture the separate ESM worker's GPU peak. The profiling
probe did measure worker memory in selected runs, which is a different scope.
See [memory interpretation][overview] and [profiling measurements][profile].

Reporting included delivery checks. Pages and assets were staged, published to
the existing internal server, and checked for actual HTTP content and links.
Desktop, mobile, and dark-mode rendering were inspected. A plot legend overlap
was corrected. The previous report was archived, and report/browser tooling was
kept separate from the scientific runtime. The completion audit also checked
that published evidence referred to the frozen source and unchanged historical
reference. These are recorded historical checks, not a new availability check
performed for this document.

## Which practices mattered

The verdicts below concern this campaign. A deferred idea is not a failed
optimization, and a diagnostic tool can be useful without producing a patch.

| Verdict | Practice | Evidence and reason |
| --- | --- | --- |
| Crucial | Lock the numerical contract and check every rerun | All 66 reruns per qualified build were checked. The algebraic screen rejected 394,419 and 3,272 float64 differences before expensive benchmarking. [Rejection record][algebraic-screen]. |
| Crucial | Test the harness and output completeness | The 34-check recovery-era suite covered silent output loss, invalid data, seeding, and recovery barriers. Without this, a faster incomplete run could pass. [Suite guide][suite-guide]. |
| Crucial | Audit source, environment, and provenance | Copied fixture paths caused a historical comparison failure; a GPU change required a new baseline. Both were corrected without weakening the comparator. [Progress log][lessons], [baseline report][baseline-report]. |
| Crucial | Use contemporary and alternating controls | Unchanged upstream failed 11 historical stage gates. Alternating folding runs narrowed the initializer evidence to 4.14–4.49 s saved. [Initialization report][initializer]. |
| Crucial | Reprofile after an accepted change and validate the combined build | Commit `312bfe2` became the next reference. The follow-up then passed 83 full case/stage gates, with an 18.04% observed suite reduction against that build. [Completion audit][followup-completion]. |
| Helped | Use broad functional coverage and narrow early screens | The 11-case suite covers distinct protocols. The follow-up used representative screens and a ligand-affinity screen before full qualification. [Manifest][cases], [follow-up report][followup]. |
| Helped | Separate mechanism evidence from timing evidence | Profiles identified repeated host overhead; alternating short-design medians then changed from 65.33 to 31.47 s. The large-ligand folding control showed no material gain. [Follow-up report][followup]. |
| Helped | Keep ledgers, failed attempts, frozen patches, and persistent launchers | The aborted snapshot campaign and launcher errors remain inspectable. Completed captures were preserved where valid, rather than repeated blindly. [Progress log][lessons]. |
| Helped | Audit plots, publication, and completion | The initializer publication checked 67 HTTP responses and recorded a corrected legend overlap. Final audits also tied outputs back to the qualified source. [Initializer completion record][initializer-completion]. |
| Little value as proof of improvement | Single controls or instrumented wall times | Early short-design controls moved from 81.34 to 76.53 s without an optimization. The profile explicitly declined to infer a gain. [Profiling report][profile]. |
| Low priority for the retained changes | Exhaustive low-level tuning before establishing the dominant cost | Selective kernel profiling informed the remaining backlog, but the accepted changes addressed initialization and dispatch. No kernel-tuning gain was qualified. [Profiling report][profile], [follow-up report][followup]. |
| Low marginal value after replay | Separate narrow reuse experiments without checking overlap | The follow-up CPU profile measured 0.80 s in one conditioning activity and 0.79 s across a repeated tensor-preparation activity. Both were deferred because broader replay could absorb the same costs. [Follow-up report][followup]. |

The failed numerical screens were useful. They cheaply prevented work on invalid
solutions. In contrast, extra precision in an instrumented opportunity estimate
would not have replaced the measured control experiments.

## Work beyond the initial list

- **Runtime qualification and asset provisioning.** The team installed and
  aligned dependencies, provisioned cached assets, qualified the isolated model
  environment, and preserved package freezes.
- **Tests of the measurement system.** The harness was tested for false passes,
  incomplete outputs, hidden randomness, and unsafe recovery.
- **Build and provenance isolation.** Frozen snapshots included untracked
  tooling. Import paths and canonical input paths were checked, as well as Git
  revisions and file hashes.
- **Failure diagnosis and evidence-preserving recovery.** VM restarts, copied
  paths, a comparison interpreter without scientific dependencies, an incomplete
  ESM test environment, and duplicate package metadata were diagnosed separately
  from candidate scientific failures.
- **Random-state and supported-behavior checks.** The work checked later random
  streams, checkpoint restoration, training behavior, and reuse across changed
  inputs, beyond the final saved predictions.
- **Drift controls and memory accounting.** Unchanged stages helped identify
  timing movement. Allocated memory, reserved memory, process RSS, and missing
  worker measurements were distinguished.
- **Publication and handoff.** Machine-readable evidence, plots, archived
  reports, browser checks, patch files, and explicit completion state made the
  result reviewable by someone continuing the work.

These additions are documented in the [suite guide][suite-guide],
[progress log][lessons], and [completion audit][followup-completion].

## Re-run checklist for another VM

The records support repeating the method on another VM. They do not establish
the same timings or exact floating-point behavior on different hardware. Create
both comparison builds on the new machine and capture a new local reference.
Do not bypass the old reference's hardware guard to compare timings across VMs.

- [ ] **Choose the comparison.** Use original upstream versus the final build
  for cumulative savings, or the accepted initialization build versus the
  follow-up for incremental savings. Record the revisions, patch, and source
  hashes. Do not label the current working tree as unmodified upstream.
- [ ] **Preserve the complete experiment bundle.** Include `benchmarks/`, its
  fixtures, relevant tests, profiling and report scripts, docs, exact dependency
  freezes, build manifests, and patches. A clean clone currently omits important
  untracked files. Back up the full reference output directories; small timing
  summaries cannot replace their scientific artifacts.
- [ ] **Provision and qualify the runtime.** Follow the [suite guide][suite-guide],
  [dependency guidance](dependencies.md), and [ESM setup](esmfold2.md). Record
  hardware identity, driver, interpreters, and actual package inventories.
  Resolve environment incompatibilities before freezing the comparison pair.
- [ ] **Provision assets outside timing.** Download models and molecule data,
  populate a local asset manifest, and verify hashes and pinned snapshots.
  Check the ESM test fixture configuration so a missing asset cannot turn
  required coverage into a skip. Confirm that timed runs can operate offline.
- [ ] **Freeze inputs and verify imports.** Prepare the manifest and input lock.
  Keep canonical fixture locations shared between build snapshots. Verify the
  application and isolated-worker source selected by each interpreter. Avoid
  copied paths or extra search paths that silently change provenance or metadata.
- [ ] **Check the new machine.** Require an idle GPU, serial jobs, a documented
  clock/power policy, and adequate persistent storage. Apply the same policy to
  both builds. Keep telemetry and run order with the records.
- [ ] **Run contract tests and an unchanged-build screen.** Validate the harness,
  project contracts, and separate model integration. Inspect actual counts,
  skips, output comparisons, and exit codes before a long capture.
- [ ] **Capture a full local reference.** Use fresh processes and output paths,
  the recorded workload, an excluded warmup, and repeated measurements. Confirm
  unchanged-build repeatability before evaluating the candidate.
- [ ] **Screen, alternate, then qualify.** Run focused candidate checks and
  representative stage replays. Alternate build order for timing controls.
  Finish with an integrated candidate check against the new local capture.
  Retain every valid sample and inspect every stage gate.
- [ ] **Check historical outputs where compatible.** Preserve their identity
  and exact comparison rules. If another machine cannot reproduce them, record
  the limitation and investigate it; a local matched timing pair does not prove
  historical numerical equivalence. Do not widen tolerances to rescue a patch.
- [ ] **Handle interruption explicitly.** Recovery is supported only for an
  eligible interrupted or failed capture with matching identities. Quality
  mismatches cannot be resumed. Candidate checks need a fresh output directory.
  A GPU or workload change needs a new capture. A persistent terminal survives
  a disconnected session, not a VM reboot.
- [ ] **Generate and audit the result.** Recompute tables and figures from raw
  records, retain quality and performance failures, state timing exclusions,
  report memory, and verify that source hashes still identify the tested build.

The basic commands below are templates for the new VM. Run them from verified
build roots, substitute local absolute paths, and use new output directories.
They are not evidence that these commands have been run for this document.

```bash
python3 scripts/run_regression_suite.py prepare \
  --suite full --profile pipeline --output /absolute/path/new-prepared-inputs

/absolute/path/boltz-runtime/bin/python scripts/run_regression_suite.py doctor \
  --python /absolute/path/boltz-runtime/bin/python \
  --output /absolute/path/new-readiness.json

# From the frozen reference build:
/absolute/path/boltz-runtime/bin/python scripts/run_regression_suite.py capture \
  --assets /absolute/path/assets.local.json \
  --suite full --profile pipeline --seed 20261007 \
  --numerics deterministic --atol 0 --rtol 0 --warmups 1 --repeats 5 \
  --output /absolute/path/new-reference

# From the frozen candidate build:
/absolute/path/boltz-runtime/bin/python scripts/run_regression_suite.py check \
  --assets /absolute/path/assets.local.json \
  --baseline /absolute/path/new-reference --max-regression 0.05 \
  --output /absolute/path/new-candidate
```

`check` inherits its cases and settings from the capture. Stage replay must
select stages present in every inherited case. Create an appropriate subset
capture when necessary. A stage replay tests fixed upstream inputs and does not
replace integrated qualification. A report marked `complete` can still contain
a failed performance gate; inspect the verdict and process exit status.

Campaign helpers are examples of orchestration, not portable one-command
installers. Several embed historical campaign paths, build labels, or asset
locations. Adapt those paths deliberately while preserving the scientific
harness. See the [follow-up handoff][followup-plan] for the known assumptions.

## What to do differently next time

| Change to the process | Evidence behind it |
| --- | --- |
| Package and version the experiment infrastructure before long runs | Essential untracked scripts and fixtures make the current clean clone insufficient. Frozen snapshots prevented loss, but do not replace a portable bundle. |
| Run a full preflight through both interpreters and a canonical-path screen | Copied inputs broke provenance; system Python could not decode results; a missing ESM fixture produced an incomplete test run; an extra import path changed package inventory. These were avoidable setup failures. [Progress log][lessons]. |
| Plan alternating controls before candidate timing | The initialization campaign added them after full runs exposed drift. The follow-up used them earlier and included unchanged stages. [Campaign reports][initializer], [follow-up report][followup]. |
| Set the noise policy and reference-selection rule in advance | Unchanged upstream failed historical gates. Document how to obtain fresh controls and when more repetitions are needed, while keeping historical failures visible. |
| State user-latency and memory acceptance criteria before choosing a mechanism | Configuration is excluded from current totals, and reserved memory increased. The benchmark should explicitly match the intended user operation and deployment capacity. [Overview][overview]. |
| Keep the decision ledger compact and authoritative | Plans, raw ledgers, and progress entries contain earlier pending states. Preserve history, but put the current accepted build, completed checks, rejected ideas, and next action in a clear final record. |

The first priorities are a portable experiment bundle, an end-to-end preflight,
and contemporary alternating controls from the start. These recommendations
follow recorded failures; they are not claims of measured time savings.

## Decisions still open

| Open decision | Evidence needed before deciding |
| --- | --- |
| How to package and integrate the qualified follow-up | Review the local patch and supporting files, decide what to commit, and choose whether to propose an upstream change. The follow-up records no push or upstream PR. |
| Where GPU replay should be enabled on other hardware and workloads | Measure smaller-memory GPUs, larger inputs, and short custom schedules, including setup cost and memory. The qualified campaign used an H100 with 80 GB. |
| Whether literal single-invocation latency needs a separate primary benchmark | Include configuration and validation costs if future work targets them. Keep the present stage-total series for continuity. |
| Whether residency or throughput should be a new objective | Use a separate session workload with first-request and steady-state costs, mixed inputs, memory retention, and scientific checks. The current fresh-process suite cannot answer it. |
| Which remaining optimization to try next | Reprofile the accepted combined build before choosing among preparation reuse, setup, reporting, larger-workload computation, or compilation. Their old opportunity estimates may overlap accepted gains. |
| How much broader coverage is needed | Add production-size design sets, supported concurrency, and separate worker-memory measurements. Current small design sets and serial execution do not establish production scaling. |

Neither campaign exhausted the optimization backlog. There is no recorded
qualification of the final combined build on another VM, a statistically
conclusive small-gain study, or a production-scale throughput benchmark. Those
remain separate work with their own workload and acceptance decisions.

## Evidence locations

| Material | Location |
| --- | --- |
| Workload, quality, timing, setup, and recovery instructions | [Regression suite][suite-guide] |
| Profiling scope, optimization plan, and follow-up handoff | [Profiling plan][profile-plan], [optimization plan][optimization-plan], [follow-up plan][followup-plan] |
| Decisions, failures, progress, and final outcomes | [Optimization learnings][lessons] |
| Harness and its tests | [Harness](../benchmarks/), [runner](../scripts/run_regression_suite.py), [harness tests](../tests/test_benchmark_suite.py) |
| Historical baseline | [Human report][baseline-report], [compact record][baseline-json], [full local report][historical] |
| Profiling | [Report][profile], [runner](../scripts/profile_pipeline.py), [audit](../scripts/audit_profiling.py), `results/profiling/` |
| Initialization campaign | [Report][initializer], [ledger][initializer-ledger], [full comparison](../results/optimization/h100-20261009-2055/comparison.json) |
| Follow-up campaign | [Report][followup], [ledger][followup-ledger], [comparison][comparison], [patch][followup-patch], [completion][followup-completion] |
| Reporting and publication | [Report generator][report-tool], [publisher](../scripts/publish_optimization_followup.py), [browser inspection](../scripts/inspect_optimization_page.py), [figures](benchmarks/figures/) |
| Cumulative comparison and memory tradeoff | [Performance overview][overview] |

Links into `results/` refer to retained local evidence. Those artifacts are
ignored by Git and must travel with an archived experiment if the links are to
remain usable elsewhere.

[overview]: benchmarks/boltzgen-performance-overview.md
[followup]: benchmarks/boltzgen-optimization-followup-20261011.md
[initializer]: benchmarks/boltzgen-optimization-20261010.md
[profile]: benchmarks/boltzgen-profiling-20261009.md
[profile-json]: benchmarks/boltzgen-profiling-20261009.json
[cpu-json]: benchmarks/boltzgen-profiling-cpu-20261009.json
[baseline-report]: benchmarks/h100-pipeline-20261009.md
[baseline-json]: benchmarks/h100-pipeline-20261009.json
[esm-performance]: esmfold2-performance.md
[suite-guide]: regression-suite.md
[profile-plan]: profiling-agent-prompt.md
[optimization-plan]: optimization-agent-prompt.md
[followup-plan]: optimization-followup-agent-prompt.md
[lessons]: optimization-learnings.md
[cases]: ../benchmarks/cases.json
[prepared-plan]: ../benchmarks/prepared/plan.json
[input-lock]: ../benchmarks/prepared/inputs.lock.json
[comparator]: ../benchmarks/compare.py
[historical]: ../results/baseline-h100-full-20261009-95f45d1d/report.json
[initializer-ledger]: ../results/optimization/h100-20261009-2055/experiments.jsonl
[initializer-bracket]: ../results/optimization/h100-20261009-2055/bracket-folding.json
[initializer-completion]: ../results/optimization/h100-20261009-2055/qualification-completion.json
[algebraic-screen]: ../results/optimization/h100-20261009-2055/algebraic-transform-screen.json
[followup-ledger]: ../results/optimization/h100-followup-20261010-1837/experiments.jsonl
[followup-bracket]: ../results/optimization/h100-followup-20261010-1837/bracket.json
[followup-patch]: ../results/optimization/h100-followup-20261010-1837/new-candidate.patch
[followup-completion]: ../results/optimization/h100-followup-20261010-1837/qualification-completion.json
[mechanism]: ../results/optimization/h100-followup-20261010-1837/graph-mechanism.json
[comparison]: ../results/optimization/h100-followup-20261010-1837/comparison.json
[report-tool]: ../scripts/report_optimization_followup.py
