# B8: disjoint DI, GI and ReSTIR PT contribution ownership

Retained strict-track design/source audit, 2026-10-29 Europe/Zurich. Subsequent initial-only implementation and the opt-in NVIDIA GI approximation are tracked in [the staged implementation](B8_STAGED_IMPLEMENTATION.md). This note is not a claim that strict glossy GI reuse is implemented. Use [the canonical B0–B10 ledger](VERSION_MAPPING.md); this note proposes a transport contract for the requested combined mode.

## Main conclusion

DI, GI and PT need either disjoint contribution domains or a correctly derived weighted combination over overlapping domains. This project chooses a **disjoint integrand partition** for B8. The current GI path collects the entire suffix after its first eligible non-delta scatter, while current ReSTIR PT also estimates indirect suffixes. Enabling both toggles would overlap. Moreover, “GI owns emission at the first secondary surface” overlaps ordinary DI: camera→primary→emitter already is a primary direct-light path.

Use accepted **scattering count**, not UI names or raw ray-hit counts:

- Native owns directly visible emission/environment and explicitly unsupported fallback domains.
- DI owns one-scattering direct lighting at the primary surface.
- GI owns a restricted, provably valid two-scattering domain.
- ReSTIR PT owns three-or-more-scattering paths.

**Track distinction:** the user selected NVIDIA's documented non-directional GI approximation for practical B8 reuse. It retains the disjoint short-GI/long-PT split and explicitly accepts the inherited GI approximation and bias controls. Exact outgoing-direction reevaluation remains a separate research enhancement, not a prerequisite for that approximate track.

For the first strict GI implementation that reuses unchanged secondary RGB, restrict its secondary endpoint to a **verified outgoing-direction-independent Lambertian response**. Native traces the remaining two-scattering paths. The current GI reservoir cannot correctly reevaluate glossy secondary outgoing radiance after reconnection, and the default diffuse model is Frostbite, not Lambertian. A later general GI implementation needs extended payload/reevaluation; it must not silently claim exact glossy reuse.

## What the current code actually does

Paths below are repository-relative. Shader inspection applies to the retained development source `a7428c8`; subsequent GUI label/input changes do not alter these shader paths.

1. `Rtxpt/Shaders/PathTracer/PathTracerHandleHit.hlsli`, `GenerateScatterRay(BSDFSample,...)`: the PT ownership early return appears **before** GI setup. If PT owns the dominant primary, native continuation stops before `restirGIStarted` can be set.
2. In the following GI block, the first dominant-plane non-delta scatter (`bs.pdf !=0`) sets `restirGIStarted` and `restirGICollectSecondarySurface`. It stores the primary scatter PDF and deliberately omits the primary `bs.weight` multiplication.
3. `PathTracer.hlsli::ShouldCollectGISecondaryRadiance` returns `restirGIStarted` indefinitely. `AccumulatePathRadiance` diverts every later eligible NEE, emissive hit, environment miss and cached suffix into `u_SecondarySurfaceRadiance.rgb`. It is **not** a one-bounce GI payload.
4. `HandleHit` stores the first secondary position/normal and clears only `restirGICollectSecondarySurface`. `HandleMiss` can store a distant virtual endpoint when that first continuation misses.
5. `Shaders/Bindings/ReSTIRBindings.hlsli` stores secondary position/normal, accumulated suffix RGB and primary scatter PDF. `GITemporalResampling.hlsl` constructs `RTXDI_MakeGIReservoir(position,normal,radiance,primaryScatterPdf)`; the runtime initializer sets contribution weight1/pdf, M1, age0. `GIFinalShading.hlsl` applies the primary BSDF using `surface.Eval(direction)`, which already includes its cosine convention.
6. `Rtxpt/SampleUI.h::ActualUseReSTIRGI` explicitly requires `!ActualUseReSTIRPT()`. `AdvancedSample.cpp` dispatches effective DI, GI and PT separately; simply removing that exclusion would not establish valid transport ownership.
7. Current PT `Rtxpt/RTXDI/PT/Bridge.hlsli::RAB_PathTrace` samples from the primary, advances/replays prefixes, records NEE at accepted secondary/later vertices, and records explicit BSDF emitter/environment hits for delta events. Its continuous light-hit contribution is represented by NEE. No lower path-length contribution filter separates “GI-short” from “PT-long”.
8. The current native PT owner flag in `Shaders/Bindings/PTPrimaryData.h` is frame-tagged. Export in `PathTracerSurfaceBridgeDonut.hlsli` requires primary native vertex1, unit prefix throughput, some non-delta reflection, no transmission and an empty medium. That mask currently owns **all** indirect transport at such primaries; it needs a new B8 ownership contract.

