/*
* Copyright (c) 2025, NVIDIA CORPORATION.  All rights reserved.
*
* NVIDIA CORPORATION and its licensors retain all intellectual property
* and proprietary rights in and to this software, related documentation
* and any modifications thereto.  Any use, reproduction, disclosure or
* distribution of this software and related documentation without an express
* license agreement from NVIDIA CORPORATION is strictly prohibited.
*/

#include "CommandLine.h"
#include <cxxopts.hpp>
#include <donut/core/log.h>
#include <filesystem>
#include <cstdio>

bool CommandLineOptions::InitFromCommandLine(int _argc, char const* const* _argv)
{
	using namespace cxxopts;
    
	try
	{
		std::filesystem::path exe_path = _argv[0];
		Options options(exe_path.filename().string(), "RTX Path Tracing is a code sample that strives to embody years of ray tracing and neural graphics research and experience. It is intended as a starting point for a path tracer integration, as a reference for various integrated SDKs, and/or for learning and experimentation.");

		bool help = false;

		options.add_options()
			("s,scene", "Preferred scene to load (.scene.json)", value(scene))
			("nonInteractive", "Indicates that RTXPT will start in non-interactive mode, disabling popups and windows that require input", value(nonInteractive))
            ("diagnosticStartupLog", "Diagnostic only: send host startup/error messages to stdout/stderr; not a benchmark mode", value(DiagnosticStartupLog))
            ("noWindow", "Not supported: rejected at startup, as there is no headless rendering path", value(noWindow))
			("d,debug", "Enables the D3D12/VK debug layer and NVRHI validation layer", value(debug))
			("gpuValidation", "Enables D3D12 GPU-based validation and debug layers (slow)", value(gpuValidation))
			("width", "Window width", value(width))
			("height", "Window height", value(height))
			("f,fullscreen", "run in fullscreen mode", value(fullscreen))
			("borderless", "Window without decorations; unlike a regular window it is not clamped to the screen size, so a render larger than the display is possible", value(borderless))
			("a,adapter", "--adapter must be followed by a string used to match the preferred adapter, e.g --adapter NVIDIA or --adapter RTX", value(adapter))
			("h,help", "Print the help message", value(help))
			("d3d12", "Render using DirectX 12 (default)")
			("vk", "Render using Vulkan", value(useVulkan))
            ("stopAnimations", "Always start the scene with animations disabled", value(stopAnimations))
            ("noSER", "Disable Shader Execution Reordering", value(disableSER))
            ("adapterIndex", "--adapterIndex must be followed by a number used to identify the preferred adapter index, e.g '--adapterIndex 0' or '--adapterIndex 1'; default is -1 (automatic)", value(adapterIndex))
            ("captureWarmupFrames", "Simple-capture history warmup frames, 1..4096", value(CaptureWarmupFrames))
            ("captureSimple", "Trigger simple screenshot capture with default warmup; use capturePath to specify output file.", value(captureSimple))
            ("captureSequence", "Trigger sequence capture; use capturePath to specify output file, sequenceWarmupTime, sequenceStartTime, sequenceFPS and sequenceFrames to control.", value(captureSequence))
            ("capturePath", "Specify output file or path for various capture commands.", value(capturePath))
            ("captureSuffix", "Optional suffix for captured file names, e.g. 'B' turns frame.png into frame_B.png (and sequence frame_000.png into frame_000_B.png).", value(captureSuffix))
            ("sequenceWarmupStart", "Scene time to start warmup when using captureSequence.", value(sequenceWarmupStart))
            ("sequenceRecordStart", "Scene time to start recording when using captureSequence.", value(sequenceRecordStart))
            ("sequenceFPS", "Fixed FPS at which to run when using captureSequence.", value(sequenceFPS))
            ("sequenceFrameCount", "Number of frames to record when using captureSequence", value(sequenceFrameCount))

            ("useNEE", "Enable/disable NEE (on by default)", value(UseNEE))
            ("NEEType", "Set NEE type: 0 - uniform sampling; 1 - power-based sampling, 2 (default) - NEE-AT", value(NEEType))
            ("useReSTIRDI", "Enable/disable ReSTIR DI", value(UseReSTIRDI))
            ("useReSTIRGI", "Enable/disable ReSTIR GI", value(UseReSTIRGI))
            ("useReSTIRPT", "Experimental ReSTIR PT indirect transport; supersedes GI, uses one plane without PSR/cache/subsampling", value(UseReSTIRPT))
            ("maxBounces", "Override total bounce cap for validation (1..32)", value(OverrideMaxBounces))
            ("maxDiffuseBounces", "Override diffuse bounce cap for validation (0..32)", value(OverrideMaxDiffuseBounces))
            ("ptReconnectionMode", "PT reconnectibility: 0 fixed threshold (B2), 1 footprint (B3)", value(PTReconnectionMode))
            ("ptRouletteProbability", "Initial-only PT roulette survival probability: 0 off, [0.1,1] on; replay never roulettes", value(PTRouletteProbability))
            ("ptFixedSpatialSamples", "Diagnostic: fixed PT ordinary/boosted neighbor count (1..32)", value(PTFixedSpatialSamples))
            ("ptDisableAgeRejectionValidation", "Diagnostic: disable PT age-based history rejection, retaining history mass cap", value(PTDisableAgeRejectionValidation))
            ("ptUnifiedRISCandidates", "Development: finite unified RIS candidates1..32 with supplemental PSS UCW; requires unified MIS;0 keeps M1 control", value(PTUnifiedRISCandidates))
            ("ptUnifiedMISValidation", "Development: finite M1 unified BSDF/NEE MIS, full-prefix replay only", value(PTUnifiedMISValidation))
            ("ptUnifiedFiniteNEEValidation", "Development: one PT reservoir for primary+indirect finite-light NEE; no standalone DI/GI, not full PT++ MIS", value(PTUnifiedFiniteNEEValidation))
            ("ptReplayOnlyValidation", "Diagnostic: suppress mid-path PT reconnection; preserve terminal-light reconnection", value(PTReplayOnlyValidation))
            ("ptExtendedSceneValidation", "Development: allow original-scene transport with full-prefix replay and native diffuse accounting", value(PTExtendedSceneValidation))
            ("b8InitialGIValidation", "Development disjoint DI/GI-short/PT-long partition", value(B8InitialGIValidation))
            ("b8GIReuseMode", "B8 NVIDIA non-directional GI: -1 legacy control,0 initial,1 temporal,2 spatial,3 both", value(B8GIReuseMode))
            ("b8Component", "Development component:0 sum,1 native,2 DI,3 GI-short,4 PT-long", value(B8Component))
            ("b8ValidationStage", "GI-short development:0 initial,1 DI/PT reuse,2 footprint/roulette,3 extended replay/roulette", value(B8ValidationStage))
            ("ptPairedSpatialValidation", "Development: pair-owned adjacent reciprocal shifts and vector shading", value(PTPairedSpatialValidation))
            ("ptGaussianPairingValidation", "Development: resident Gaussian reciprocal tables and frame transforms", value(PTGaussianPairingValidation))
            ("ptReplayCompactionValidation", "Development: compact paired spatial replay queue; diagnostics compare same-frame direct control", value(PTReplayCompactionValidation))
            ("ptDuplicationHistoryValidation", "Development: deliberately biased PT duplication-based temporal history reduction", value(PTDuplicationHistoryValidation))
            ("strictDIValidation", "DI validation: disable boiling rejection and naive-neighbor discount; retain raytraced bias correction", value(StrictDIValidation))
            ("diLightMode", "DI local light proposals: 0 uniform, 1 power RIS, 2 ReGIR RIS", value(OverrideDILightMode))
            ("diBrdfSamples", "DI initial BRDF candidate count (0..32)", value(OverrideDIBrdfSamples))
            ("captureNativeRadiance", "HDR diagnostic: save native radiance before DI/GI/PT additions", value(CaptureNativeRadiance))
            ("restirDIMode", "DI reuse override: 0 initial only, 1 temporal, 2 spatial, 3 both", value(OverrideReSTIRDIMode))
            ("neeMIS", "Native NEE MIS: 0 exact, 1 auto, 2 approximate", value(OverrideNEEMIS))
            ("preserveGBufferThroughput", "Diagnostic: preserve prefix throughput above1; 0 legacy clamp, 1 no upper clamp", value(PreserveGBufferThroughput))
            ("captureGBufferThroughput", "With HDR, save packed dominant-prefix throughput texture", value(CaptureGBufferThroughput))
            ("roundedGBufferMaterials", "Diagnostic: rounded material GBuffer packing; default retains legacy truncation", value(RoundedGBufferMaterials))
            ("environmentDiffuseMip", "Explicit native environment diffuse MIP (0..16); 0 for matched unfiltered validation, omitted preserves defaults", value(OverrideEnvironmentDiffuseMip))
            ("restirPTMode", "PT resampling: 0 initial only, 1 temporal, 2 spatial, 3 both", value(ReSTIRPTMode))
            ("samplingSeed", "Validation scramble seed; zero retains the original random streams", value(SamplingSeed))
            ("referencePixelCenter", "Reference rays use pixel centers, matching raw realtime AA0", value(ReferencePixelCenter))
            ("capturePTReservoirs", "With HDR capture, export packed PT reservoir diagnostics (large, synchronizes GPU)", value(CapturePTReservoirs))
            ("captureLinearHDR", "Write stored linear radiance as PFM alongside screenshots (raw AA0 only)", value(CaptureLinearHDR))
            ("benchmarkUncapped", "Force app VSync/FPS/Reflex caps and frame generation off; render unfocused (external caps require separate audit)", value(BenchmarkUncapped))
            ("realtimeSamplesPerPixel", "Number of spp in realtime mode",     value(RealtimeSamplesPerPixel))
            ("referenceSamplesPerPixel", "Number of spp in reference mode", value(ReferenceSamplesPerPixel))
            ("standaloneDenoiser", "Enable/disable standalone denoiser active when DLSS-RR not enabled (on by default)", value(StandaloneDenoiser))
            ("realtimeAA", "Set realtime AA mode: 0 - none; 1 - TAA; 2 - DLSS; 3 - DLSS-RR (AA+denoiser, default)", value(RealtimeAA))
            ("overrideToRealtimeMode", "Override scene default", value(OverrideToRealtimeMode))
            ("overrideToReferenceMode", "Override scene default", value(OverrideToReferenceMode))
            ("overrideAutoexposureOff", "Override scene default", value(OverrideAutoexposureOff))
            ("overrideExposureOffset", "Override scene default", value(OverrideExposureOffset))
            ("disableFireflyFilters", "Override realtime and reference mode firefly filters to off", value(DisableFireflyFilters))
            ("disablePostProcessFilters", "Disable post-process filters like bloom", value(DisablePostProcessFilters))
            ("asyncPrefix", "Async compute prefix (UI: AsyncPrefix); on by default where supported, --asyncPrefix=false turns it off", value(AsyncPrefix))
            ("overrideRadianceCacheMode", "Override radiance cache mode: 0 - disabled, 1 - SHaRC", value(OverrideRadianceCacheMode))
            ("overrideSubSamplingMode", "Override realtime sub-sampling (sub-1spp) rate: 0 - disabled, 1 - three quarters, 2 - half, 3 - quarter", value(OverrideSubSamplingMode))
            ("subSamplingPattern", "Realtime sub-sampling pattern: 0 - random per block, 1 - stochastic (compacted), 2 - block stratified, 3 - Sobol (0,2) per block (default)", value(SubSamplingPattern))
            ("subSamplingBlockSize", "Block size N for the block stratified and Sobol sub-sampling patterns: 4, 8 (default) or 16", value(SubSamplingBlockSize))
            ("overrideDLSSMode", "Force the DLSS / DLSS-RR mode (UI changes are ignored): 1 - performance, 2 - balanced, 3 - quality, 4 - ultra performance, 5 - ultra quality, 6 - DLAA", value(OverrideDLSSMode))
            ("perfLog", "Append per-frame GPU timings of the path tracing passes (build, sub-sampling compaction, fill) to this CSV file", value(PerfLogPath))
            ("cameraPosDirUp", "Specify camera location to set after loading the scene; format is 9 comma separated values; can be obtained via UI Camera->Copy TO clipboard", value(cameraPosDirUp))
            ("propShowTags", "To show special props only if tag found in list (comma separated values)", value(PropShowTags))
            ("propCameraAttach", "After load, try to attach camera to the named prop", value(PropCameraAttach))            
            ;

		int argc = _argc;
		char const* const* argv = _argv;
		options.parse(argc, argv);
        if (DiagnosticStartupLog)
        {
            donut::log::EnableOutputToConsole(true);
            if (nonInteractive) donut::log::EnableOutputToMessageBox(false);
            std::fprintf(stderr, "STARTUP_DIAGNOSTICS enabled=1 benchmarkEligible=0\n");
            std::fflush(stderr);
        }
        if (PreserveGBufferThroughput < 0 || PreserveGBufferThroughput > 1 ||
            (CaptureGBufferThroughput && !CaptureLinearHDR))
        {
            if (nonInteractive)
            {
                donut::log::EnableOutputToMessageBox(false);
                donut::log::EnableOutputToConsole(true);
            }
            donut::log::error("preserveGBufferThroughput must be0/1; captureGBufferThroughput requires captureLinearHDR");
            return false;
        }
        if (RoundedGBufferMaterials < 0 || RoundedGBufferMaterials > 1)
        {
            // Validation occurs before SampleBaseApp applies noninteractive logging.
            if (nonInteractive)
            {
                donut::log::EnableOutputToMessageBox(false);
                donut::log::EnableOutputToConsole(true);
            }
            donut::log::error("roundedGBufferMaterials must be 0 or 1");
            return false;
        }

		if (help)
		{
			std::string helpMessage = options.help();
			donut::log::info("%s", helpMessage.c_str());
			return false;
		}

		return true;
	}
	catch (const exceptions::exception& e)
	{
		std::string errorMessage = e.what();
		donut::log::error("%s", errorMessage.c_str());
		return false;
	}
}
