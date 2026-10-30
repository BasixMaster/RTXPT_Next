# Local experiment history and data retention

## Current preservation policy

**Completed cleanup:** 4,826 files, 18.59 GiB of logical file data removed (16.17 GiB on C: and 2.43 GiB on D:). The full latest 18-sequence B10 dataset, references and two additional older sequences are retained. Six cleanup safety tests and 8,306 retention/deletion checks passed.

On 2026-10-30 the user requested removal of redundant local simulation data, including captures under Documents, while preserving lessons and the ability to reproduce older experiments. This cleanup applies to Basix Pathtracing workbench data. Other projects found in Documents are outside its deletion scope.

The repository's published benchmark evidence, selected raw HDR, plots, comparison pictures, source history, scene assets and benchmark tools remain intact. Local reference images, frozen source/runtime controls, diagnostic reservoir/state payloads, timing traces, settings, logs and failed-attempt records are retained. The complete latest B10 duplication dataset, including all three seeds, remains available for future temporal analysis.

Historical frame sequences selected for pruning retain four chronological checkpoints: first, quarter, halfway and last. The interior PFM/PNG frames can be rerendered from the preserved configuration; they are no longer a complete local sequence after pruning. Per-frame metadata, previously calculated metrics and original hashes remain evidence of the original acquisition. A new metric requiring every original pixel or frame needs a fresh acquisition; the retained checkpoints cannot substitute for it.

The machine-readable [cleanup history](../../Benchmarks/development/2026-10-30-local-retention/summary.json) records the actual completed deletion scope, counts and limitations. Its compressed file ledger records each removed file's original hash and size. Private host paths, telemetry and complete command archives stay in the local workbench history.

Two older sequences without a matching frozen executable were excluded from pruning and remain complete. Of the 34 affected capture folders, 30 have a recorded executable hash matched to a retained binary. Three excluded startup-diagnostic runs have command-only metadata without that historical hash; one incomplete C-volume capture has invalid original metadata. These gaps remain explicit rather than being filled from the current executable.

## Experiment history and lessons learned

| Stage | Persistent finding | Evidence and reproduction entry point |
|---|---|---|
| RTXPT 1.9 and runtime migration | B0 preserves original defaults and pins. A raw native-only override is a different configuration. Earlier migration/control labels must not be treated as canonical DI-on results. | [Version mapping](VERSION_MAPPING.md), [native matrix](NATIVE_MATRIX_RESULTS.md), [native DI controls](CANONICAL_NATIVE_DI_RESULTS.md). |
| ReSTIR PT foundation | The scoped opaque checkpoint does not establish broader material, medium or diffuse-budget support. | [PT implementation](B2_IMPLEMENTATION.md), [extended scenes](PT_EXTENDED_SCENES.md), source and scene identities in each capture. |
| Rejected-shift correction | A zero-Jacobian rejected shift must return a finite zero target; NaN multiplied by zero can otherwise erase valid contributions in inverse MIS. | [Finite shift guard](FINITE_SHIFT_GUARD.md), retained before/after diagnostic records and selected raw HDR. |
| Brightness investigations | Material precision, DI reuse and prefix-throughput probes are separate ablations. Do not fit exposure to hide a transport error or infer a universal brightness fix. | [Material precision](GBUFFER_PRECISION.md), [DI isolation](DI_REUSE_ISOLATION.md), [prefix probe](PREFIX_THROUGHPUT.md). Brightness fixes remain user-deferred. |
| B8 GI integration | Short-GI/long-PT ownership is explicit. NVIDIA non-directional GI reuse is an approximation with support restrictions, not unrestricted full directional integration. | [Partition design](B8_PARTITION_DESIGN.md), [staged implementation](B8_STAGED_IMPLEMENTATION.md). |
| B9 limited PT++ | Room enables footprint reconnection and initial-only roulette. Original Convergence/Kitchen retain full-prefix replay and use a roulette-only ablation. Replay must not draw roulette. | [B9 results](B9_RESULTS.md), three-seed quality and separate uncapped timing. |
| Paired spatial reuse | Reciprocity, ownership and sharing need exact checks. A supplied mechanism or successful compilation does not prove active, correct use. | [Paired pilot](B10_PAIRED_PILOT.md), [Gaussian pairing](B10_GAUSSIAN_PAIRING.md), [queue history](B10_QUEUE_HISTORY.md). |
| B10 duplication reduction | The completed three-scene ablation has averaged-image MSE improvements in the original scenes, but individual-frame/perceptual tradeoffs and no general speedup. The reduction is deliberately biased and opt-in. | [Duplication report](B10_DUPLICATION_HISTORY.md); complete latest sequences retained locally; public metrics, curves, selected HDR and timing evidence retained. |
| Full B10 target | PT++ §6.1 gives one PT reservoir direct and all indirect paths. Keeping short GI separately is a labelled adaptation. Exact finite-domain MIS/PSS tests are prerequisites, not renderer activation. | [Unified-lighting derivation and oracle](B10_UNIFIED_LIGHTING.md). B10 remains partial; B11 inactive. |
| Measurement failures | No PresentMon events is missing timing evidence. Diagnostic logging/debugger captures are excluded from performance comparisons. Rare startup failures remain unresolved. | Failed-attempt records, capture/timing eligibility and restoration receipts in the owning evidence directories. |