## Physical path partition

Let x0 be the camera, x1 the first accepted material surface and x2 the next material surface. Let k be the number of actual BSDF scattering events before reaching emitted light. A path can contain null/alpha-rejected/false-medium interfaces without increasing k. A terminal emissive material can itself scatter on other longer paths; its emitted and scattered terms are distinct contributions.

- k0: directly visible surface emission or camera environment miss.
- k1: x0→x1→light. This includes BSDF hits at an emissive x2 and environment after scattering at x1.
- k2: x0→x1→x2→light. This includes NEE at x2 and BSDF hit/environment **after scattering at x2**. Emission of x2 itself belongs to k1, not this domain.
- k≥3: longer paths.

Define deterministic eligibility D(x1) for a valid DI primary, P(x1) for a valid B8 split primary and L(x2) for the restricted GI secondary. For the first strict implementation, P requires first actual surface, opaque nontransmissive material, no medium, unit prefix, one plane/pinhole and **no delta lobes at the primary**. Do not infer P from the randomly selected BSDF lobe. A mixed-delta primary initially remains native fallback unless a lobe-labelled split is separately derived.

L requires a material/BSDF implementation whose radiance is outgoing-direction-independent within the relevant hemisphere, with compatible normals/sides and no transmission/delta response. Roughness1 or a material named “Diffuse” is not sufficient. `BSDFs/BxDFConfig.hlsli` defaults `DiffuseBrdfFrostbite`; a global switch to Lambertian would change the baseline renderer and is not an acceptable hidden test-scene fix. Add an explicit verified material capability or keep L=false for unsupported secondary materials. If the chosen fixture has no qualifying endpoint, report no active GI contribution rather than claiming combined-path coverage.

The proposed characteristic functions are:

    chi_DI = D * [k=1]
    chi_GI = P * L * [k=2]
    chi_PT = P * [k>=3]
    chi_N  = [k=0] + (1-D)*[k=1]
             + (1-P)*[k>=2] + P*(1-L)*[k=2]

For every supported physical path, chi_N+chi_DI+chi_GI+chi_PT=1 and each is0or1. For k2, L is evaluated at that path's x2; other domains need not evaluate it. This design keeps PT-long independent of secondary material classification, avoiding a sample-class change under hybrid shifts of a k2 PT path. An alternative PT domain `[k>=3] or ([k=2] and !L)` would need L reevaluation and corresponding inverse support tests at every shifted k2 prefix; do not implement that shortcut from stored radiance alone.

These masks multiply the **physical integrand**. NEE and BSDF sampling techniques for one path length still use their internal MIS whose weights sum to one. Do not classify one technique as “DI” and another technique for the same path as “GI”, then count both as complete estimates.

## DI contract

At a DI-eligible primary, DI estimates the whole k1 reflected direct term using the pinned DI light/BRDF proposals and its existing actual settings. Native NEE and native continuous BSDF emitter/environment counterparts for that primary must be suppressed consistently. The existing `PathTracerNEE.hlsli::HandleNEE` DI branch suppresses NEE and sets `SkipEmissiveBRDF`; current hit/miss code consults that bit. Preserve or explicitly replace both halves under the same D predicate.

Primary directly visible emission, directly visible environment and primary delta/transmission fallback are native domains. Do not allow the k2 GI payload to reintroduce Le(x2) that DI already estimates. For a non-DI primary, native k1 remains active and the other component masks are unchanged. First strict B8 may require DI enabled and reject a missing DI configuration rather than improvise a new direct estimator.

## A precise restricted GI initial estimator

