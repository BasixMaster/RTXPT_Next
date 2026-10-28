# Diffuse-budget algebra: inactive research helper

This helper is **not connected to B2 rendering**. B2's tested subset requires a
nonbinding diffuse-bounce limit. It does not provide a suffix metadata buffer,
replace RTXDI runtime headers, or establish correctness for a binding cutoff.
The work below is not a PT++ paper mechanism or a B3 activation claim.

## Why a copied diffuse counter is insufficient

Native RTXPT `GenerateScatterRay` charges a scatter when its selected BSDF lobe
is diffuse or roughness exceeds 0.25. Diffuse transmission at odd source vertex
indices is exempt. A hybrid shift changes its prefix and the directions at the
reconnection boundary; a cached source-path count cannot simply be reused.

Moreover, `FalcorBSDF::sample` returns a selected-component throughput while
its continuous `pdf` is a mixture PDF. Native component choices are latent
variables, and the binding cutoff depends on them. Carrying an arbitrary
component label across a new connection requires defining its joint sampling
measure and corresponding weights. A random post-reconnection drop or an
uncorrected scalar prefix counter does not solve that problem.

## Finite-path marginalization

For a fixed geometric path in one common measure, let f(j,l,c) be component l's nonnegative BSDF times
cosine contribution at source vertex j, color channel c. Let b(j,l) be 1 when
the native classification charges that component, otherwise 0. For each RGB
channel define:

    p(j,c) = sum_l b(j,l) f(j,l,c) / sum_l f(j,l,c)
    G_c(z) = product_j ((1-p(j,c)) + p(j,c) z)
    S_D,c = sum_{k=0}^D coefficient(G_c, k)

Zero total BSDF contribution means the corresponding full-path channel is
zero; its p value may be set to zero. The component proposal probabilities are
**not** the p values in this expression. Native component estimators contain
f_component / q_component, so their proposal masses cancel when summing the
conditional component transport. RGB contribution fractions remain. The
Discrete delta atoms and continuous directional densities must be treated in
their respective measures before these fractions are formed; the finite
oracle does not supply that material-domain integration. The
finite-domain oracle explicitly enumerates the component combinations and
retains proposal probabilities to test this cancellation.

The marginal target is full-mixture RGB path contribution multiplied by S_D.
One potential implementation would generate untruncated geometric paths and
apply this target consistently in initial RIS, resampling, and inverse MIS.
This is a proposed estimator transformation, not a validated renderer change.

## Last-edge convention

For a path whose light endpoint has index L, count only scattering vertices
1 through L-2. Native RTXPT permits the emitted-light hit immediately after a
scatter first crosses the diffuse limit, then stops there before another NEE
or continuation. For NEE, the final connection from vertex L-1 to the light is
not a generated continuation scatter. Charging that final edge again would
remove transport that native RTXPT retains.

## Conditions for future integration

A shifted prefix can be composed with an unchanged suffix using polynomial
convolution. Nonnegative counts make truncation above D exact: discarded high
degrees cannot return to the accepted range. The reconnection boundary still
requires reevaluating both changed directional component fractions. Caching
only the suffix polynomial is insufficient; the reconnection surface/material
and outgoing direction must remain available with compatible history rules.

A future implementation must carry selected-candidate metadata through initial
RIS and every reservoir combine, preserve original metadata during inverse-MIS
queries, and update the target and contribution weight together. Its memory,
register, bandwidth and convolution costs require measurement. The current
HLSL helper's maximum degree96 follows the UI's current total-bounce bound;
it is not a claim that a97-element RGB working array is performant.

The six CPU tests check finite-domain algebra, cached-suffix composition,
RGB/component weighting, charge boundaries and truncation. A separate DXC
typecheck checks the helper's shader syntax. Neither check executes a GPU
path tracer, proves dynamic-scene integration, or validates a complete B2.
