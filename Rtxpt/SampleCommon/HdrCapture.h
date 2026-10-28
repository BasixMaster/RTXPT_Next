// Project-owned raw HDR validation capture. No display or exposure transform.
#pragma once

#include <nvrhi/nvrhi.h>
#include <filesystem>
#include <string>

namespace rtxpt
{
    // The caller must submit/close its rendering command list first. This function
    // submits its own copy list, waits for device idle, and writes path plus
    // path + ".json". Output is the texture's stored RGB, including non-finites.
    // Use OutputColor with AA0 for raw estimator validation. Alpha is omitted.
    bool SaveLinearHdrPFM(nvrhi::IDevice* device, nvrhi::ITexture* texture,
        const std::filesystem::path& path, std::string& error);

    // Same encoding for already mapped, top-to-bottom texture rows. Exposed so
    // CPU fixture tests can check the actual writer independently of a GPU.
    bool WriteMappedLinearHdrPFM(const void* data, size_t rowPitch,
        unsigned int width, unsigned int height, nvrhi::Format format,
        const std::filesystem::path& path, std::string& error);
}