At eligible x1, sample a continuous direction omega12 with the **full marginal** primary BSDF proposal q1(omega12|x1), and trace to accepted x2. If no actual surface is hit, this is a k1 environment event; no GI candidate is created. If L(x2)=false, this draw creates no GI candidate; the native two-scattering fallback independently covers that domain.

For L=true, construct an unbiased estimate Z1(x2) of **direct reflected radiance at x2 only**, excluding Le(x2), all reflected suffixes with another intermediate scattering vertex and cache values containing longer transport. Its outgoing direction is towards x1. For genuinely Lambertian x2 this Z1 distribution/expectation is independent of that outgoing direction within the permitted hemisphere.

For a simple all-light-support NEE-only initial implementation:

    Z1(x2) = EvalBSDF2(omega_light) * Le_light * visibility * W_light / pOmega_light

Here `EvalBSDF2` follows the renderer's f*cos convention (do not multiply the cosine twice); W_light is the finalized RIS light-selection contribution weight when RIS is used, and pOmega_light is the returned conditional solid-angle density. With direct light draws instead of RIS, the equivalent denominator includes light-selection probability and its conditional point/direction PDF. Match the exact pinned light sampler semantics rather than transplanting1/r.weightSum as an unconditional density. Area/continuous-environment and delta analytic lights require their respective mixed-measure conventions. Start with verified supported lights; reject unsupported emissive-light support rather than lose a domain silently.

NEE-only here uses light/BSDF path MIS weight1 because a BSDF light-hit counterpart is not included in Z1. Alternatively include both NEE and BSDF emitter/environment techniques at x2 with their exact complementary MIS, but terminate after the terminal light hit and do not include NEE at x3. Never downweight NEE against a BSDF counterpart that was removed by truncation.

Store x2 position, its correct geometric normal, Z1 and q1. The initial GI estimator before reuse is:

    I_GI_draw = EvalBSDF1(omega12) * Z1(x2) / q1(omega12|x1)

The primary BSDF and1/q1 must each occur exactly once. This matches the conceptual decomposition of the existing GI export, but the current export's suffix RGB must be replaced/restricted; clearing it after several deep contributions is too late.

Prefer a dedicated short-GI producer first: it traces the primary proposal, evaluates Z1 at x2 and writes an explicitly tagged GI-short record. That avoids retrofitting `restirGIStarted` before x2's eligibility is known, and makes its acceptance/PDF visible. A later optimization may share the native first continuation through a carefully factored export. Correlation between GI-short/native-short/PT-long samples is allowed by linearity if each estimator is correct, but requires its own variance assessment; distinct effect seeds make the first ablation easier to inspect.

### GI reuse and an existing approximation barrier

For fixed endpoint x2, shifting the primary from a to b maps source solid angle to destination solid angle with:

    J_GI = G(b,x2) / G(a,x2)
    G(a,x2) = abs(n_geom2 dot direction(x2→a)) / distance(a,x2)^2

This is the ratio `dOmega_destination/dOmega_source`; reverse mapping uses its inverse at the same endpoint. The target at receiver b is luminance(EvalBSDF_b(direction b→x2)*Z1). Its resampling weights and inverse normalization need the actual Jacobian, source UCW, confidence and correct visibility support.

Current `RtxdiApplicationBridge.hlsli::RAB_ValidateGISampleWithJacobian` rejects outside[0.1,10] and **clamps accepted Jacobians to[1/3,3]**. Current GI defaults also use Basic correction, boiling, permutation and `GIFinalShading`'s roughness-dependent final/initial blend. These are not a strict unbiasedness proof. For a strict reference track: disable sample-dependent filters/approximate final blend, use the raw Jacobian and explicit finite/support checks, and evaluate the necessary visibility/normalization terms. If rejection limits remain, their partial-map support must be treated consistently in both directions; an incorrect Jacobian cannot be made correct by labelling it a quality control.

Even after these fixes, scalar secondary radiance is insufficient for general glossy/view-dependent x2. To extend GI beyond L, store the light/path sampling payload and material state required to reevaluate its target for the new outgoing direction, with full proposal/selection UCW and support; update every forward/inverse/final evaluation. That is an explicit root-overlay extension, not the existing32-byte GI reservoir magically becoming a general path reservoir.

