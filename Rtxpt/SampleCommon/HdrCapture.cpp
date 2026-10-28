// Project-owned raw HDR validation capture. No display or exposure transform.
#include "HdrCapture.h"

#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <limits>
#include <locale>

namespace
{
    static_assert(sizeof(float) == 4 && std::numeric_limits<float>::is_iec559,
        "PFM capture requires IEEE-754 binary32");

    struct SourceLayout { unsigned int channels, componentBytes; const char* name; };
    bool GetLayout(nvrhi::Format format, SourceLayout& layout)
    {
        switch (format)
        {
        case nvrhi::Format::RGBA16_FLOAT: layout = { 4, 2, "RGBA16_FLOAT" }; return true;
        case nvrhi::Format::RGBA32_FLOAT: layout = { 4, 4, "RGBA32_FLOAT" }; return true;
        case nvrhi::Format::RGB32_FLOAT: layout = { 3, 4, "RGB32_FLOAT" }; return true;
        default: return false;
        }
    }

    // Exact binary16 -> binary32 expansion, including subnormals, signed zero,
    // infinities and NaN payload bits. No arithmetic clamp or half rounding.
    float ReadComponent(const unsigned char* source, unsigned int bytes)
    {
        uint32_t bits;
        if (bytes == 4)
            std::memcpy(&bits, source, 4);
        else
        {
            uint16_t half;
            std::memcpy(&half, source, 2);
            const uint32_t sign = uint32_t(half & 0x8000u) << 16;
            uint32_t exponent = (half >> 10) & 31u;
            uint32_t mantissa = half & 1023u;
            if (exponent == 0)
            {
                bits = sign;
                if (mantissa)
                {
                    int normalExponent = -14;
                    while ((mantissa & 1024u) == 0) { mantissa <<= 1; --normalExponent; }
                    bits |= uint32_t(normalExponent + 127) << 23;
                    bits |= (mantissa & 1023u) << 13;
                }
            }
            else if (exponent == 31)
                bits = sign | 0x7f800000u | (mantissa << 13);
            else
                bits = sign | ((exponent + 112u) << 23) | (mantissa << 13);
        }
        float value;
        std::memcpy(&value, &bits, 4);
        return value;
    }

    void WriteLittleFloat(std::ostream& stream, float value)
    {
        uint32_t bits;
        std::memcpy(&bits, &value, 4);
        const std::array<char, 4> bytes = { char(bits), char(bits >> 8), char(bits >> 16), char(bits >> 24) };
        stream.write(bytes.data(), bytes.size());
    }
}

