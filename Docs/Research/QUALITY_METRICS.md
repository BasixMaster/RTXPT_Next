# Image quality and temporal stability measurement plan

Checked 2026-10-28. This is a source-backed metric specification and proposed comparison protocol, not metrics code, renderer implementation, captured images or measured results. Final comparison basis remains B0: untouched RTXPT 1.9 with its scenes and original dependency pins; B1: future RTXDI 3.1 adoption; B2+: future isolated optimization variants. RTXDI 3.1 is currently a linked reference, not an applied B0 runtime change.

## What the selected papers actually report

| Source | Verified metric and locator | Important boundary |
| --- | --- | --- |
| [PT++](https://cwyman.org/papers/i3d26_ReSTIRPT++.pdf) | HDR-FLIP, §7 pp11–12; MSE and FLIP convergence, §7.4 pp14–16 and Fig15 p17; mean absolute relative bias, Fig5 p9 | Fig15 reruns one camera animation 1024 times using different sampling seeds and compares the same view. Its FLIP description does not specify exposure range, tone mapper, PPD or software revision. Those must be recorded in our tests; reproducing defaults is not reproducing undisclosed paper settings. |
| [Compatibility-guided neighbors (CGNS)](https://cwyman.org/papers/hpg26_compatibleNeighborSelection.pdf) | SMAPE, footnote3 p8; spatial relative covariance and temporal relative autocovariance, Appendix A p16; capture protocol, §7 p9 | Main numeric tests use static camera, 40-frame warm-up, ten trials over 2048-frame sequences, temporal lag 3, radius-8 spatial covariance. Geometrically hardest 10% of pixels are also reported. Dynamic testing requires added alignment controls. |
| [Stochastic pairwise MIS](https://cwyman.org/papers/eg26_StochasticPairwiseMIS.pdf) | MAPE formula, §6 p7 | Figure5 p8 captures the last frame of a 50-frame animation; that is not a complete temporal quality measurement. Formula does not fully specify RGB reduction/color-space handling. |
| [ReSTIR PG](https://cwyman.org/papers/siga25_ReSTIR_PG.pdf) | MAPE with grayscale reference denominator, §5 p8 footnote4 | The tested configurations use separate DI and indirect guiding, no roulette and scene-specific bounce caps. Do not compare metric values across these settings as if they shared one estimator budget. |
| [ReSTIR LoD](https://cwyman.org/papers/sig26_ReSTIR_LoD.pdf) | RelMSE labels in Fig1 p1 and result captions | No exact RelMSE formula was identified in the inspected main PDF text. A named RelMSE score is insufficient to recover channel reduction and stabilization convention. The formula below is our explicit project definition until code/supplement verification supplies the authors' exact one. |
| [Multi-layer reservoir splatting](https://cwyman.org/papers/sig26_multiLayerReSTIR.pdf) | MAPE and FLIP, §6 p5 | Its footnote3 warns whole-frame errors can hide gains because disoccluded regions are a small fraction of the image. It cites 2020 FLIP; HDR versus LDR mode and settings are not established by that citation alone. |

None of these paper excerpts establishes a common universal pass/fail threshold. Report operating curves, per-scene/ROI outcomes and uncertainty before choosing application-specific acceptance targets.

## Shared notation and preprocessing: proposed project conventions

Let \(I_{n,t,i,c}\) be linear scene-referred RGB radiance from independent run \(n\), frame \(t\), pixel \(i\), channel \(c\); \(R_{t,i,c}\) is the high-quality reference for that exact frame, scene, geometry/LoD, shutter/lens/filter and lighting state. Let \(Y(I)=0.2126I_R+0.7152I_G+0.0722I_B\) after conversion to linear Rec.709 primaries. These luminance coefficients and the conversion rule are our documented conventions, not a claim that all papers use these exact coefficients. Store source primaries, white point, radiometric scale, units/exposure multiplier and conversion matrix.

Use float HDR captures before tone mapping, sharpening, UI and display transfer for radiometric metrics. Do not compute these metrics on heatmaps or 8-bit screenshots. Do not normalize each candidate to its own brightness: that can conceal energy bias. If storage uses pre-exposure, undo the recorded multiplier before evaluation. Keep identical finite-value handling across variants; count NaN/Inf/negative samples and report them separately rather than silently hiding failures with clamping. Define the reference's uncertainty from independently converged reference batches; reference noise must be small enough to resolve the proposed difference.

Always state whether a reported scalar is a mean over channels, pixels, frames or independent runs. Evaluate each run before averaging its metric for single-frame quality. Evaluating only the image averaged across runs answers a bias/convergence question and suppresses single-frame noise.

## Metric definitions and attribution

### SMAPE following CGNS

For nonnegative luminance \(y_i=Y(I_i)\), \(r_i=Y(R_i)\), use

\[
\operatorname{SMAPE}_{\rm CGNS}=\frac{100}{|\Omega|}
\sum_{i\in\Omega}\frac{|y_i-r_i|}{|y_i|+|r_i|+10^{-4}}.
\]

This follows CGNS footnote3 p8. Preserve its factor **100**, rather than substituting the factor 200 used by another common SMAPE convention. The fixed epsilon is tied to image scale; record the radiance scale to make comparisons reproducible. SMAPE limits bright outlier dominance but is not a pure variance statistic: bias contributes, and saturated-color errors can be underrepresented in luminance. Report an RGB-sensitive metric alongside it. The papers do not establish external display exposure settings for this formula; compute on the explicitly recorded HDR scale as our test convention.

### MAPE following SPMIS and PG, with explicit project channel handling

SPMIS §6 p7 writes

\[
\operatorname{MAPE}=\operatorname{mean}\left(
\frac{|I-R|}{R+0.01\operatorname{mean}(R)}\right).
\]

PG footnote4 p8 instead explicitly uses grayscale reference \(\widetilde R\) in the denominator:

\[
\operatorname{MAPE}_{\rm PG}=\operatorname{mean}\left(
\frac{|I-R|}{\widetilde R+0.01\operatorname{mean}(\widetilde R)}\right).
\]

The excerpts do not completely specify color conversion and reduction. Our named `MAPE_RGB_Ydenom` resolves them: average absolute RGB error over all channels/pixels, divide each channel's error by \(Y(R_i)+0.01\mu_R\), where \(\mu_R\) is the **full reference frame** mean luminance. Preserve the full-frame \(\mu_R\) when reducing an ROI so its normalization does not change merely because the crop changes. This ROI choice is ours. Also emit `MAPE_Y` on luminance if a direct scalar-luminance comparison is useful. Keep values as ratios; multiply by 100 only for a separately labelled percent display. If \(\mu_R=0\), report the relative metric unavailable and report absolute error for that frame rather than silently inventing a denominator.

### RelMSE: explicitly proposed project definition, not recovered LoD implementation

Let \(\mu_R=\operatorname{mean}_i Y(R_i)\), \(d_i=Y(R_i)^2+(0.01\mu_R)^2\). Define

\[
\operatorname{RelMSE}_{\rm project}
=\frac{1}{3|\Omega|}\sum_{i\in\Omega}\sum_{c\in\{R,G,B\}}
\frac{(I_{i,c}-R_{i,c})^2}{d_i}.
\]

This is an original measurement convention inspired by relative-error reporting in the ReSTIR literature. It is **not asserted to reproduce ReSTIR LoD's exact scores**. Its denominator is not \((Y(R_i)+0.01\mu_R)^2\); those alternatives differ. Record the formula/version in every result. Use full-frame \(\mu_R\) for ROI scores and flag all-black references as unavailable for this relative measure. Include absolute linear RGB MSE in parallel,

\[
\operatorname{MSE}_{\rm RGB}=\frac{1}{3|\Omega|}\sum_{i,c}(I_{i,c}-R_{i,c})^2,
\]

because relative normalization emphasizes dark regions while MSE emphasizes bright energetic outliers. Do not switch definitions between B0/B1/B2 or rank variants against published RelMSE numbers from another convention.

### HDR-FLIP and displayed-image FLIP

PT++ explicitly uses HDR-FLIP. It combines errors from exposure-compensated, tone-mapped image pairs. The official implementation exposes both images equally, computes LDR-FLIP at each exposure, and takes the per-pixel maximum; mean HDR-FLIP averages that map. Thus

\[
E_i^{\rm HDR}=\max_{e\in\mathcal E}
\operatorname{LDRFLIP}_i\left(T(2^eI),T(2^eR);\mathrm{PPD}\right),
\quad F_{\rm HDR}=\operatorname{mean}_i E_i^{\rm HDR}.
\]

This compact definition delegates LDR-FLIP's perceptual color/feature filtering to the official evaluator; it is not a substitute reimplementation. Pin evaluator revision/backend, PPD, tone mapper, exposure start/stop/count and input conversion. Auto exposures derive from the reference in the inspected implementation; save resolved values and reuse them across variants. PT++ Fig15 p17 notes FLIP is less sensitive to fireflies/correlation but remains sensitive to brightness differences. Sources: [HDR-FLIP publication](https://research.nvidia.com/publication/2021-05_visualizing-errors-rendered-high-dynamic-range-images), [official evaluator](https://github.com/NVlabs/flip/blob/main/src/cpp/FLIP.h#L2126), [parameter documentation](https://github.com/NVlabs/flip/blob/main/src/python/README.md).

Our proposed reporting is mean plus an uncolored error map and ROI/high-percentile summaries. Evaluate full-frame FLIP first, then reduce its map over ROI masks: cropping inputs before the evaluator changes spatial-filter boundaries and potentially auto-exposure. For the actual displayed output, separately evaluate LDR-FLIP after the fixed documented display transform. Do not call that HDR-FLIP or mix it with raw-radiance scores. A static perceptual image metric does not measure temporal flicker.

### Relative spatial covariance and temporal autocovariance: exact CGNS equations

CGNS Appendix A p16 uses grayscale luminance \(y_{n,i}\), sample mean \(\bar y_i=N^{-1}\sum_n y_{n,i}\), and \(\epsilon=10^{-4}\):

\[
r_{ij}=\frac{1}{N-1}\sum_{n=1}^N
\left(\frac{y_{n,i}-\bar y_i}{\bar y_i+\epsilon}\right)
\left(\frac{y_{n,j}-\bar y_j}{\bar y_j+\epsilon}\right).
\]

It averages \(r_{ij}\) in radius-8 disks, then over pixels. Although introductory wording mentions ground-truth normalization, **the printed equations normalize by the sample mean**, not \(R\). Do not silently replace the denominator when claiming reproduction. The text does not explicitly resolve inclusion of the center pixel or border weighting; our convention is to exclude the center (self-variance), average valid neighbors per center, then average centers. Label this convention; exact author-code verification may require changing it before claiming bit-level reproduction.

For \(N\) independent video sequences of the same static scene, define separate means at each frame and use lag \(T=3\):

\[
a_i^{(t)}=\frac{1}{N-1}\sum_{n=1}^N
\left(\frac{y_{n,t,i}-\bar y_{t,i}}{\bar y_{t,i}+\epsilon}\right)
\left(\frac{y_{n,t+T,i}-\bar y_{t+T,i}}{\bar y_{t+T,i}+\epsilon}\right).
\]

Average over valid frames/pixels. CGNS reports similar behavior for lags 1–5. This is normalized covariance, **not Pearson correlation**: do not divide again by standard deviations. Show covariance and error together: increasing independent noise or resetting history can reduce covariance while harming quality. Full-frame static-scene covariance is the paper-aligned measurement; moving cameras/objects require separate treatment below.

## Reproducible capture and comparison plan: proposed, not executed

1. **Freeze variants and content.** Archive B0 executable/config/dependency/asset revisions and untouched RTXPT 1.9 scene set. Define B1 and each B2+ variant before benchmarking. Record GPU/driver, clocks/power state, resolution/internal render scale, sample rate, bounces, light sampling, cache/denoiser modes and memory footprint. Add challenging test scenes only as explicitly separate workloads with their own asset license/revision and scene requirements.
2. **Separate output tracks.** Capture raw HDR with denoising disabled; a fixed NRD path; and a fixed DLSS-RR path where available. Keep model/version, input scale, history reset, jitter, exposure and sharpening settings constant within each track. Raw versus denoised outcomes answer different questions. An approximate cache/reference mode must be labelled and compared to a matching support/transport reference; denoising success cannot establish an unbiased estimator.
3. **Generate matched references.** For static frames and deterministic animations, render independent high-spp references at each required time and exact scene state. For LoD, retain a same-LoD reference for estimator error and an all-high-detail reference for geometric approximation error; do not combine those into an unexplained single score. Match shutter/lens/pixel filter, output size and exposure policy. Record reference noise/convergence checks.
4. **Use independent runs and histories.** Reset the complete history at the start of each independent seed run; preserve history within a run. Pair B0/B1/B2 by camera/event/seed schedule for lower-variance differences, but do not assume identical random-number consumption after algorithm changes. Use run/sequence-level confidence intervals or bootstrap; frames/pixels connected by ReSTIR history are not independent replicate counts. Choose run count from a pilot and precision target, then record the fixed capture design. CGNS's ten 2048-frame sequences/40-frame warm-up and PT++'s 1024 reruns are source examples, not arbitrary universal requirements.
5. **Include cold and steady states.** Measure startup/history reset separately from warm steady state, plus scripted camera pans, thin-geometry reveal, large disocclusions, moving emitters, material changes, caustic discovery and LoD switches. Warm-up must not erase the very transient being evaluated. Keep event time/trajectory identical across methods.
6. **Compare both equal budget and equal quality.** At equal GPU time, permit explicitly logged spp/neighbor-budget changes; report the resulting quality/memory. At equal quality, estimate time-to-target from sampled operating curves. Keep display reconstruction track and target definition fixed. Do not multiply speedups from different papers or report a target never reached as an interpolated success.

## ROI, flicker and recovery: proposed definitions

Derive masks from deterministic high-quality geometry/visibility metadata, not each algorithm's observed error. Record total/full-frame area and invalid counts for every ROI. Report whole frame plus (a) first visible/disoccluded pixels, (b) time-since-visibility age buckets, (c) thin geometry/foliage, (d) glossy/specular paths, (e) shadows and caustics, and (f) stable regions. A hard-pixel ROI based on geometric neighbor compatibility can follow CGNS §7 p9, but freeze its definition across variants. Multi-layer §6 p5 motivates disocclusion-specific scores because whole-frame averaging dilutes them.

For flicker under motion, compute errors relative to the per-frame reference and warp only geometrically valid correspondences. A proposed supplementary statistic is

\[
\operatorname{Flicker}_{\rm project}
=\operatorname{mean}_{(t,i)\in V}
\left|e_{t,i}-\mathcal W_{t-1\to t}(e_{t-1})_i\right|,
\quad e_{t,i}=\frac{Y(I_{t,i})-Y(R_{t,i})}{Y(R_{t,i})+0.01\mu_{R_t}}.
\]

\(V\) excludes disocclusions, invalid warps, topology changes and unsupported transparency; document interpolation and mask rules. This is our metric, **not CGNS Eq17**. Report unmatched/disoccluded regions in their own recovery curves rather than filling missing warped errors with zero. Static sequences additionally use exact CGNS covariance. A camera-locked flicker score can otherwise mistake real motion for stochastic instability.

For an event at \(t_0\), plot ROI error \(Q(k)\) versus frames \(k=t-t_0\) and elapsed GPU milliseconds; include confidence bands. Also report a fixed-window mean error/AUC \(K^{-1}\sum_{k=0}^{K-1}Q(k)\), first-frame error, worst-frame error, and persistent residual. A proposed recovery time is the first \(k\) for which \(Q(k),\ldots,Q(k+L-1)\le q_*\). Choose \(q_*\), hold length \(L\), and window \(K\) from scene/use-case needs **before** evaluating candidates; publish them, do not present them as universal paper thresholds. If never reached, mark recovery as not reached by the capture horizon. Keep a decaying ROI cohort tied to the same surfaces/event, or explicitly state that the ROI evolves; otherwise changing mask membership can manufacture apparent recovery.

## Bias, outliers and estimator checks

Use independent run averages at the **same frame/event state** to estimate \(\hat b_{i,c}=N^{-1}\sum_n I_{n,i,c}-R_{i,c}\). Show signed bias/energy maps as well as an absolute relative summary; attach uncertainty from both test and reference. PT++ Fig5 p9 reports \(\operatorname{mean}(|\mathrm{bias}|/\mathrm{ref})\); our stabilized luminance summary can use \(\operatorname{mean}_i |Y(\hat b_i)|/(Y(R_i)+0.01\mu_R)\), explicitly labelled as our stabilized version. A confidence interval containing zero is not a proof of unbiasedness. Test strict estimator settings and interactive bias controls separately, including duplication history reduction, clamping and caches.

Retain raw max/high-percentile errors, firefly counts with a declared scale-aware definition, missing/invalid samples, and spatial error maps. Perceptual and relative metrics can suppress bright outliers; absolute MSE alone can overemphasize them. Use complementary measures and inspect failure sequences. Do not claim numerical stability from an appealing tone-mapped still image.

## Summary and lessons learned

The selected papers support a complementary suite: radiometric error (MSE/explicit RelMSE and MAPE), luminance-balanced SMAPE, perceptual HDR/display FLIP, and spatial/temporal covariance. Their metric names do not imply identical preprocessing or normalization. Exact CGNS equations and paper-specific settings are preserved above; unspecified choices are labelled project conventions. The next action is to record this schema and capture matrix in the roadmap, preserve B0, then implement evaluation and B1 only in a later authorized stage. No quality or performance improvement has been measured by this document.