## Native short/fallback execution

Current PT's immediate primary return must be replaced in combined B8 mode. Native needs enough continuation to estimate its assigned k2 fallback:

- At P=false, keep native transport through the user's original cap; prevent GI collection for that fallback primary.
- At P=true, keep native k0/k1 only as assigned by D, and trace the short branch far enough to see x2 and, for L=false, the terminal BSDF emitter/environment after scattering at x2.
- For L=false, native NEE at x2 and its BSDF terminal counterpart at x3 form k2 and keep complementary MIS.
- After terminal emission at x3, stop before NEE at x3 or another continuation; those are k≥3 and belong to PT-long.
- For L=true, native k2 is masked out because GI-short estimates it. Preserve any k1 Le(x2) handling before this decision.

Use an explicit radiance-routing predicate in hit/NEE/miss accumulation. Do not merely set a global bounce cap2 for all pixels: P=false native fallback still requires the original cap, and an emission hit's order differs from the NEE vertex's order. The existing clean-truncation comment in `HandleHit` explains why the terminal BSDF emission must be collected before stopping.

If a reservoir happens to select zero light, native must **not** reactivate the same domain as an opportunistic fallback. That selection is an ordinary zero-valued estimator outcome. Fallback is determined before sampling by supported geometry/material/frame contract, not by radiance or successful selection. Likewise, finite sanitization is diagnostic, not permission to substitute a second estimate of already-owned transport.

## PT-long filtering and source PDF

The runtime uses light-inclusive path length d: k=d-1 for the current primary anchor. `Sample::RtxdiSetupFrame` already maps native capB to max path lengthB+1. PT-long accepts d≥4, while respecting d≤B+1.

At `ctx.GetBounceDepth()==2`, the first traced secondary is x2 and `RecordNeeLightSample` would create d3 (k2); reject that contribution for PT-long. Still advance the path/reconnection state: later NEE at x3 creates d4 (k3), which is valid. For BSDF emissive/environment recordings the stored length is the current bounce depth; reject d2/d3, accept d≥4. Rejecting early contributions must not prematurely terminate the prefix needed by long paths.

Implement one explicit contribution-acceptance function before each initial RIS stream operation, and preserve the same domain in stored paths and all target/replay/inverse evaluations. Do not change the proposal into a conditional distribution “given long path” without recording that conditioning probability. Empty path trees contribute zero; they are not discarded from the initial-sample count to inflate the estimate. Existing roulette survival PDFs and full BSDF/NEE proposal weights remain in their existing roles; filtering an integrand term does not remove its sampling factors.

Hybrid shifts preserve d and therefore the k≥3 class, which is one reason to prefer a pure-length PT domain. Reset/reject old reservoirs with d<4 and any prior domain-contract version. The existing packed path reservoir has no version field: use an application-owned history generation/receipt and explicit clear, or a root sidecar with validated identity. Do not silently reuse standalone full-indirect GI/PT history in B8-long.

## Alpha, delta, media and material boundaries

- Alpha-rejected triangles and false interfaces do not increase k. Keep native and bridge alpha tests, opacity interpretation and sample coordinates consistent; do not make “number of intersections” the domain index.
- A delta first scatter uses discrete mass, not a solid-angle q1. First strict P excludes primary delta/mixed-delta responses, leaving full native fallback. A later lobe-labelled partition must record selection mass, transport component and reference conventions explicitly.
- Delta events later in PT-long remain valid under its hybrid/replay/discrete-weight rules. At a non-L secondary, native k2 includes delta-secondary light hits as a fallback domain.
- Native GI currently treats primary scatter PDF0 as empty, so it cannot be used as a delta measure carrier without an extension.
- Transmission/media/shadow transmittance, nested state, binding diffuse limits, PSR, reconstruction and multiple layers remain independently gated. Restricting the contribution length does not solve their replay/medium/PDF problems. The current global opaque/nonbinding-cap PT checks remain until their separate acceptance work completes.
- Geometry/material/light changes can change P/L or direct support. Reevaluate eligibility and invalidate affected histories; a cached GI radiance sample from a now-ineligible material cannot keep claiming the old domain.

