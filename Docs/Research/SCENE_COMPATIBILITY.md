**Current project context (2026-10-28):** RTXPT1.9 with its original scenes is the immutable B0 baseline. B1 at `7010bb4cda80788eb13cd9ee6143eb2f52a5b6ee` applies the RTXDI3.1 runtime/API migration to the existing DI/GI path. It does not add a ReSTIR PT renderer or activate PT++/CGNS features. `External/RTXDI-SDK` remains reference-only. See [B1 results](B1_RESULTS.md) for measured scope and limitations. B2+ remain planned.

# Scene compatibility: RTXDI3.1 and RTXPT1.9

## Practical answer

The RTXDI runtime has no scene-file format; the application supplies its scene, materials, lights and ray-tracing callbacks. RTXDI FullSample and RTXPT1.9 both use Donut and glTF-based assets with `.scene.json` scene descriptions. That makes a common geometry/texture baseline plausible, but does not establish drop-in material or rendering parity.

RTXDI FullSample selects Arcade.gltf, CornellBox.gltf and Bistro `.scene.json` variants in `Samples/FullSample/Source/App/SceneRenderer.cpp:167–183`. Its path selection uses predefined scene assets. RTXPT's README documents glTF2.0 plus a subset of extensions and `--scene` `.scene.json` loading. Its `Rtxpt/SampleCommon/ExtendedScene.cpp` supplies custom environment/point/spot light types, proxy-mesh light properties and material-domain handling; it warns that older scene material properties can be missing. Common file extensions do not make these custom fields equivalent.

## Compatibility levels

| Level | Current evidence | Required next check |
|---|---|---|
| Common meshes and textures | Shared glTF/Donut ecosystem; actual loaders inspected | Verify coordinate units, transforms, normals/tangents, texture color space and paths on one common asset. |
| Scene graph, instances and cameras | Similar scene descriptions, different application setup | Compare hierarchy, camera projection/exposure, clipping, instance IDs and animation frames. |
| Materials and lights | RTXPT has renderer-specific scene extensions | Map roughness/metalness/IOR, transmission/absorption, alpha modes, emission, environment scale and light units. |
| Runtime rendering features | Different pass graphs, caches, reconstruction and settings | Match transport/bounce limits and disable differing approximations before reference comparison. |
| Production scene parity | Not tested in this task | Shared scene manifest, loader warnings and raw high-spp image comparisons required. |

## Roadmap work package

Add a general scene-path option to the fork's application before claiming arbitrary RTXPT scene loading. Start with a common Cornell-style glTF scene and then a textured/emissive scene, mirror/rough-glass scene and animated scene. Use a scene-feature manifest and explicit unsupported-field diagnostics. Preserve original assets and licenses; record conversions and settings separately. Test geometry/lighting parity in raw outputs before denoising. Reusing RTXPT assets through the original root `Assets` does not automatically mount them in RTXDI's virtual filesystem.

A longer-term renderer adapter can reuse RTXPT's own loader/material model while consuming the3.1 PT runtime. That is often a better route to RTXPT scene fidelity than extending FullSample to duplicate all RTXPT scene semantics; choose based on the initial scene-conversion results.

Sources: [RTXDI FullSample loader](https://github.com/NVIDIA-RTX/RTXDI/blob/a6efab966b7c3b272da0461578eb56ac61c7cbff/Samples/FullSample/Source/App/SceneRenderer.cpp#L167), [RTXPT README](https://github.com/NVIDIA-RTX/RTXPT/blob/303b408ab81790a5051abd7573830b7a4112eb8e/README.md), [RTXPT scene extensions](https://github.com/NVIDIA-RTX/RTXPT/blob/303b408ab81790a5051abd7573830b7a4112eb8e/Rtxpt/SampleCommon/ExtendedScene.cpp).

## Summary and lessons learned

Share assets first and verify semantics explicitly. File-format overlap is useful evidence for a porting path; only an actual scene and material comparison establishes parity. This deliverable inspected source loaders but did not load or render either scene set.
