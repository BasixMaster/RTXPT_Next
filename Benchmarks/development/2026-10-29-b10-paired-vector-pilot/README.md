# Adjacent reciprocal-pair/vector GPU pilot

See [the scoped report](../../../Docs/Research/B10_PAIRED_PILOT.md).

This is partial B10 development with GI reuse off, one adjacent paired neighbor and separate vector shading. No complete PT++, general unbiasedness, accepted total timing or speedup claim.

Raw .pfm.gz and .pt.bin.gz decompress directly to their original bytes. Metadata/counters accompany the packed64-byte reservoirs. The two64-frame sequences retain raw frame hashes/official FLIP values and separately labelled arithmetic-mean PFMs; individual raw sequences remain locally retained. Supplemental FLIP metrics for the previous B8 cohort are appended here without changing its frozen dataset.

GPU counters establish pixel ownership, the two-directed-shifts-per-pair bound and finite outputs. Empty sources retain mass and require no shift. The vector activation comparison is not a transport-mean proof. The initial spatial-h1 attempt predates dedicated counters and is excluded from this frozen cohort.

The source patch applies to db72fe0070fb7be788bf8b75e92057792cfd1026. Final artifact identity is post-cohort; earlier executables retain their own hashes. The final guard capture uses the final executable. Default controls, baseline refs, submodule pins and original scenes are preserved.

Private resource samples/host paths are removed. files.json records exact exported bytes.