## Host/resources/reset contract

Add a named combined ownership mode, not a generic removal of `!ActualUseReSTIRPT` from `ActualUseReSTIRGI`. Report actual DI/GI/PT=1, the four domain definitions and contract version, while maintaining old separate GI and PT modes.

The first B8 host schedule should use explicit separate final passes: native primary/short/fallback merge first, then DI, GI-short and PT-long additions exactly once. Disable the fused DI/GI final optimization until component ownership and raw output match the separate sequence. Keep GI and PT reservoirs, their canonical inputs, sidecars and histories distinct with correct barriers. Any all-candidate PT RGB shading buffer replaces its PT-long scalar contribution; it is not another independent indirect add.

Clear GI export textures every frame and assign frame/domain owner tags, including misses and invalid pixels. Invalidate on combined-mode change, length boundary, P/L capability definition, cap/diffuse policy, BSDF/lobe model, light proposal version, scene/material changes, camera cuts/resize and any RNG/replay construction change. Explicit history/camera states must not use selected-reservoir age as an ownership tag.

For raw correctness, keep AA0, no denoiser/cache/PSR/subsampling, one plane and nonbinding diffuse cap. Report allocated GI+PT resources and all extra short tracing/reuse/barrier costs. The combined design may cost more than either alone; it is not automatically a performance improvement or the PT++ paper's unified single-reservoir method.

## Independent mathematical and GPU gates

Before GPU work, build an exact finite path catalog whose paths include k0,k1,k2-L,k2-non-L,k3+, delta-primary fallback, secondary delta, alpha/null interfaces and zero contribution. Independently compute the full RGB integral, assert the four characteristics sum to1 at **every physical path**, then enumerate proposal draws, their PDFs/discrete masses and internal NEE/BSDF MIS. Test each component against its separately declared reference and their sum against the full integral. Mutation tests must detect including Le(x2) in GI, leaving deep suffixes in GI, dropping terminal BSDF emission, extra primary BSDF/pdf factors, sample-success-dependent fallback, forgetting a domain-generation reset and confusing raw hits with actual scattering count.

Use a second independent finite weighted-domain GI oracle for a→x2 reconnection: nonuniform masses/PDFs, geometric Jacobians, partial visibility support, unequal confidence and Lambertian versus deliberately view-dependent secondary responses. Demonstrate that reusing unchanged glossy Z1 fails the declared reference, and that a raw/clamped Jacobian substitution is detected. Existing paired-PT algebra does not validate this different GI payload.

GPU validation must then proceed component-first:

1. Initial-only DI/GI-short/PT-long/native components, no reuse. Export raw linear components and event/path-length/material masks. Fixed seeds and actual domain counters prove GI-short and PT-long both contribute when the fixture supports them.
2. Vary total caps1,2,3,4: cap1 has no GI/PT-long; cap2 enables the GI/native-short partition but PT-long stays zero; cap3 introduces PT-long. Compare per-component and sum to independently masked native high-spp references, including finite-reference discrepancy.
3. One component's reuse at a time, then combinations. Check frame-tagged history, material/eligibility transitions, cuts/resize and no stale component texture additions.
4. Explicit emissive-secondary test proves Le(x2) is DI-owned; emissive-tertiary/environment and secondary-mirror tests prove k2 handling; alpha tests prove nulls do not add a scatter.
5. Native fallback and unsupported settings tests, then multiple seeds, motion/temporal metrics and reconstruction only after raw acceptance.
6. Repeated cap-verified isolated timing and memory accounting, with diagnostics off and all component costs included. Preserve mandatory original Convergence/Kitchen rows as unsupported until their original material and14/2 transport gates genuinely pass.

## Zero-intensity EnvironmentLight: source-level survival proof

The scene's local light cleanup does **not** remove the registered environment leaf:

