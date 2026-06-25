#pragma once

#include <cstdint>
#include <map>
#include <string>
#include <vector>

#include "raftsim_water/array2d.hpp"

namespace raftsim {

struct BoolGrid {
    std::size_t ny = 0;
    std::size_t nx = 0;
    std::vector<std::uint8_t> values;

    bool operator()(std::size_t row, std::size_t col) const {
        return values.at(row * nx + col) != 0;
    }
};

Array2D load_npy_f64(const std::string& path);
BoolGrid load_npy_bool_bytes(const std::string& path);

struct NpzArchive {
    std::map<std::string, Array2D> float_arrays;
    std::map<std::string, BoolGrid> bool_arrays;
};

NpzArchive load_npz(const std::string& path);

}  // namespace raftsim

