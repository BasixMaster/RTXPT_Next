# Wyman recent-paper breadth review

Ranks 6, 8, 9, 11–20 in the Wyman conference/journal list, checked 2026-10-28; seven focus papers are covered separately. Current project labels follow [canonical B0–B10](VERSION_MAPPING.md): B0 is unchanged RTXPT1.9 defaults/pins; legacy migration7010bb4 is not canonical B1. Historical native DI+GI runtime3.0/3.1 observations map to B2/B5, with cap coverage unverified. The app-owned PT foundation is B6/B7; B8 sharing and B9/B10 features require their own validation. Priorities below remain research proposals, separate from the [retained migration measurements](B1_RESULTS.md) and later scoped PT pilots.

Many cwyman PDFs exceed web extraction size limits. Full-text access is marked only for publisher HTML read; indexed excerpts/abstracts are labelled. No paper-algorithm reproduction was run in this breadth review.

## 6. Gradient-Domain ReSTIR Path Tracing (2026)

[Paper](https://cwyman.org/papers/eg26_Gradient_ReSTIR.pdf) · [Inspected primary source](https://onlinelibrary.wiley.com/doi/10.1111/cgf.70328)

**Reading:** Publisher full-text HTML: Sections 4–6; direct PDF exceeded web size limit. **Locators:** Sections 4.1–4.4, 5 Results, 6 Discussion and Conclusion; Figures 9–12

**Mechanism:** Resample paired-pixel paths directly in gradient space, with adaptive edge-aligned spatial reuse and positive/negative reservoirs to reduce sign noise; reconstruct using a separate primal Area ReSTIR image.

**Evidence context:** Falcor, RTX 5090, Ryzen 5900X, 1920×1080 moving camera. L2 Poisson reconstruction costs 11 ms; L1 costs 300 ms. L2 cost is included in equal-time comparisons.

**Limits:** Assumes affine object transforms. High-frequency temporal turbulence remains without temporal gradients; reconstruction is an additional cost. Neural reconstruction efficiency is prospective, not demonstrated as a DLSS integration.

**Integration proposal:** RTXPT research branch: separate gradient reservoirs, primal pass and reconstruction interface. RTXDI core can supply path shifts but cannot obtain this by merely changing a spatial-neighbor picker.

**Priority: defer.** Promising detail preservation, but a separate estimator/reconstruction architecture follows the seven requested sampling priorities.

**Validation proposal:** Compare paired-pixel reuse against gradient-after-ReSTIR at equal complete frame time; measure signed-gradient error, reconstructed error, deformation failures and temporal instability.

[Author implementation/reference](https://github.com/elite-sheep/gradient-restir). Implementation existence is verified from an author page or repository; exact revision/license is not audited here and must be checked before copying.

## 8. Reservoir Splatting for Temporal Path Resampling and Motion Blur (2025)

[Paper](https://cwyman.org/papers/sig25_ReSTIR_Splatting.pdf) · [Inspected primary source](https://research.nvidia.com/labs/rtr/publication/liu2025splatting/)

**Reading:** Author abstract, official repository README and indexed supplemental Section 1–3 excerpt; large main PDF could not be opened. **Locators:** Abstract; supplemental Sections 1–3; repository Temporal Resampling Options

**Mechanism:** Forward-project exact prior-frame primary hits rather than only backprojecting current pixels. Combine splats and backup gather samples using MIS. Multiple time splats extend reuse to motion blur; depth of field is also supported.

**Evidence context:** Author abstract reports better resampling quality than Area ReSTIR at up to 10% lower cost; this is not a measured RTXDI_Next result.

**Limits:** Forward scatter requires deterministic handling of collisions and uncovered pixels; multi-splat partitions raise storage. Repository describes a Falcor 8 prototype, not an RTXDI API port.

**Integration proposal:** RTXPT temporal candidate-production pass plus RTXDI PT-compatible sample/weight import. Foundational dependency for the 2026 multi-layer splatting branch.

**Priority: high.** Establish a single-layer splat plus backup baseline before adding hidden-surface layers.

**Validation proposal:** Separate gather-only, scatter-only and scatter-plus-backup; test subpixel moving geometry, lens aperture, camera cuts, splat overflow, shutter support and unbiased mean.

[Author implementation/reference](https://github.com/Jebbly/Reservoir-Splatting). Implementation existence is verified from an author page or repository; exact revision/license is not audited here and must be checked before copying.

## 9. Unbiased Differential Visibility Using Fixed-Step Walk-on-Spherical-Caps And Closest Silhouettes (2025)

[Paper](https://cwyman.org/papers/sig25_differential_visibility.pdf) · [Inspected primary source](https://research.nvidia.com/labs/rtr/publication/wu2025unbiased/)

**Reading:** Author abstract and indexed first-page PDF abstract/Figure 1; full PDF size blocked web extraction. **Locators:** Abstract and Figure 1

**Mechanism:** Construct a velocity field for warped-area differential visibility using fixed-step walks on spherical caps and cone queries for closest silhouettes.

**Evidence context:** A differentiable-rendering visibility derivative estimator, not a primal-lighting or temporal-reuse result.

**Limits:** The fixed-step field is continuous but need not be harmonic. Requires silhouette-oriented geometric queries; existing primal ray tracing alone is insufficient.

**Integration proposal:** An optional differentiable/inverse-rendering RTXPT extension; no direct replacement for RTXDI visibility tests.

**Priority: defer.** The current goal is forward rendering quality/performance, so derivative estimation has no immediate acceptance target.

**Validation proposal:** If adopted later, compare geometry derivatives to finite differences and test silhouette discontinuities, not just rendered color.

## 11. Many-Light Rendering Using ReSTIR-Sampled Shadow Maps (2025)

[Paper](https://cwyman.org/papers/eg25_ReSTIR_for_ShadowMaps.pdf) · [Inspected primary source](https://doi.org/10.1111/cgf.70059)

**Reading:** Publisher full-text Section 3, plus author abstract; direct PDF too large. **Locators:** Sections 3.1 Selecting Lights, 3.2 Practical Algorithm, 3.3 Maintaining Temporal Stability

**Mechanism:** Use a ranking reservoir process to select a budgeted subset of full-resolution light shadow maps, with imperfect shadow maps elsewhere; a separate shading reservoir process evaluates lighting. Variance-based hysteresis stabilizes upgrades and downgrades.

**Evidence context:** Targets rasterized many-light shadow-map computation/storage.

**Limits:** Two reservoirs prevent ranking/shading feedback flicker; combining them degrades stability or noise. Imperfect maps approximate visibility, so this is not exact ray-traced visibility.

**Integration proposal:** A separate low-end/raster RTXDI sample backend, or an importance-ranking experiment. Not a baseline visibility replacement for RTXPT.

**Priority: defer.** Avoid mixing visibility approximation into evaluation of unbiased PT resampling improvements.

**Validation proposal:** If adopted, measure map generation cost, memory, ranking flicker, approximation error and temporal response separately from reservoir estimator error.

## 12. Area ReSTIR: Resampling for Real-time Defocus and Antialiasing (2024)

[Paper](https://cwyman.org/papers/sig24_areaReSTIR.pdf) · [Inspected primary source](https://graphics.cs.utah.edu/research/projects/area-restir/)

**Reading:** Author project abstract and indexed paper Sections 4.1–4.6 excerpts; complete large PDF unavailable in web extraction. **Locators:** Sections 4.1 Area Reservoirs, 4.3 Temporal Reuse, 4.4 General Pixel Filters, 4.6 Depth of Field

**Mechanism:** Include film and lens coordinates in the reservoir domain. Fractional-pixel temporal tracking and camera-aware shifts improve reuse of subpixel detail and defocus. The robust option can borrow shifted samples from four overlapping prior reservoirs.

**Evidence context:** Supports antialiasing and depth of field; basis for later splatting and gradient-domain work.

**Limits:** Aperture support and shift Jacobians matter; primary-hit reconnection can leave the aperture. General filters alter overlap/MIS weights. The author repository publishes only the DI implementation, modifies scene-history storage outside its module, and warns module-only copying produces bias/errors; noisy camera-domain G-buffers challenge denoisers.

**Integration proposal:** Extend RTXPT camera/sample domain and RTXDI PT history metadata before camera effects or splatting. Audit what current RTXDI already implements first.

**Priority: high.** Use as domain-correctness reference and comparison baseline for the requested 2026 temporal techniques.

**Validation proposal:** Pinhole and large aperture, subpixel wires/fur, fractional motion, box/non-box pixel filters, aperture-boundary failure, long-run mean.

[Author implementation/reference](https://github.com/guiqi134/Area-ReSTIR). Implementation existence is verified from an author page or repository; exact revision/license is not audited here and must be checked before copying.

## 13. Decorrelating ReSTIR Samplers via MCMC Mutations (2024)

[Paper](https://cwyman.org/papers/tog24_ReSTIRMutations.pdf) · [Inspected primary source](https://doi.org/10.1145/3629166)

**Reading:** Publisher full-text method Section 3 and limitations Section 7; indexed paper excerpts. **Locators:** Section 3 Method, Equation 16, Algorithm 3, Section 7 Limitations; Figures 12–13

**Mechanism:** Mutate selected reservoir samples using Metropolis–Hastings, usually after temporal reuse; update the contribution weight by the old/new target-function ratio before further resampling.

**Evidence context:** Demonstrated in DI and PT; mutations address correlation and duplicate-sample impoverishment.

**Limits:** Non-negligible runtime; can improve perceptual correlation without lowering MSE. It is not a discovery mechanism for missing important transport, and even unlimited mutations need not remove all correlations.

**Integration proposal:** Optional RTXDI DI/PT decorrelation stage, especially when long temporal history is valuable. Compare to compatible-neighbor selection rather than assuming gains add.

**Priority: medium.** Revisit if improved neighbors and PT++ still leave visible boiling/blotches.

**Validation proposal:** Measure covariance/FLIP and denoised sequences alongside MSE, complete frame cost and target-ratio boundary handling.

## 14. Conditional Resampled Importance Sampling and ReSTIR (2023)

[Paper](https://cwyman.org/papers/siga23_CRIS.pdf) · [Inspected primary source](https://wrap.warwick.ac.uk/id/eprint/180947/)

**Reading:** Author-affiliated archival abstract, indexed first-page paper excerpt, official prototype README. **Locators:** Abstract and Figure 1; official prototype Introduction

**Mechanism:** Extend GRIS to conditional domains with correct joint contribution weights; a final gather reuses path suffixes after one or more unreused prefix bounces.

**Evidence context:** A proof-of-concept with reduced blotchy correlation and improved denoiser behavior; prototype is explicitly unoptimized.

**Limits:** Conditional independence and contribution-weight requirements must be preserved. Suffix reuse cannot silently inherit full-path reservoir weights.

**Integration proposal:** Theoretical reference for RTXPT suffix-guiding/conditional reuse and PG interactions; not needed to add all seven focus methods to DI.

**Priority: medium.** Use when choosing between full-path reuse and a final-gather architecture.

**Validation proposal:** Compare full-path and suffix reuse, denoised correlation, unbiased mean and extra rays at equal time.

[Author implementation/reference](https://github.com/NVlabs/conditional-restir-prototype). Implementation existence is verified from an author page or repository; exact revision/license is not audited here and must be checked before copying.

## 15. Amortizing Samples in Physics-Based Inverse Rendering Using ReSTIR (2023)

[Paper](https://cwyman.org/papers/siga23_inverseRenderingReSTIR.pdf) · [Inspected primary source](https://projects.shuangz.com/psdr-restir-sa23/)

**Reading:** Author project results and indexed paper multi-view Algorithm 8/computational-overhead excerpt. **Locators:** Project results; paper multi-view estimator and Computational overhead discussion

**Mechanism:** Reuse sampling work across inverse-rendering optimization iterations/views, including gradient estimates and preserved occluded reservoirs.

**Evidence context:** Project reports up to 100× lower gradient relative error and up to 20× lower reconstruction error in its inverse-rendering comparisons, not forward rendering FPS.

**Limits:** A practical geometry-optimization variant checks visibility only in current geometry and introduces bias; learning rate limits its effect.

**Integration proposal:** Future material/shape fitting tool around RTXPT, not the forward-rendering fork core.

**Priority: defer.** Different workload and validation objective.

**Validation proposal:** If adopted, compare optimization error versus complete wall time and geometry-change bias.

## 16. Generalized Resampled Importance Sampling: Foundations of ReSTIR (2022)

[Paper](https://cwyman.org/papers/sig22_foundationsOfReSTIR.pdf) · [Inspected primary source](https://graphics.cs.utah.edu/research/projects/gris/sig22_GRIS.pdf)

**Reading:** Indexed primary PDF abstract/introduction and Sections 3.2, 4.1–4.2; supplement contents, not complete proof review. **Locators:** Sections 3.2 and 4, Equation 4 partition of unity and Equation 8 unbiased contribution weights; supplement S.1–S.5

**Mechanism:** Formalize resampling of correlated samples with tractable unbiased contribution weights and domain-changing shift maps/Jacobians; under conditions derive convergence and variance guarantees.

**Evidence context:** Establishes the ReSTIR PT framework and its distinction from classical independent-sample RIS.

**Limits:** Correlation alone does not grant convergence. Correct support, resampling MIS partition and mapping weights are obligations; an arbitrary heuristic can converge to a wrong answer.

**Integration proposal:** Mandatory estimator contract for every RTXDI PT extension and shared reservoir schema.

**Priority: high.** Correctness prerequisite to combining neighbor selection, stochastic MIS, LoD and PG.

**Validation proposal:** Use analytic tiny scenes, independent repetitions, canonical candidates, inverse shifts/Jacobians and partition-of-unity checks.

## 17. Fast Volume Rendering with Spatiotemporal Reservoir Resampling (2021)

[Paper](https://cwyman.org/papers/siga21_volumeReSTIR_small.pdf) · [Inspected primary source](https://doi.org/10.1145/3478513.3480499)

**Reading:** Publisher abstract and indexed author-paper first page; PDF open timed out. **Locators:** Abstract and Figure 1

**Mechanism:** Extend reuse to volumetric path space, using cheap approximate scattering/transmittance during candidate selection and unbiased final evaluation.

**Evidence context:** Handles dynamic illumination, volumetric emission and multiple scattering; the approximation in selection need not bias final shading if weighting is correct.

**Limits:** Medium path domains and transmittance estimators differ from surface PT. Figure examples are interactive volumetric results, not a 60 Hz guarantee.

**Integration proposal:** Separate RTXPT participating-media extension; RTXDI surface reservoirs cannot be assumed compatible.

**Priority: defer.** Establish robust surface baseline first; medium support has its own path-state contract.

**Validation proposal:** Homogeneous analytic transmittance, heterogeneous media, zero-density transitions, multiple scattering, mean and memory.

## 18. Rearchitecting Spatiotemporal Resampling for Production (2021)

[Paper](https://cwyman.org/papers/hpg21_rearchitectingReSTIR.pdf) · [Inspected primary source](https://diglib.eg.org/items/97358bf2-da67-4df4-8355-b0495f873208)

**Reading:** Publisher abstract and indexed primary paper Figure 2 / Sections 5–7 overview. **Locators:** Abstract; Figure 2; Sections 5, 6.1–6.3 and 7

**Mechanism:** Rework candidate presampling and memory coherence, ray budgets, synchronization, spatial-neighbor choices and separation of shading from reuse for production.

**Evidence context:** Author abstract reports up to 7× lower lighting cost over the earlier research implementation.

**Limits:** These are historical changes underlying productization, not fresh gains to add on top of current RTXDI. GPU timing must include all new passes and synchronization.

**Integration proposal:** Mandatory design/performance reference for the fork and integration with RTXPT dispatch scheduling.

**Priority: high.** Audit already-shipped work before porting research pseudocode or increasing reservoir traffic.

**Validation proposal:** Profile occupancy, cache/memory transactions, rays, barriers and full-frame time against the pinned upstream baseline.

## 19. Glossy Probe Reprojection for Interactive Global Illumination (2020)

[Paper](https://cwyman.org/papers/siga20_glossyProbeReprojection.pdf) · [Inspected primary source](https://www-sop.inria.fr/reves/Basilic/2020/RLPWSD20/)

**Reading:** Author project abstract and indexed primary first-page method overview. **Locators:** Abstract and Figure 1

**Mechanism:** Precompute directional glossy light probes with adaptive parameterization; gather using path perturbation and split roughness convolution between precomputation and runtime filtering.

**Evidence context:** Interactive walkthroughs for static scenes with opaque objects; diffuse light maps complement glossy probes.

**Limits:** Baked scene assumptions and probe storage/reprojection limits do not match general dynamic path tracing.

**Integration proposal:** Alternative cached-lighting branch or scene-class baseline around RTXPT, not a ReSTIR reservoir feature.

**Priority: defer.** Different architecture and static-scene tradeoff; prioritize dynamic unbiased sampling.

**Validation proposal:** If explored, measure bake time/storage, parallax/occlusion error and stale probes after edits.

[Author implementation/reference](https://gitlab.inria.fr/sibr/projects/glossy-probes/synthetic_ibr). Implementation existence is verified from an author page or repository; exact revision/license is not audited here and must be checked before copying.

## 20. Spatiotemporal Reservoir Resampling for Real-time Ray Tracing with Dynamic Direct Lighting (2020)

[Paper](https://cwyman.org/papers/sig20_ReSTIR.pdf) · [Inspected primary source](https://research.nvidia.com/publication/2020-07_spatiotemporal-reservoir-resampling-real-time-ray-tracing-dynamic-direct)

**Reading:** Author abstract and indexed primary paper Sections 5–6 evaluation/temporal weighting excerpt. **Locators:** Abstract; Sections 5–6 reservoir storage, temporal weighting and results

**Mechanism:** Select weighted reservoir light samples and reuse across pixels/frames to spend visibility/shading on high-contribution candidates.

**Evidence context:** The paper distinguishes unbiased and lower-noise biased versions; original results used RTX 2080 Ti/Titan RTX and omit shared G-buffer rasterization costs.

**Limits:** Energy loss in the biased form and temporal sample dominance are explicit tradeoffs. Old speedup ratios are not expected incremental gains over RTXDI 3.1.

**Integration proposal:** Foundational DI correctness and baseline reference; RTXDI already supplies its production lineage.

**Priority: high.** Keep DI as a separately measurable baseline while modifying PT.

**Validation proposal:** Direct-light analytic scenes, visibility discontinuities, dynamic lights and history limits; report biased options separately.

## Summary and lessons learned

Sampling, camera-domain reuse, visibility approximation, gradient reconstruction, differentiable rendering and baked probes solve distinct problems. The highest-value supporting work defines the estimator contracts and temporal baseline; historical production optimizations must be audited against current RTXDI before being counted as new work. Reported gains use incompatible workloads and cannot be multiplied. Every proposed port needs complete-frame, equal-quality and equal-time comparisons, with raw/denoised output and statistical mean checks separated.