## Reproduce an older experiment

1. Identify the exact result row and its original dataset ID in the [comparison overview](COMPARISON_OVERVIEW.md). Use the [version mapping](VERSION_MAPPING.md) before interpreting historical B labels.
2. Read the corresponding evidence manifest and local reproduction index. Preserve the source commit, submodule/asset pins, shader inputs, executable hash, scene/camera/material identities, transport flags, seed, frame chronology and quality-reference hashes. Local history is under `work/retention-2026-10-30` in the owning chat workbench.
3. Use a retained frozen runtime matching the recorded executable hash, or build the recorded source in an isolated checkout. The current executable can differ. An archived command that names the main executable does not authorize replacing that executable or imply that its current bytes match the historical run.
4. Adapt only output destinations to a new directory. The local reproduction index preserves the original argument vector and working directory as data, plus matching frozen-runtime locations where available. Do not execute archived scripts that patch current source or restore old state blindly.
5. For sequence acquisition, use the maintained `Benchmarks/tools/run_capture.py` wrapper with the recorded options. The B8/B9/B10 sequence runners and evaluators preserve their acquisition/analysis protocol. Respect required scene guards, warm-up, seeds, fixed references and official FLIP policy; check the historical wrapper's source at the recorded commit if interfaces changed.
6. Acquire quality separately from no-image-write timing. Verify effective algorithm flags, frame count and output hashes; record caps, presentation eligibility and driver-state restoration for timing. Preserve failures as failures.
7. Compare fresh measurements statistically. Whole-renderer cross-process bit identity was not established; original hashes identify old evidence, not a guarantee that a new launch reproduces every pixel or timing value exactly.

## Cleanup audit and recovery limits

Before deletion, the local preview inventories resolved paths, original sizes, timestamps and SHA256 hashes. Deletion rejects path escapes, reparse points, modified files and repeat application. It removes individual manifest-listed files without recursively deleting experiment folders. Run metadata is copied and verified first. A receipt records each successful deletion; verification checks the retained main dataset, reference images, checkpoints and original manifests.

The local history includes `inventory.json`, `preview-retention.json`, `reproduction-index.json`, `run-metadata/`, volume-specific deletion receipts, safety-test output and a verification receipt. The inventory also records other projects seen during the Documents scan; their presence does not mark them disposable.

Deleted interior frames are not recoverable from a hash. Reproduction requires rendering again, matching the recorded code, runtime, assets and environment as closely as possible. Frozen binaries and metadata improve reproducibility but do not guarantee identical execution on a changed GPU/driver or renderer state.

## Summary and lessons learned

Keep compact authoritative evidence and executable reproduction inputs; retain full sequences where further temporal analysis is planned. Separate historical results from new acquisitions, and preserve failed attempts and scope limitations. Cleanup changes local data availability, never algorithm acceptance, measured values or the B10–B16 roadmap.
