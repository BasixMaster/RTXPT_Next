/*
* Copyright (c) 2025, NVIDIA CORPORATION.  All rights reserved.
*
* NVIDIA CORPORATION and its licensors retain all intellectual property
* and proprietary rights in and to this software, related documentation
* and any modifications thereto.  Any use, reproduction, disclosure or
* distribution of this software and related documentation without an express
* license agreement from NVIDIA CORPORATION is strictly prohibited.
*/

#pragma once

#include <string>
#include <optional>

struct CommandLineOptions
{
	std::string scene;
	bool nonInteractive = false;
    bool DiagnosticStartupLog = false; // Opt-in host diagnostics; exclude from benchmark cohorts.
	bool noWindow = false;
	bool debug = false;
	bool gpuValidation = false;
	uint32_t width = 1920;
	uint32_t height = 1080;
	bool fullscreen = false;
	bool borderless = false;
	std::string adapter;
    int adapterIndex = -1;
	bool useVulkan = false;
    bool stopAnimations = false;
	bool disableSER = false;

    std::string capturePath = "";
    std::string captureSuffix = "";
    bool captureSimple = false;
    int CaptureWarmupFrames = -1; // -1 keeps the existing 64-frame default.
    bool CaptureLinearHDR = false;
    bool CapturePTReservoirs = false;
    bool ReferencePixelCenter = false;
    uint32_t SamplingSeed = 0;
    bool captureSequence = false;
    float sequenceWarmupStart = 0;
    float sequenceRecordStart = 0;
    float sequenceFPS = 60.0f;
    int sequenceFrameCount = 0;

    std::string cameraPosDirUp = "";

    int  UseNEE                     = 1;
    int  NEEType                    = 2;
    int  UseReSTIRDI                = false;
    int  UseReSTIRGI                = true;
    int  UseReSTIRPT                = false;
    bool BenchmarkUncapped         = false;
    int OverrideMaxBounces         = -1;
    int OverrideMaxDiffuseBounces  = -1;
    int ReSTIRPTMode               = 3;
    int OverrideReSTIRDIMode       = -1;
    int OverrideNEEMIS            = -1;
    int OverrideEnvironmentDiffuseMip = -1;
    int PreserveGBufferThroughput = 0; // Opt-in upper-clamp ablation; legacy default0.
    bool CaptureGBufferThroughput = false; // Packed texture diagnostic, with HDR only.
    int RoundedGBufferMaterials = 0; // Opt-in precision ablation; legacy packing remains default.
    int OverrideDILightMode       = -1;
    int OverrideDIBrdfSamples     = -1;
    bool CaptureNativeRadiance    = false;
    int  RealtimeSamplesPerPixel    = 1;
    int  ReferenceSamplesPerPixel   = 4096;
    int  StandaloneDenoiser         = true;
    int  RealtimeAA                 = 3;

    bool OverrideToRealtimeMode     = false;
    bool OverrideToReferenceMode    = false;

    bool OverrideAutoexposureOff    = false;
    float OverrideExposureOffset    = FLT_MAX;
    
    int PTReconnectionMode = -1; // -1 preserves B2; 0 fixed, 1 footprint.
    float PTRouletteProbability = 0.0f;
    int PTFixedSpatialSamples      = -1;
    bool PTDisableAgeRejectionValidation = false;
    int PTUnifiedRISCandidates = 0; // 0 preserves verified M1 mixed-measure control; 1..32 explicit PSS RIS.
    bool PTUnifiedMISValidation = false; // Finite M1 complementary BSDF/NEE MIS, full-prefix replay.
    bool PTUnifiedFiniteNEEValidation = false; // Opt-in finite-light NEE-only unified tree; not full paper MIS.
    bool PTReplayOnlyValidation    = false;
    bool B8InitialGIValidation = false;
    int B8GIReuseMode = -1; // -1 preserves initial-only control; 0..3 opts into NVIDIA GI approximation.
    int B8ValidationStage = 0; // 0 initial-only, 1 DI/PT reuse, 2 footprint/roulette,3 extended replay/roulette; GI mode is selected separately (stage3 requiresGI3).
    bool PTPairedSpatialValidation = false; // Adjacent reciprocal-pair/vector pilot, not full B10.
    bool PTGaussianPairingValidation = false; // Three resident tables, one per frame; not simultaneous three-neighbor reuse.
    bool PTDuplicationHistoryValidation = false; // Deliberately biased temporal history cap; opt-in development only.
    bool PTReplayCompactionValidation = false; // Opt-in queue schedule; same-frame direct oracle when reservoir diagnostics are captured.
    int B8Component = 0; // 0 sum, 1 native, 2 DI, 3 GI-short, 4 PT-long.
    bool PTExtendedSceneValidation = false; // Replay-first diagnostic; requires explicit opt-in.
    bool StrictDIValidation        = false;
    bool DisableFireflyFilters      = false;
    bool DisablePostProcessFilters  = false;
    bool AsyncPrefix                = true;

    int  OverrideRadianceCacheMode  = -1;   // -1 keeps the default

    int  OverrideSubSamplingMode    = -1;   // -1 keeps the performance preset's; 0 - disabled, 1 - three quarters, 2 - half, 3 - quarter
    int  SubSamplingPattern         = 3;    // SubSamplingPattern in SampleUI.h
    int  SubSamplingBlockSize       = 8;    // N for SubSamplingPattern::BlockStratified and ::SobolBlock

    int  OverrideDLSSMode           = -1;   // -1 keeps the preset's / UI's; otherwise forces StreamlineInterface::DLSSMode every frame
    std::string PerfLogPath         = "";   // if set, per-frame GPU timings of the path tracing passes are appended there as CSV

    std::string PropShowTags        = "";
    std::string PropCameraAttach    = "";

	CommandLineOptions(){}

	bool InitFromCommandLine(int argc, char const* const* argv);
};
