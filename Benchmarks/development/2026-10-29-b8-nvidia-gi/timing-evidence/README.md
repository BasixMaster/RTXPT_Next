# B8 NVIDIA GI reuse timing

18 process-filtered PresentMon2.6.0 runs: three repeats per policy/scene,30s warmup and15s capture, last600 Original/NotSet rows minus16. Frozen renderer source/executable/699shader-cache files; no image writes or reported trace loss. Known app/NVIDIA/RTSS caps checked; exact-executable NVIDIA profile restored after every process. Unknown external limiters/background load remain limitations.

GPUBusy is per-process GPU engine busy, separate from CPU cadence and complete critical-path frame latency/FPS. Control bypasses GI reservoir packing/filter/blend; candidate includes these inherited approximations as well as reuse. Quality is measured separately in64-frame static sequences, not equal-time or independently replicated. No canonical promotion or brightness fitting.
