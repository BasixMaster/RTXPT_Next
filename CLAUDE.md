# Project instructions

Follow AGENTS.md and Docs/Research. RTXPT1.9 is the baseline; B1 at7010bb4 implements runtime3.1 API migration on existing DI/GI only. B2 ReSTIR PT is an active development integration; B3 PT++ extensions remain planned. See B1_RESULTS.md for measured scope.

B2 ReSTIR PT integration is in progress with scoped static opaque HDR validation and cap-verified native-control timings; it is not promoted. See Docs/Research/B2_RESULTS.md for the current measured checkpoint. B3 is reserved for PT++ changes. Read Docs/Research/B2_IMPLEMENTATION.md and Benchmarks/versions.json; preserve immutable B0/B1 and reject overlapping GI/PT lighting without a valid partition/MIS. Future benchmarks require explicit uncapped renderer controls plus recorded driver/external-cap coverage.
