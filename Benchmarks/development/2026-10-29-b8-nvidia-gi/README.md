# B8: NVIDIA GI approximation checkpoint

This is an experimental configuration, not a promotion of canonical B8. The disjoint contribution split assigns primary direct lighting to DI, two-scattering indirect lighting to GI-short and longer indirect paths to ReSTIR PT. NVIDIA GI uses non-directional secondary RGB and the inherited approximate bias controls. Initial-only GI remains the control. No brightness multiplier, scene material replacement or reference adjustment is applied.

Evidence: eight focused Room gates, six full-resolution snapshots, six64-frame static quality sequences and18uncapped timing processes. Room uses640x360 cap4/4; original Convergence/Kitchen use1280x720 cap14/2. Quality is mixed. See Docs/Research/B8_STAGED_IMPLEMENTATION.md for measurements, limitations and convergence curves. Large raw sequences/reservoirs remain local with exact payload/frame hashes; a small GI snapshot and reference inputs are included.

## Reproduce

From the repository root, use the portable tools with a Release Rtxpt.exe:

- `Benchmarks/tools/run_b8_gi_approximation.py --exe bin/Rtxpt.exe --output <new-work-folder>` runs focused GPU gates. Add `--full-scenes` for the six full-resolution snapshots.
- `Benchmarks/tools/run_b8_gi_sequences.py --exe bin/Rtxpt.exe --output <new-sequences-folder>` records the six64-frame sequences with animations stopped.
- `Benchmarks/tools/evaluate_b8_gi_sequences.py --help` evaluates sequences against the frozen reference hashes/HDR-FLIP policy in this directory's `quality.json`. It accepts explicit native reference directories and an optional local FLIP module directory. Use official flip-evaluator1.7. The portable evaluator exactly reproduced both retained Room group results in an offline check.
- `Benchmarks/tools/plot_b8_gi_convergence.py --quality <quality.json> --output <figure.svg>` plots the chronological mean-image error curves using Matplotlib; its portable command was exercised.
- `Benchmarks/tools/run_timed.py --help` exposes the same GI option for uncapped measurements. Exact launch arguments, profile audits/restoration and PresentMon CSVs are in `timing-evidence/`. GPU diagnostic captures are separate from timing.

Room's2048spp PFM is gzip-compressed in `references/room`; decompress it alongside its PNG before evaluation. Original4096spp references and PNGs are retained in `../2026-10-29-finite-shift-guard/references/original-resolution/<scene>/reference4096`. Frozen policy hashes reject substituted references. The renderer source patch reconstructs the application changes on the recorded source base; component gitlinks/licenses are unchanged.

NVIDIA cap recovery state and private host resource telemetry are excluded. GPU busy is not complete frame latency/FPS;64-frame chronological averages are not equal-time or independent-seed convergence. The earlier GI-off DI brightness residual remains a separate deferred investigation.
