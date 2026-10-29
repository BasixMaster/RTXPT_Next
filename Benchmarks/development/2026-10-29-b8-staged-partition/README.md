# B8 staged partition and limited PT++ development evidence

Read [the implementation report](../../../Docs/Research/B8_STAGED_IMPLEMENTATION.md).

- Initial GI-short remains fixed outgoing; no GI temporal/spatial reuse acceptance.
- Raw .pfm.gz files decompress directly to original linear RGB PFM captures; same-frame cumulative stages are named explicitly.
- Packed .pt.bin.gz is the pinned64-byte RTXDI reservoir ABI, with metadata and counters alongside it.
- room-initial-quality.json contains one low-resolution64-frame sequence per configuration, not replicated final benchmark results. Arithmetic means are separate .pfm.gz artifacts; individual-frame hashes remain in run manifests, and raw sequences remain locally retained.
- Convergence retains its original failed verifier status plus a separate corrected offline revalidation. No image was changed.
- final-renderer-artifacts.json is a post-cohort snapshot; earlier executable phases were not pre-frozen. The renderer patch applies to e10fc3c; standalone Python oracle sources are versioned in Benchmarks/tools.
- The first static-clock sequence attempt was stopped/excluded; it has no accepted images or timing. The capture clock was repaired before the completed sequences.
- No GPU timing/FPS, full canonical B8/B9/B10, general scene acceptance or brightness improvement is claimed.
- Private resource samples and workspace-specific absolute paths were removed. files.json records exact exported bytes.
