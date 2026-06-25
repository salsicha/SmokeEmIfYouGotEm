#pragma once

#include <algorithm>
#include <cstddef>
#include <stdexcept>
#include <vector>

namespace raftsim {

class Array2D {
public:
    Array2D() = default;

    Array2D(std::size_t ny, std::size_t nx, double value = 0.0)
        : ny_(ny), nx_(nx), values_(ny * nx, value) {}

    std::size_t ny() const { return ny_; }
    std::size_t nx() const { return nx_; }
    std::size_t size() const { return values_.size(); }
    bool empty() const { return values_.empty(); }

    double& operator()(std::size_t row, std::size_t col) {
        return values_.at(row * nx_ + col);
    }

    double operator()(std::size_t row, std::size_t col) const {
        return values_.at(row * nx_ + col);
    }

    const std::vector<double>& values() const { return values_; }
    std::vector<double>& values() { return values_; }

    double min() const {
        if (values_.empty()) {
            throw std::runtime_error("Cannot compute min of empty Array2D.");
        }
        return *std::min_element(values_.begin(), values_.end());
    }

    double max() const {
        if (values_.empty()) {
            throw std::runtime_error("Cannot compute max of empty Array2D.");
        }
        return *std::max_element(values_.begin(), values_.end());
    }

private:
    std::size_t ny_ = 0;
    std::size_t nx_ = 0;
    std::vector<double> values_;
};

}  // namespace raftsim