bool rtxpt::WriteMappedLinearHdrPFM(const void* data, size_t rowPitch,
    unsigned int width, unsigned int height, nvrhi::Format format,
    const std::filesystem::path& path, std::string& error)
{
    error.clear();
    SourceLayout layout{};
    if (!GetLayout(format, layout)) { error = "Unsupported raw HDR source format"; return false; }
    const size_t pixelBytes = size_t(layout.channels) * layout.componentBytes;
    if (!data || !width || !height || width > std::numeric_limits<size_t>::max() / pixelBytes ||
        rowPitch < size_t(width) * pixelBytes || height > std::numeric_limits<size_t>::max() / rowPitch)
    { error = "Invalid mapped HDR dimensions or row pitch"; return false; }

    std::ofstream image(path, std::ios::binary | std::ios::trunc);
    if (!image) { error = "Cannot open PFM output"; return false; }
    image.imbue(std::locale::classic());
    image << "PF\n" << width << ' ' << height << "\n-1.0\n";
    std::array<uint64_t, 3> finite{}, nan{}, positiveInfinity{}, negativeInfinity{};
    uint64_t nonFinitePixels = 0;
    for (unsigned int storedRow = 0; storedRow < height; ++storedRow)
    {
        const auto* row = static_cast<const unsigned char*>(data) + size_t(height - 1 - storedRow) * rowPitch;
        for (unsigned int x = 0; x < width; ++x)
        {
            bool nonFinite = false;
            for (unsigned int c = 0; c < 3; ++c)
            {
                const float value = ReadComponent(row + size_t(x) * pixelBytes + c * layout.componentBytes, layout.componentBytes);
                if (std::isfinite(value)) ++finite[c];
                else
                {
                    nonFinite = true;
                    if (std::isnan(value)) ++nan[c];
                    else if (std::signbit(value)) ++negativeInfinity[c];
                    else ++positiveInfinity[c];
                }
                WriteLittleFloat(image, value);
            }
            nonFinitePixels += nonFinite ? 1 : 0;
        }
    }
    image.close();
    if (!image) { error = "PFM write failed (output may be partial)"; return false; }

    auto metadataPath = path;
    metadataPath += ".json";
    std::ofstream metadata(metadataPath, std::ios::trunc);
    metadata.imbue(std::locale::classic());
    if (!metadata) { error = "Cannot open HDR metadata sidecar"; return false; }
    metadata << "{\n  \"schema_version\": 1,\n  \"source_format\": \"" << layout.name
        << "\",\n  \"width\": " << width << ",\n  \"height\": " << height
        << ",\n  \"source_row_pitch_bytes\": " << rowPitch
        << ",\n  \"source_component_bits\": " << layout.componentBytes * 8
        << ",\n  \"stored_channels\": \"RGB\",\n  \"alpha\": \"omitted\","
        << "\n  \"value_transform\": \"none: raw stored texture values; no tonemap or exposure correction\","
        << "\n  \"pfm_encoding\": \"IEEE754 binary32 little endian, scale -1, bottom row first\","
        << "\n  \"nonfinite_policy\": \"preserved\",\n  \"nonfinite_pixels\": " << nonFinitePixels;
    const auto writeCounts = [&metadata](const char* name, const std::array<uint64_t, 3>& counts)
    { metadata << ",\n  \"" << name << "_rgb\": [" << counts[0] << ", " << counts[1] << ", " << counts[2] << ']'; };
    writeCounts("finite", finite); writeCounts("nan", nan);
    writeCounts("positive_infinity", positiveInfinity); writeCounts("negative_infinity", negativeInfinity);
    metadata << "\n}\n";
    metadata.close();
    if (!metadata) { error = "HDR metadata write failed (output may be partial)"; return false; }
    return true;
}

bool rtxpt::SaveLinearHdrPFM(nvrhi::IDevice* device, nvrhi::ITexture* texture,
    const std::filesystem::path& path, std::string& error)
{
    error.clear();
    if (!device || !texture) { error = "Missing HDR capture device or texture"; return false; }
    const auto& desc = texture->getDesc();
    SourceLayout layout{};
    if (!GetLayout(desc.format, layout) || desc.dimension != nvrhi::TextureDimension::Texture2D ||
        desc.arraySize != 1 || desc.sampleCount != 1 || desc.depth != 1)
    { error = "HDR capture requires a single-sample 2D RGB32F/RGBA32F/RGBA16F texture"; return false; }

    auto staging = device->createStagingTexture(desc, nvrhi::CpuAccessMode::Read);
    auto commandList = device->createCommandList();
    if (!staging || !commandList) { error = "HDR staging allocation failed"; return false; }
    commandList->open();
    commandList->copyTexture(staging, nvrhi::TextureSlice(), texture, nvrhi::TextureSlice());
    commandList->close();
    device->executeCommandList(commandList);
    if (!device->waitForIdle()) { error = "Device idle wait failed during HDR capture"; return false; }

    size_t rowPitch = 0;
    const void* mapped = device->mapStagingTexture(staging, nvrhi::TextureSlice(), nvrhi::CpuAccessMode::Read, &rowPitch);
    if (!mapped) { error = "HDR staging map failed"; return false; }
    struct UnmapGuard
    {
        nvrhi::IDevice* device; nvrhi::IStagingTexture* texture;
        ~UnmapGuard() { device->unmapStagingTexture(texture); }
    } unmap{ device, staging.Get() };
    return WriteMappedLinearHdrPFM(mapped, rowPitch, desc.width, desc.height, desc.format, path, error);
}
