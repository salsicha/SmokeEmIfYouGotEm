#include "raftsim_water/numpy_io.hpp"

#include <zlib.h>

#include <algorithm>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iterator>
#include <sstream>
#include <stdexcept>

namespace raftsim {

namespace {

std::vector<std::uint8_t> read_binary_file(const std::string& path) {
    std::ifstream stream(path, std::ios::binary);
    if (!stream) {
        throw std::runtime_error("Could not open binary file: " + path);
    }
    return std::vector<std::uint8_t>((std::istreambuf_iterator<char>(stream)), std::istreambuf_iterator<char>());
}

std::uint16_t le16(const std::vector<std::uint8_t>& data, std::size_t offset) {
    return static_cast<std::uint16_t>(
        static_cast<std::uint16_t>(data.at(offset)) |
        static_cast<std::uint16_t>(data.at(offset + 1)) << 8
    );
}

std::uint32_t le32(const std::vector<std::uint8_t>& data, std::size_t offset) {
    return static_cast<std::uint32_t>(
        static_cast<std::uint32_t>(data.at(offset)) |
        static_cast<std::uint32_t>(data.at(offset + 1)) << 8 |
        static_cast<std::uint32_t>(data.at(offset + 2)) << 16 |
        static_cast<std::uint32_t>(data.at(offset + 3)) << 24
    );
}

bool contains(const std::string& text, const std::string& needle) {
    return text.find(needle) != std::string::npos;
}

std::pair<std::size_t, std::size_t> parse_shape(const std::string& header) {
    std::size_t shape_pos = header.find("'shape'");
    if (shape_pos == std::string::npos) {
        shape_pos = header.find("\"shape\"");
    }
    if (shape_pos == std::string::npos) {
        throw std::runtime_error("Numpy header is missing shape.");
    }
    std::size_t open = header.find('(', shape_pos);
    std::size_t close = header.find(')', open);
    if (open == std::string::npos || close == std::string::npos) {
        throw std::runtime_error("Invalid Numpy shape header.");
    }
    std::string tuple = header.substr(open + 1, close - open - 1);
    std::replace(tuple.begin(), tuple.end(), ',', ' ');
    std::istringstream stream(tuple);
    std::size_t ny = 0;
    std::size_t nx = 0;
    stream >> ny >> nx;
    if (ny == 0 || nx == 0) {
        throw std::runtime_error("Only non-empty 2D Numpy arrays are supported.");
    }
    return {ny, nx};
}

struct NpyData {
    std::string descr;
    std::size_t ny = 0;
    std::size_t nx = 0;
    std::vector<std::uint8_t> payload;
};

NpyData parse_npy_bytes(const std::vector<std::uint8_t>& bytes) {
    if (bytes.size() < 12 || std::memcmp(bytes.data(), "\x93NUMPY", 6) != 0) {
        throw std::runtime_error("Invalid Numpy .npy header.");
    }
    std::uint8_t major = bytes.at(6);
    std::size_t header_len_offset = 8;
    std::size_t header_len_size = major <= 1 ? 2 : 4;
    std::size_t header_len = header_len_size == 2 ? le16(bytes, header_len_offset) : le32(bytes, header_len_offset);
    std::size_t data_offset = header_len_offset + header_len_size + header_len;
    if (data_offset > bytes.size()) {
        throw std::runtime_error("Numpy header length exceeds file size.");
    }
    std::string header(reinterpret_cast<const char*>(bytes.data() + header_len_offset + header_len_size), header_len);
    auto shape = parse_shape(header);
    std::string descr;
    if (contains(header, "<f8") || contains(header, "|f8")) {
        descr = "f8";
    } else if (contains(header, "|b1") || contains(header, "|?")) {
        descr = "b1";
    } else {
        throw std::runtime_error("Unsupported Numpy dtype in header: " + header);
    }
    std::vector<std::uint8_t> payload(bytes.begin() + static_cast<std::ptrdiff_t>(data_offset), bytes.end());
    return {descr, shape.first, shape.second, std::move(payload)};
}

Array2D npy_to_f64(const NpyData& data) {
    if (data.descr != "f8") {
        throw std::runtime_error("Expected float64 Numpy array.");
    }
    std::size_t count = data.ny * data.nx;
    if (data.payload.size() < count * sizeof(double)) {
        throw std::runtime_error("Numpy float64 payload is truncated.");
    }
    Array2D array(data.ny, data.nx);
    std::memcpy(array.values().data(), data.payload.data(), count * sizeof(double));
    return array;
}

BoolGrid npy_to_bool(const NpyData& data) {
    if (data.descr != "b1") {
        throw std::runtime_error("Expected bool Numpy array.");
    }
    std::size_t count = data.ny * data.nx;
    if (data.payload.size() < count) {
        throw std::runtime_error("Numpy bool payload is truncated.");
    }
    BoolGrid grid;
    grid.ny = data.ny;
    grid.nx = data.nx;
    grid.values.assign(data.payload.begin(), data.payload.begin() + static_cast<std::ptrdiff_t>(count));
    return grid;
}

std::vector<std::uint8_t> inflate_raw_deflate(
    const std::vector<std::uint8_t>& source,
    std::size_t offset,
    std::size_t compressed_size,
    std::size_t uncompressed_size
) {
    std::vector<std::uint8_t> output(uncompressed_size);
    z_stream stream{};
    stream.next_in = const_cast<Bytef*>(reinterpret_cast<const Bytef*>(source.data() + offset));
    stream.avail_in = static_cast<uInt>(compressed_size);
    stream.next_out = reinterpret_cast<Bytef*>(output.data());
    stream.avail_out = static_cast<uInt>(output.size());
    if (inflateInit2(&stream, -MAX_WBITS) != Z_OK) {
        throw std::runtime_error("Could not initialize zlib inflate.");
    }
    int result = inflate(&stream, Z_FINISH);
    inflateEnd(&stream);
    if (result != Z_STREAM_END) {
        throw std::runtime_error("Could not inflate compressed zip member.");
    }
    return output;
}

struct ZipEntry {
    std::string name;
    std::uint16_t method = 0;
    std::uint32_t compressed_size = 0;
    std::uint32_t uncompressed_size = 0;
    std::uint32_t local_header_offset = 0;
};

std::vector<ZipEntry> read_zip_entries(const std::vector<std::uint8_t>& bytes) {
    if (bytes.size() < 22) {
        throw std::runtime_error("Zip file is too small.");
    }
    std::size_t eocd = std::string::npos;
    for (std::size_t pos = bytes.size() - 22; pos > 0; --pos) {
        if (le32(bytes, pos) == 0x06054b50u) {
            eocd = pos;
            break;
        }
    }
    if (eocd == std::string::npos) {
        throw std::runtime_error("Zip EOCD record not found.");
    }
    std::uint16_t count = le16(bytes, eocd + 10);
    std::uint32_t central_offset = le32(bytes, eocd + 16);
    std::size_t pos = central_offset;
    std::vector<ZipEntry> entries;
    for (std::uint16_t i = 0; i < count; ++i) {
        if (le32(bytes, pos) != 0x02014b50u) {
            throw std::runtime_error("Invalid zip central directory header.");
        }
        std::uint16_t method = le16(bytes, pos + 10);
        std::uint32_t compressed = le32(bytes, pos + 20);
        std::uint32_t uncompressed = le32(bytes, pos + 24);
        std::uint16_t name_len = le16(bytes, pos + 28);
        std::uint16_t extra_len = le16(bytes, pos + 30);
        std::uint16_t comment_len = le16(bytes, pos + 32);
        std::uint32_t local_offset = le32(bytes, pos + 42);
        std::string name(reinterpret_cast<const char*>(bytes.data() + pos + 46), name_len);
        entries.push_back({name, method, compressed, uncompressed, local_offset});
        pos += 46 + name_len + extra_len + comment_len;
    }
    return entries;
}

std::vector<std::uint8_t> read_zip_entry_data(const std::vector<std::uint8_t>& bytes, const ZipEntry& entry) {
    std::size_t pos = entry.local_header_offset;
    if (le32(bytes, pos) != 0x04034b50u) {
        throw std::runtime_error("Invalid zip local file header.");
    }
    std::uint16_t name_len = le16(bytes, pos + 26);
    std::uint16_t extra_len = le16(bytes, pos + 28);
    std::size_t data_offset = pos + 30 + name_len + extra_len;
    if (entry.method == 0) {
        return std::vector<std::uint8_t>(
            bytes.begin() + static_cast<std::ptrdiff_t>(data_offset),
            bytes.begin() + static_cast<std::ptrdiff_t>(data_offset + entry.uncompressed_size)
        );
    }
    if (entry.method == 8) {
        return inflate_raw_deflate(bytes, data_offset, entry.compressed_size, entry.uncompressed_size);
    }
    throw std::runtime_error("Unsupported zip compression method.");
}

}  // namespace

Array2D load_npy_f64(const std::string& path) {
    return npy_to_f64(parse_npy_bytes(read_binary_file(path)));
}

BoolGrid load_npy_bool_bytes(const std::string& path) {
    return npy_to_bool(parse_npy_bytes(read_binary_file(path)));
}

NpzArchive load_npz(const std::string& path) {
    std::vector<std::uint8_t> bytes = read_binary_file(path);
    NpzArchive archive;
    for (const ZipEntry& entry : read_zip_entries(bytes)) {
        std::vector<std::uint8_t> data = read_zip_entry_data(bytes, entry);
        NpyData npy = parse_npy_bytes(data);
        std::string name = entry.name;
        if (name.size() > 4 && name.substr(name.size() - 4) == ".npy") {
            name = name.substr(0, name.size() - 4);
        }
        if (npy.descr == "f8") {
            archive.float_arrays.emplace(name, npy_to_f64(npy));
        } else if (npy.descr == "b1") {
            archive.bool_arrays.emplace(name, npy_to_bool(npy));
        }
    }
    return archive;
}

}  // namespace raftsim
