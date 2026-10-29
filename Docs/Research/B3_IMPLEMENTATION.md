# B7 limited PT++ ablations: retained legacy B3 implementation

> **LEGACY NUMBERING.** The old-B3 footprint/initial-only-roulette implementation described below ran the **B7** partition (DI3.1 + ReSTIR PT, GI off). It is **not canonical B9**, whose B8 foundation includes valid GI sharing. The preserved old-B2 control `de9fe651` maps to B7; old-B4 remaining-work references map to **B10**. [VERSION_MAPPING.md](VERSION_MAPPING.md) is authoritative; source refs, runtime controls, measurements and raw IDs below are unchanged.

B8 sharing requires a valid contribution partition/MIS before B9/B10 can claim it. Packed reservoirs and forced NEE were inherited from runtime3.1; enabling supplied machinery does not establish a full PT++ implementation. Keep original scene coverage visible and prioritize the missing matched canonical B1/B4 native-DI benchmarks.

B3 development starts from the preserved B2 checkpoint `de9fe651903f203327830e7361ac4237e00d508c` on `b3/ptpp-activation`. It retains **RTXPT + ReSTIR DI + ReSTIR PT, with GI off** in the tested configuration. B3 is in progress; it does not mean every PT++ mechanism is implemented or that B2's broader material gates have passed.

## First implementation

| Mechanism | B2 control | B3 implementation and verification boundary |
|---|---|---|
| Footprint and inverse-footprint reconnection | Fixed roughness/distance threshold | Activates the existing RTXDI 3.1 footprint policy through `--ptReconnectionMode 1`. Runtime thresholds retain their pinned defaults. Opaque scene gate remains enforced. |
| Initial-generation Russian roulette | Bridge never invokes roulette | `--ptRouletteProbability 0.8` enables fixed survival probability after the first continuation. Surviving throughput is divided by probability and the initial context records that probability. Draws use the initial RNG; hybrid-shift replay never invokes roulette. Supported values are 0 (disabled) or [0.1,1]; value 1 is a no-op. Smaller nonzero probabilities are rejected to bound reciprocal scaling. |
| History identity | Fixed-threshold settings and schedule | A changed policy, footprint parameter or roulette probability resets PT history. CLI receipts report actual first-frame settings. |
| Activation diagnostics | Reservoir census | Diagnostic-only GPU counters record roulette tests, termination, survival and any replay roulette. They are disabled in throughput runs. |
| History-length sweep | Default 64-frame warm-up | `--captureWarmupFrames` / wrapper `--history-frames` selects 1–4096 simple-capture warm-up frames with an effective receipt. These are history-settling samples, not accumulated spp. |

The first GPU smoke capture recorded 166,511 roulette tests, 33,381 terminations, 133,130 survivals and zero replay roulette tests. That verifies execution in this capture, not unbiasedness or a performance improvement. The initial image had finite raw HDR. The separately retained smoke build precedes the final history-sweep GUI build and is not substituted for its artifact identity.

## Predetermined ablations

Use one executable for four settings: fixed/no roulette (B2-policy control), footprint only, roulette only at survival 0.8, and both. A same-executable B2-policy control isolates settings but is not renamed to the immutable B2 executable. Keep the frozen B2 data separately identified.

The first controlled-scene pilot uses seeds 0, 11 and 47, initial-only and temporal-plus-spatial reuse, and history warm-up lengths 1, 8, 32 and 64. Native finite 8192spp reference, pixel-center convention and fixed HDR-FLIP exposure parameters remain those of the B2 checkpoint. No candidate brightness normalization or favorable-seed selection is allowed. Three seeds/process repetitions are exploratory.

Quality is measured outside throughput runs. Timing runs use application uncapped controls, scoped NVIDIA cap/VSync settings with restoration, and read-only RTSS boundary audits. Include the added dispatch/binding cost and retain artifact/cache failures rather than relaxing the oracle. A history-settling curve is not a time-to-equal-quality result.

## Mandatory extended scene coverage

| Original case | Matched contract | B2/B3 status |
|---|---|---|
| Convergence (`convergence-test.scene.json`) | Original materials/camera, 1280×720, exposure 0, 14 total / 2 diffuse bounces | Unsupported: transmission materials and binding diffuse budget. No B2/B3 timing or quality result. |
| Kitchen (`kitchen-with-test-stuff.scene.json`) | Original materials/camera, 1280×720, exposure 2, 14 total / 2 diffuse bounces | Unsupported: glass/transmission/BLEND materials and binding diffuse budget. No B2/B3 timing or quality result. |
| Owned opaque room | 640×360, exposure 0, 3/3 bounces, DI + PT, GI off | Controlled B3 activation pilot; cannot replace either original-scene gate. |

See [algorithm variants and comparison policy](ALGORITHM_VARIANTS.md). Every later comparison keeps all three rows visible, including unsupported cases. The historical B0/B1 DI+GI scene results have unverified external cap coverage and cannot be pooled with cap-verified throughput runs.

## Remaining PT++ work assigned to B4

| Technique | Current status / next gate |
|---|---|
| 64-byte packed reservoirs and forced NEE reconnection | Inherited by B2; not counted as new B3 work. |
| Duplication-based history reduction | Pending real sample-ID/map producer, lifecycle and barriers. Deliberately biased; keep outside strict radiometric preset. |
| Reciprocal spatial pairing | Pending pair ownership and shared forward/inverse shift implementation and validation. |
| Unified direct + indirect PT reservoir | Pending primary NEE candidate integration and a new contribution partition; current DI + PT remains separate. |
| Explicit replay stream compaction | Pending work queues, bounded overflow handling, synchronization and complete-cost measurement. |
| All-candidate vector-weight shading | Pending estimator derivation/integration and independent numerical oracle; RGB target storage alone is insufficient. |
| Dual-motion-vector disocclusion recovery | Pending relative surface/occluder motion construction and temporal tests. Ordinary motion or zero-motion fallback is not this technique. |
| CGNS | Separate paper; pending real prepass activation and validation. Do not label it reciprocal pairing. |
| All paper micro-optimizations / SER | No equivalence claim. Profile and validate isolated changes before activation. |

Source audit and paper locators: [PT++ audit](PTPP_AUDIT.md). No runtime submodule modification or imported unlicensed implementation is required by these first two activations.

The user assigned the remaining techniques to **B4**, starting after this B3 checkpoint. B3 retains the two isolated activations above; it is not renamed to a complete PT++ implementation. See [B4 implementation plan](B4_IMPLEMENTATION.md).

## Summary and lessons learned

Separate inherited code, application wiring and measured activation. B3 now exposes footprint and initial-only roulette as independent experimental controls, while preserving the B2 policy and scene gates. The decisive next evidence is matched raw-HDR quality, history settling and repeated uncapped cost; the original-scene material/diffuse-limit gap remains a prerequisite for a broad comparison or promotion.

## Changes

- 2026-10-28: Started B3 activation work, GPU execution counters and explicit extended-comparison coverage.
