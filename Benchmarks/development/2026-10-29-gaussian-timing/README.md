# Gaussian versus adjacent development timing

18 process-filtered PresentMon2.6.0 runs, three repeats per policy and scene;45s warmup plus30s capture. Last600 Original/NotSet rows, final16 excluded. All runs verify frozen source/executable/682shader-cache identities, no image writes, no reported trace loss, uncapped application/owned NVIDIA profile/read-only RTSS checks and verified profile restoration. The renderer source stayed at1f64042 throughout.

Per-process GPU busy and CPU cadence are separate metrics; neither inverse GPU busy nor display cadence is renderer FPS. Three process repetitions are exploratory, not general acceptance. Gaussian and adjacent are one-neighbor pair/vector schedules with GI initial only. No complete B10, simultaneous multi-neighbor reuse or replay-queue implementation is claimed. Quality is retained in the separate Gaussian cohort and the new adjacent original-scene snapshots.

Private host resource samples and driver recovery state are excluded. Presentation-availability probe and earlier no-event failures are not benchmark results. See Docs/Research/B10_GAUSSIAN_PAIRING.md for scope and interpretation.
