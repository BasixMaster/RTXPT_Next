# Source provenance and reuse terms

Checked2026-10-28. These are component-scoped source observations to guide implementation decisions; retain the actual license texts. No blanket MIT or BSD license is applied to NVIDIA SDK code or paper artifacts.

| Artifact | Revision / terms observation | Integration policy |
|---|---|---|
| [RTXDI](https://github.com/NVIDIA-RTX/RTXDI/blob/a6efab966b7c3b272da0461578eb56ac61c7cbff/LICENSE.txt) | SDK a6efab9; NVIDIA RTX SDKs LICENSE | Retain original license/notices, inspect supplement and ThirdPartyLicenses.txt. Do not relabel whole fork permissive. |
| [RTXDI runtime](https://github.com/NVIDIA-RTX/RTXDI-Library/blob/f12037fa8e97ebc08e9e3edfd2de528ed1772a4b/LICENSE.txt) | f12037f; NVIDIA RTX SDKs LICENSE | Maintain child commit provenance and distribution notices. |
| [RTXPT1.9](https://github.com/NVIDIA-RTX/RTXPT/blob/303b408ab81790a5051abd7573830b7a4112eb8e/LICENSE.txt) | 303b408; NVIDIA RTX SDKs LICENSE | Pinned source submodule; SDKs/assets/dependencies remain separately governed. |
| [CGNS reference](https://github.com/orion-junkins/ReSTIR-CGNS/blob/f28d553f3b2552b1be829feffea6d1abb1945e1d/LICENSE.md) | f28d553; BSD-3-Clause-style root terms | Preserve notices/nonendorsement; linked SDKs separate. Existing RTXDI3.1 selector is first comparison. |
| [LoD reference](https://github.com/elite-sheep/ReSTIR-LoD/blob/37d13d9b1f3e76be88aa79109d24b0fe6e4ef6a9/LICENSE.md) | 37d13d9; BSD-3-Clause-style root terms | Study/port with notices; Falcor, SDKs and assets separate. |
| [BDPT reference](https://github.com/Shmaug/ReSTIR-BDPT/blob/b4fc2c7f16a6af6791e1139b930adce5e19117c9/LICENSE.md) | b4fc2c7; BSD-3-Clause-style root terms | Known rough-glass UCW bias in README; no unqualified adoption. |
| [SPMIS archive](https://research.nvidia.com/labs/rtr/publication/hedstrom2026stochastic/hedstrom2026stochastic.zip) | SHA25602be1910858db4cd340f642edbf5a0405395f8056a21238ee832ce5c08f670b7; no permission/license notice in nine inspected files | Link/study mathematics; source copying deferred pending terms. |
| ReSTIR PG / multilayer official code | No official implementation link found on inspected project pages | Absence is search-scoped, not proof none exists. No invented reuse grant. |

Original summaries and proposed integration plans are supplied here; original paper PDFs and extracted full text remain outside published docs. In particular PG's author PDF states personal use/nonredistribution. CC-BY statements on other papers do not automatically license their code, SDKs, scenes, textures or video. All20 catalog entries retain public primary links and reading scope. Any breadth code reference with no pinned license check requires a fresh artifact-specific review before reuse.

## Primary entry points

- [Wyman conference/journal paper list](https://cwyman.org/paperList.html)
- [RTXDI3.1 changelog](https://github.com/NVIDIA-RTX/RTXDI/blob/a6efab966b7c3b272da0461578eb56ac61c7cbff/ChangeLog.md)
- [RTXDI ReSTIR PT integration guide](https://github.com/NVIDIA-RTX/RTXDI/blob/a6efab966b7c3b272da0461578eb56ac61c7cbff/Doc/RestirPT.md)
- [RTXPT1.9 design](https://github.com/NVIDIA-RTX/RTXPT/blob/303b408ab81790a5051abd7573830b7a4112eb8e/Docs/Design.md)

Bibliographic month/year is retained where verified. Unknown exact publication dates remain blank in structured records. The inspected BDPT author PDF contains placeholder DOI/publication fields; those placeholders are not treated as final metadata.