- `Rtxpt/Sample.h:370` declares the application's separate `m_lights` vector.
- `Sample.cpp` near790 copies shared pointers from `m_scene->GetSceneGraph()->GetLights()` into that vector. It finds `envLight` and copies path/intensity into environment runtime settings **before** the cleanup near831.
- The cleanup only executes `m_lights.erase(...)`. No `SceneGraph::Detach`/unregister call occurs. `EnvironmentLight::FillLightConstants` writes zero for **all** environment lights, so their removal from this local analytic-light list is normal even with intensity1.
- Donut `SceneGraph.h:532` owns a different `m_Lights` vector; `GetLights()` at557 returns its const reference. `SceneGraph.cpp:587` registers a light there. Removal at663–665 is inside the explicit leaf-unregistration path, which local vector erase does not invoke. The scene node and graph vector keep their shared pointers alive.
- `PrepareLightsPass::Process` reads the graph's `GetLights()`, not the local application vector. Its `ConvertLight` Environment case checks only that an environment map is enabled, then appends an environment-type record regardless of intensity.

Therefore an explicit registered EnvironmentLight with **intensity0** and a nonempty valid path remains in the scene graph and contributes a proper zero-radiance environment record to RTXDI light preparation. The source's subtraction then has one actual environment record to remove from ordinary-infinite count, preventing the no-record underflow. `radianceScale:[0,0,0]` is ignored by the original `EnvironmentLight::Load` and is not a substitute.

The raw source cubemap and its importance hierarchy are baked independently of runtime intensity. Intensity0 is applied later through `EnvMapSceneParams.ColorMultiplier`; use a finite nonblack pinned source so its unscaled importance integral is positive. An all-black source has an unguarded0/0 PDF risk. This proof establishes container lifetime/registration and intended PDF/radiance data flow by source; a finite GPU payload/index preflight on the new fixture remains necessary before measurement. Do not misrepresent this code audit as that run.

## Summary and lessons learned

A correct combined label needs separate path-domain integrals, usable secondary-radiance reevaluation and verified fallback. Current GI payload/approximation constraints are active correctness gates; this design does not remove them or establish a speedup. The zero-intensity environment fixture passed its registered-room GPU preflight and measurement checks; this establishes fixture usability, not combined B8 correctness.

## Exact CPU prerequisite gate —2026-10-29

Seventeen new tests in `Benchmarks/tools/test_transport_partition_oracle.py` pass using exact rational arithmetic. The implementation lives in `transport_partition_oracle.py`; its frozen source hashes, test output and counterexample values are retained in `Benchmarks/development/2026-10-29-b8-partition-oracles`.

The tests independently check all56 combinations of scattering count and eligibility, a labelled RGB physical-path catalog, nonuniform measures/proposals, unequal NEE/BSDF technique counts, secondary-emission ownership, alpha/null interfaces, empty draws, primary BSDF/PDF factors and support. Negative controls detect full-suffix GI overlap, classifying raw hits as scattering events, conditioning on successful GI candidates and removing a BSDF counterpart while retaining its old NEE MIS weight.

A second finite geometric example uses source/target solid-angle derivatives with Jacobians1/4 and4. Both lie inside the native validator's1/10–10 acceptance interval. Replacing their transfer Jacobians by the1/3–3 clamp changes the declared estimator's result. With view-dependent secondary outgoing radiance, unchanged stored RGB also misses the target integral; reevaluation restores this finite example. These are counterexamples for the explicitly declared finite transfer model, not a measured bias magnitude or a complete diagnosis of every native GI estimator.

### Initial-only GPU stage before GI reuse

A fixed-outgoing-direction GI-short initial sampler can evaluate a general non-delta secondary BSDF correctly. Its outgoing direction has not changed, so the unchanged-RGB reuse objection does not apply. An additional exact test includes the otherwise ineligible secondary endpoint at its original outgoing direction and recovers the full short-path integral.

This permits a bounded first GPU stage: DI for primary direct lighting, GI-short **initial sampling only**, PT-long for longer paths and native fallback, with separate component exports. It does not grant glossy GI temporal/spatial reuse or establish the complete canonical B8 configuration. Delta-light support, native fallback, PDF measures, resets, buffer ownership and all required GPU component checks remain implementation gates. These CPU tests alone enable no mode. A subsequent opt-in GPU implementation now exercises this initial-only GI stage; see [staged implementation and evidence](B8_STAGED_IMPLEMENTATION.md). General GI reuse and full canonical acceptance remain pending.
