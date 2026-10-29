# Registered zero-radiance environment fixture

`opaque-room-registered-env.scene.json` is a separately identified comparison
fixture. It preserves the original `opaque-room.scene.json` model, materials and
camera and adds one explicitly registered `EnvironmentLight` with `intensity:0`.
The original scene is preserved byte for byte.

The light references the existing pinned Assets texture
`EnvironmentMaps/20060807_wells6_hd.hdr`. Its nonblack unscaled importance map
avoids an undefined all-black sampling density; runtime intensity makes its
emitted radiance zero. No HDR texture is copied into this directory. Asset and
texture terms remain those of the pinned Assets repository.

This fixture addresses a comparison constraint without patching the original
native renderer: its light preparation assumes that an available environment
map has a corresponding registered scene light. An absent record can underflow
the ordinary infinite-light count. A real zero-intensity record supplies that
registration while preserving zero environment radiance. The source audit is
documented in `Docs/Research/B8_PARTITION_DESIGN.md`; finite GPU output and
effective intensity still require a preflight before measurements are accepted.

Use `intensity`, which the original loader reads. `radianceScale` is ignored by
that loader and cannot establish a zero-radiance environment. Keep this fixture's
identity beside every result; do not silently relabel older no-environment room
captures as measurements of this scene.

The fixture is not a substitute for original Convergence or Kitchen. Their
materials, cameras and transport limits remain independently required coverage.
