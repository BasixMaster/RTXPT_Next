# B11 integration: compatibility-guided neighbor selection

**Latest B10 checkpoint:** [duplication temporal history](B10_DUPLICATION_HISTORY.md) now has6GPU on/off gates/384frames, exact map counts and active nonzero prior-map reads. Quality14of18sequences; startup reliability prevents timing. Full B10/B11 remain incomplete.

## Summary and lessons learned

**B11 is B10 plus active Compatibility-Guided Neighbor Selection (CGNS). It remains pending, with B10 completion as a dependency.** RTXDI3.1 supplies a real selector, but the current application neither dispatches it nor provides a compatible combined paired-reuse path. Turning on its flag would not implement B11 correctly.

Source inspection used pinned runtime `f12037fa8e97ebc08e9e3edfd2de528ed1772a4b` and SDK reference `a6efab966b7c3b272da0461578eb56ac61c7cbff`. See the [CGNS paper](https://cwyman.org/papers/hpg26_compatibleNeighborSelection.pdf) and the retained [PT++ audit](PTPP_AUDIT.md) for the distinction between supplied code and application activation.

## Concrete integration requirements

| Boundary | Current application | Required implementation and acceptance evidence |
|---|---|---|
| Selector dispatch | No CGNS producer; heuristic flag explicitly rejected | Port the supplied geometry-only selector wrapper and surface callback; dispatch before consumption; prove actual dispatch and non-default selected coordinates |
| Buffer ownership | Bindingu18 is used by B10's RGB vector-shading output | Allocate a distinct four-packed-coordinate-per-pixel CGNS buffer, keep RGB radiance separate, update every producer/consumer binding and barrier; verify odd extents and reset behavior |
| Selection heuristic | SDK scores normals and world positions, independent of radiance reservoirs | Preserve geometry-only input, coordinate packing, invalid sentinel, candidate bounds and RNG stream; do not introduce sample luminance/confidence into its independence argument |
| Reciprocal pairing | B10 shares two directed shifts across an involutive pair | Guided choices need not be reciprocal. Implement a derived reciprocal guided construction or a general directed-edge schedule with valid normalization; retain the unguided B10 control |
| Replay scheduling | Queue owns one source per pixel for a reciprocal pair | Re-derive edge ownership/capacity/dependencies for the selected topology; exact queued-versus-direct output/history oracles must remain strict |
| Evaluation | No active B11 measurements | Room, original Convergence and Kitchen; raw HDR/reference error, convergence and motion/disocclusion checks; repeated uncapped timings including selector, buffers, barriers and all reuse work |

The supplied selector examines up to32 disk candidates within radius50, uses geometry compatibility weights and stores up to four independently selected coordinates. Its early-stop rule and invalid-neighbor handling are part of the pinned implementation. These directed picks cannot simply replace B10's reciprocal partner lookup: if pixelp choosesq, q need not choosep. The pair-owned inverse shift and normalization then lose the topology assumed by the current pilot.

## Execution order

1. Complete and freeze B10's remaining mechanisms and strict versus deliberately biased presets.
2. Separate vector-radiance and neighbor-selection storage; validate the supplied selector independently as a diagnostic ablation, without calling it cumulative B11.
3. Derive and test the combined guided topology, conditional normalization and queue schedule. Preserve own-sample support, rejected/empty candidates and boundary behavior.
4. Validate GPU activation and full history, then run the extended matched B10/B11 comparison. Keep regressions and uncertainty visible; publish full B11 only after those gates.

A mutual-pick filter or symmetric compatibility gate could produce a reciprocal research candidate, but it would differ from the paper's independent weighted selector. Such a candidate needs its own explicit label, derivation and measurements. It is not an already implemented B11 feature.

The current queue-history checkpoint is reported in [B10 queue validation](B10_QUEUE_HISTORY.md). B12's stochastic pairwise MIS remains a later cumulative stage; it must not be silently substituted while labelling this implementation B11.

Changelog: 2026-10-30 — documented the actual buffer collision, selector producer gap and reciprocal-topology acceptance requirements.
