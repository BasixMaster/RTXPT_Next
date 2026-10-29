**Current project context (2026-10-29):** [Canonical B0–B10 and legacy crosswalk](VERSION_MAPPING.md) govern project labels. B0 preserves unchanged RTXPT1.9 original defaults and pins. Legacy migration `7010bb4` is not canonical B1; its native/DI/DI+GI configurations map to B3/B4/B5. The PT-only/DI+PT foundation maps to B6/B7; old-B2 checkpoint `de9fe651` is B7. The GI-off old-B3 pilot is a B7 limited-feature ablation, not B9. B8 requires valid GI/PT sharing; B9/B10 depend on it, and full remaining PT++ work belongs to B10. The SDK stays reference-only. Preserve legacy measurements/IDs; historical original-scene DI+GI rows map to B2/B5 with cap coverage unverified.

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

For a separate FullSample reproduction, generalize that sample's scene-path selection before claiming arbitrary RTXPT scene parity. The primary fork already uses RTXPT's own loader and original Assets; its B6/B7 PT adapter does not imply support for every loaded material or bounce contract. Test a common Cornell-style asset, textured/emissive scene, mirror/rough-glass and animation with explicit feature manifests. Preserve originals/licenses and label conversions separately. RTXPT Assets are not automatically mounted in the separate FullSample virtual filesystem.

The implemented app-owned PT foundation follows the RTXPT-loader/material route. Original Convergence/Kitchen still hit transmission/medium and binding diffuse-cap gates, so a successful opaque room is not original-scene support. Keep both original scenes visible in every comparison matrix; no material-edited derivative counts as their result. Cross-renderer FullSample parity remains a separate source/scene validation task.

Sources: [RTXDI FullSample loader](https://github.com/NVIDIA-RTX/RTXDI/blob/a6efab966b7c3b272da0461578eb56ac61c7cbff/Samples/FullSample/Source/App/SceneRenderer.cpp#L167), [RTXPT README](https://github.com/NVIDIA-RTX/RTXPT/blob/303b408ab81790a5051abd7573830b7a4112eb8e/README.md), [RTXPT scene extensions](https://github.com/NVIDIA-RTX/RTXPT/blob/303b408ab81790a5051abd7573830b7a4112eb8e/Rtxpt/SampleCommon/ExtendedScene.cpp).

## Summary and lessons learned

Share assets first and verify semantics explicitly. The initial comparison inspected upstream loaders without rendering parity tests. Later scoped B7 opaque rendering does not establish FullSample/RTXPT material parity or remove the original-scene gates. File-format overlap is evidence for a porting path, not proof of equivalent transport.
