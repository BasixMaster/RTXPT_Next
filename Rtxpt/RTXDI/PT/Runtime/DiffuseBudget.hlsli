// Original RTXPT Next diffuse-budget algebra. This helper is not an activated
// transport path until initial sampling, reservoir metadata, hybrid shifts and
// inverse-MIS evaluation all carry the same polynomial state.
#ifndef RTXPT_DIFFUSE_BUDGET_HLSLI
#define RTXPT_DIFFUSE_BUDGET_HLSLI

#ifndef RTXPT_DIFFUSE_BUDGET_MAX_DEGREE
#define RTXPT_DIFFUSE_BUDGET_MAX_DEGREE 96
#endif

// RGB channels need separate polynomials: the native component-sampling
// throughput is f_component/(selection_probability*component_pdf), not the
// full-BSDF mixture estimator. Marginalizing a component-dependent bounce
// cutoff therefore uses BSDF contribution fractions, not proposal fractions.
struct RTXPT_DiffuseBudgetPolynomial
{
    float3 coefficient[RTXPT_DIFFUSE_BUDGET_MAX_DEGREE + 1];
    uint degree;
};

bool RTXPT_InitializeDiffuseBudget(uint degree, out RTXPT_DiffuseBudgetPolynomial p)
{
    p = (RTXPT_DiffuseBudgetPolynomial)0;
    if (degree > RTXPT_DIFFUSE_BUDGET_MAX_DEGREE) return false;
    p.degree = degree;
    p.coefficient[0] = 1.0f;
    return true;
}

// Multiply by (1-probability)+probability*z, retaining degrees0..D. Dropped
// higher degrees cannot return to the accepted domain because counts only
// increase. No sampler draw or geometry-dependent rejection is introduced.
bool RTXPT_AppendDiffuseBudget(inout RTXPT_DiffuseBudgetPolynomial p, float3 probability)
{
    if (any(isnan(probability)) || any(isinf(probability)) ||
        any(probability < 0.0f) || any(probability > 1.0f)) return false;
    for (int k = int(p.degree); k >= 1; --k)
        p.coefficient[k] = p.coefficient[k] * (1.0f - probability) + p.coefficient[k - 1] * probability;
    p.coefficient[0] *= 1.0f - probability;
    return true;
}

// Compose an altered prefix with an unchanged cached suffix. Both must have
// the same retained degree; accepting a mismatched truncation would silently
// erase support. The reconnection-boundary factors are appended separately.
bool RTXPT_ComposeDiffuseBudgets(RTXPT_DiffuseBudgetPolynomial prefix,
    RTXPT_DiffuseBudgetPolynomial suffix, out RTXPT_DiffuseBudgetPolynomial result)
{
    result = (RTXPT_DiffuseBudgetPolynomial)0;
    if (prefix.degree != suffix.degree || prefix.degree > RTXPT_DIFFUSE_BUDGET_MAX_DEGREE) return false;
    result.degree = prefix.degree;
    for (uint k = 0; k <= result.degree; ++k)
        for (uint j = 0; j <= k; ++j)
            result.coefficient[k] += prefix.coefficient[j] * suffix.coefficient[k - j];
    return true;
}

float3 RTXPT_DiffuseBudgetSurvival(RTXPT_DiffuseBudgetPolynomial p)
{
    float3 survival = 0;
    for (uint k = 0; k <= p.degree; ++k) survival += p.coefficient[k];
    return survival;
}

// Native GenerateScatterRay increments the counter for a diffuse lobe OR
// roughness>.25, except diffuse transmission at odd source vertex indices.
bool RTXPT_IsChargedNativeDiffuseScatter(uint lobe, float roughness, uint sourceVertex)
{
    const bool diffuseReflection = (lobe & 0x01u) != 0;
    const bool diffuseTransmission = (lobe & 0x10u) != 0;
    const bool classifiedDiffuse = diffuseReflection || diffuseTransmission || roughness > 0.25f;
    return classifiedDiffuse && !(diffuseTransmission && (sourceVertex & 1u));
}
#endif
