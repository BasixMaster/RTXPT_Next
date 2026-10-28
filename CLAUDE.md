# Project instructions

Follow AGENTS.md and Docs/Research. RTXPT1.9 is the baseline; B1 at7010bb4 implements runtime3.1 API migration on existing DI/GI only. B2+ and ReSTIR PT integration remain planned. See B1_RESULTS.md for measured scope.

B2 ReSTIR PT integration is in progress, not yet promoted or benchmarked. B3 is reserved for PT++ changes. Read Docs/Research/B2_IMPLEMENTATION.md and Benchmarks/versions.json; preserve immutable B0/B1 and reject overlapping GI/PT lighting without a valid partition/MIS. Future benchmarks require explicit uncapped renderer controls plus recorded driver/external-cap coverage.
