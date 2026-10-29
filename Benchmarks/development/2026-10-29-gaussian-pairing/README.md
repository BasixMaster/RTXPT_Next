# Gaussian reciprocal pairing development evidence

Read [the scoped report](../../../Docs/Research/B10_GAUSSIAN_PAIRING.md).

Three resident tables, one globally transformed table/neighbor per frame; GI initial only. No simultaneous three-neighbor reuse, explicit replay queue, full PT++, canonical acceptance or timing claim. The room result is a mixed MSE/FLIP tradeoff, not a promotion.

native-pairing.bin.gz is the actual C++ producer's RG32_SINT payload (254/230/210, sigma16). Every diagnostic GPU readback matches its exact SHA256. The native source/fixture and independent validator are versioned in the repository. gpu-checks.json retains all seven ownership/finite proofs, packed-reservoir input hashes and raw counters.

Selected raw PFM.gz, the small odd-height packed reservoir and arithmetic room-mean PFMs decompress directly to original bytes. Large reservoirs, full component captures and individual raw sequences remain locally retained; their hashes are in run manifests. Reference-room2048 is fresh at640x360 cap4/4; original-scene metrics reuse the pinned4096-spp references with checked scene hash/dimensions/exposure/14/2 budgets.

flip-quality.json retains official per-frame HDR/display metrics, parameters and input hashes. Room groups have64frames each; original scenes one image each. Eight warm-up frames are not eight accumulated spp. No brightness normalization is applied.

The source patch applies to4a98c55931c2b6264ea80e03f78fe60b9a587a8c. All runs use the final executable; artifact identity is a post-cohort snapshot, not a pre-frozen timing receipt. Old baseline/source/data identities are preserved. Private resource samples and host paths are removed. files.json lists exact exported bytes.

## Reproduce

From the repository root, build the renderer with the documented toolchain, then run:

```powershell
cmake -S Benchmarks/native-pairing-test -B work/pairing-fixture
cmake --build work/pairing-fixture --config Release
ctest --test-dir work/pairing-fixture -C Release --output-on-failure
python Benchmarks/tools/run_gaussian_development.py --output work/new-gaussian-cohort
```

The runner owns a new output directory and launches the ten captures sequentially. Use `inspect_pairing_tables.py --binary <GPU .pairs.bin> --native-producer <fixture native-pairing.bin> --output <new receipt.json>` for actual byte/transform validation. `inspect_pt_reservoirs.py`, `analyze_hdr.py` and `analyze_captures.py` remain the owning raw/reservoir/official-FLIP evaluators; install their declared dependencies before requesting those metrics. A portable CMake fixture's binary output is in its build directory.

The final publication adds explicit branching around the disabled policy, avoiding unselected reads from the dummy resource. cohort-renderer-artifacts.json and cohort-renderer-source.patch.gz retain the original cohort source/cache identities. Final artifacts/source and both final guard captures are separate. The Gaussian packed PT state is byte-identical before/after this guard at the same frame index; separate-process total HDR differs beginning at DI, so no whole-image equality is claimed. This reinforces the need for same-frame scheduling oracles when implementing compaction.
