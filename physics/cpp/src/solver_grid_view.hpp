#pragma once

#include "raftsim_water/array2d.hpp"
#include <cassert>
#include <limits>
#include <type_traits>

namespace raftsim::solver_detail {

// Stage-local views for loops whose row/column bounds are explicit. Validate
// shape AND backing storage once, including externally resized Array2D storage.
// Never retain a view across a state swap, resize, or worker barrier lifetime.
// General Array2D access remains checked; these views are private to kernels.
template<bool Mutable>
class ValidatedGridView {
    using Array = std::conditional_t<Mutable, Array2D, const Array2D>;
    using Pointer = std::conditional_t<Mutable, double*, const double*>;
    Pointer data_;
    std::size_t nx_, ny_;
public:
    ValidatedGridView(Array& array, std::size_t ny, std::size_t nx)
        : data_(array.values().data()), nx_(nx), ny_(ny) {
        if (nx == 0 || ny == 0 || ny > std::numeric_limits<std::size_t>::max()/nx ||
            array.nx() != nx || array.ny() != ny || array.values().size() != nx*ny)
            throw std::runtime_error("Numerical kernel grid shape/storage mismatch");
    }
    std::conditional_t<Mutable, double&, const double&>
    operator()(std::size_t row, std::size_t col) const noexcept {
        assert(row < ny_ && col < nx_);
        return data_[row*nx_+col];
    }
};

using ReadGridView = ValidatedGridView<false>;
using WriteGridView = ValidatedGridView<true>;

} // namespace raftsim::solver_detail
