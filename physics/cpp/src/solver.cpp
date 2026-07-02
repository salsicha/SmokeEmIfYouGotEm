#include "raftsim_water/solver.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <utility>

namespace raftsim {

namespace fs = std::filesystem;

namespace {

constexpr double kPi = 3.14159265358979323846;
// Scoped bed-step constants are calibrated against the GeoClaw discontinuous-bed fixture.
constexpr double kBedStepFaceSourceBoost = 1.26;
constexpr double kBedStepPreStepDischargeFloor = 0.66;
constexpr double kBedStepTopographyRedistributionRate = 0.47;
constexpr double kConstrictionEdgeVelocityFraction = 0.41;
constexpr std::size_t kConstrictionWetBandRelaxationCells = 2;
constexpr double kConstrictionWetBandMinimumDepth = 0.15;
constexpr double kConstrictionWetBandProfileRate = 5.0;
constexpr double kConstrictionWetBandProfileMaxDepthPerSecond = 1.4;
constexpr double kConstrictionWetBandProfileEdgeDepthScale = 0.42;
constexpr double kConstrictionWetBandProfileInteriorDepthScale = 1.36;
constexpr double kConstrictionWetBandProfileDryShelfDepth = 0.12;
constexpr double kConstrictionWetBandProfileExponent = 0.3;
constexpr double kConstrictionWetBandProfileVelocityRate = 2.0;
constexpr double kConstrictionWetBandProfileMaxSpeedPerSecond = 3.0;
constexpr double kConstrictionWetBandProfileSpeedFraction = 0.55;
constexpr double kConstrictionWetBandProfileEdgeSpeedBoost = 0.45;
constexpr double kConstrictionWetBandProfileCrossStreamFraction = 0.8;
constexpr double kConstrictionUpstreamInteriorVelocityRate = 0.8;
constexpr double kConstrictionUpstreamInteriorVelocityMaxSpeedPerSecond = 0.65;
constexpr double kConstrictionUpstreamInteriorVelocityCenterSpeedFraction = 0.03;
constexpr double kConstrictionUpstreamInteriorVelocityEdgeSpeedFraction = 0.42;
constexpr double kConstrictionUpstreamInteriorVelocityEdgeExponent = 1.2;
constexpr double kConstrictionVolumeResponseRate = 0.75;
constexpr double kConstrictionVolumeResponseMaxDepthPerSecond = 0.16;
constexpr double kConstrictionUpstreamVolumeDepthScale = 1.22;
constexpr double kConstrictionThroatVolumeDepthScale = 0.9;
constexpr double kConstrictionDownstreamVolumeDepthScale = 1.05;
constexpr double kConstrictionRecoveryTransportRate = 0.8;
constexpr double kConstrictionRecoveryTransportMaxDepthPerSecond = 0.14;
constexpr double kConstrictionRecoveryTransportDepthScale = 1.0;
constexpr double kConstrictionShoulderDepthTaperRate = 0.45;
constexpr double kConstrictionShoulderEdgeWeight = 0.22;
constexpr double kConstrictionShoulderInteriorWeight = 1.35;
constexpr double kConstrictionShoulderVelocityRate = 0.45;
constexpr double kConstrictionShoulderMaxVelocityPerSecond = 0.25;
constexpr double kConstrictionShoulderSpeedFraction = 1.0;
constexpr double kConstrictionShoulderEdgeVelocityFraction = 0.25;
constexpr double kConstrictionLocalFringeTargetDepth = 0.18;
constexpr double kConstrictionLocalFringeRate = 1.0;
constexpr double kConstrictionLocalFringeMaxDepthPerSecond = 0.12;
constexpr double kConstrictionLocalFringeRecoveryDepthScale = 1.0;
constexpr double kConstrictionLocalFringeSpeedFraction = 1.145;
constexpr double kConstrictionLocalFringeEdgeVelocityFraction = 0.16;
constexpr double kConstrictionNearThroatDepthScale = 1.0;
constexpr double kConstrictionNearThroatReceiverDepthScale = 1.22;
constexpr double kConstrictionNearThroatSpeedFraction = 1.0;
constexpr double kConstrictionNearThroatEdgeVelocityFraction = 0.41;
constexpr double kConstrictionDepthDistributionRate = 1.0;
constexpr double kConstrictionDepthDistributionMaxDepthPerSecond = 0.14;
constexpr double kConstrictionDepthDistributionRecoveryDepthScale = 0.93;
constexpr double kConstrictionDepthDistributionUpstreamDepthScale = 1.42;
constexpr double kConstrictionDepthDistributionDownstreamDepthScale = 1.28;
constexpr double kConstrictionVelocityTimingRate = 0.7;
constexpr double kConstrictionVelocityTimingMaxSpeedPerSecond = 0.35;
constexpr double kConstrictionVelocityTimingUpstreamSpeedScale = 1.28;
constexpr double kConstrictionVelocityTimingUpstreamInteriorSpeedFloor = 0.06;
constexpr double kConstrictionVelocityTimingUpstreamEdgeSpeedBoost = 0.86;
constexpr double kConstrictionVelocityTimingUpstreamEdgeExponent = 0.75;
constexpr double kConstrictionVelocityTimingRecoverySpeedScale = 1.0;
constexpr double kConstrictionVelocityTimingDownstreamSpeedScale = 0.98;
constexpr double kConstrictionVelocityTimingCrossStreamDamping = 0.5;
constexpr double kConstrictionFluxMassTimingRate = 0.75;
constexpr double kConstrictionFluxMassTimingMaxDepthPerSecond = 0.08;
constexpr double kConstrictionFluxMassTimingRecoveryDepthScale = 0.9;
constexpr double kConstrictionFluxMassTimingUpstreamReceiverDepthScale = 1.5;
constexpr double kConstrictionFluxMassTimingDownstreamReceiverDepthScale = 1.35;
constexpr double kConstrictionFluxMassTimingVelocityRate = 0.8;
constexpr double kConstrictionFluxMassTimingMaxSpeedPerSecond = 0.55;
constexpr double kConstrictionFluxMassTimingFringeSpeedFraction = 1.15;
constexpr double kConstrictionFluxMassTimingFringeCrossStreamFraction = 0.25;
constexpr double kConstrictionLateralSlopeShapeVelocityRate = 0.95;
constexpr double kConstrictionLateralSlopeShapeMaxSpeedPerSecond = 0.72;
constexpr double kConstrictionLateralSlopeShapeDryBankDepthCap = 0.22;
constexpr double kConstrictionLateralSlopeShapeUpstreamCrossStreamFraction = 1.15;
constexpr double kConstrictionLateralSlopeShapeDownstreamCrossStreamFraction = 0.26;
constexpr double kConstrictionLateralSlopeShapeRecoveryCrossStreamFraction = 0.34;
constexpr double kConstrictionLateralSlopeShapeUpstreamLowerSpeedFraction = 0.315;
constexpr double kConstrictionLateralSlopeShapeUpstreamUpperSpeedFraction = 1.12;
constexpr double kConstrictionLateralSlopeShapeDownstreamBankSpeedFraction = 0.12;
constexpr double kConstrictionLateralSlopeShapeRecoveryBankSpeedFraction = 0.72;
constexpr double kConstrictionLateralSlopeShapeBankInfluenceFloor = 0.45;
constexpr double kConstrictionCenterThroatCirculationVelocityRate = 3.4;
constexpr double kConstrictionCenterThroatCirculationMaxSpeedPerSecond = 2.4;
constexpr double kConstrictionCenterThroatCirculationCrossStreamFraction = 0.62;
constexpr double kConstrictionCenterThroatCirculationEdgeBoost = 2.35;
constexpr double kConstrictionCenterThroatCirculationDownstreamSpeedFraction = 1.0;
constexpr double kConstrictionUpstreamEdgeFluxRate = 1.0;
constexpr double kConstrictionUpstreamEdgeFluxMaxDepthPerSecond = 0.42;
constexpr double kConstrictionUpstreamEdgeFluxTargetDepthScale = 0.28;
constexpr double kConstrictionUpstreamEdgeFluxMinTargetDepth = 0.32;
constexpr double kConstrictionYFaceOppositionFluxTargetDepthScale = 0.92;
constexpr double kConstrictionYFaceOppositionFluxCrossStreamFraction = 1.2;
constexpr double kConstrictionYFaceOppositionFluxMaxReferenceScale = 0.28;
constexpr double kConstrictionUpstreamEdgeMomentumRate = 3.0;
constexpr double kConstrictionUpstreamEdgeMomentumMaxSpeedPerSecond = 8.0;
constexpr double kConstrictionUpstreamEdgeSpeedFraction = 1.35;
constexpr double kConstrictionUpstreamEdgeCrossStreamFraction = 1.35;
constexpr double kConstrictionYFaceSourceSplitFraction = 0.06;
constexpr double kConstrictionYFaceSourceSplitMaxSpeedPerSecond = 0.45;
constexpr double kConstrictionYFaceStateBlend = 0.34;
constexpr double kConstrictionYFaceStateMaxSpeedDelta = 1.1;
constexpr double kConstrictionYFaceStateDepthScale = 0.72;
constexpr double kConstrictionYFaceStateMinDepth = 0.24;
constexpr double kConstrictionYFaceStateCompanionDepthFraction = 0.5;
constexpr double kConstrictionYFaceStateOutsideCompanionDepthFraction = 0.5;
constexpr double kConstrictionYFaceStateDownstreamSpeedFraction = 1.15;
constexpr double kConstrictionYFaceStateCrossStreamFraction = 1.25;
constexpr double kConstrictionTransitionEdgeFaceWeightScale = 0.75;
constexpr double kConstrictionUpstreamEdgeSupportRate = 1.2;
constexpr double kConstrictionUpstreamEdgeSupportMaxDepthPerSecond = 0.24;
constexpr double kConstrictionUpstreamEdgeSupportTargetDepthScale = 0.92;
constexpr double kConstrictionUpstreamEdgeSupportInteriorDepthScale = 1.48;
constexpr double kConstrictionUpstreamEdgeOppositionVelocityRate = 2.4;
constexpr double kConstrictionUpstreamEdgeOppositionMaxSpeedPerSecond = 2.0;
constexpr double kConstrictionUpstreamEdgeOppositionSpeedFraction = 1.15;
constexpr double kConstrictionUpstreamEdgeOppositionCrossStreamFraction = 1.2;
constexpr double kConstrictionLowerEdgeWidthDepthBalanceRate = 12.0;
constexpr double kConstrictionLowerEdgeWidthDepthBalanceMaxDepthPerSecond = 4.0;
constexpr double kConstrictionLowerEdgeWidthDepthBalanceTargetDepthScale = 0.45;
constexpr double kConstrictionLowerEdgeWidthDepthBalanceDonorFloorScale = 1.35;
constexpr double kConstrictionLowerEdgeWidthDepthBalanceVelocityRate = 4.0;
constexpr double kConstrictionLowerEdgeWidthDepthBalanceMaxSpeedPerSecond = 6.0;
constexpr double kConstrictionLowerEdgeWidthDepthBalanceSpeedFraction = 0.64;
constexpr double kConstrictionLowerEdgeWidthDepthBalanceCrossStreamFraction = 0.63;
constexpr double kConstrictionUpperEdgeOppositionBalanceRate = 10.0;
constexpr double kConstrictionUpperEdgeOppositionBalanceMaxDepthPerSecond = 4.0;
constexpr double kConstrictionUpperEdgeOppositionBalanceReceiverDepthScale = 0.68;
constexpr double kConstrictionUpperEdgeOppositionBalanceDonorFloorScale = 0.45;
constexpr double kConstrictionUpperEdgeOppositionBalanceVelocityRate = 4.0;
constexpr double kConstrictionUpperEdgeOppositionBalanceMaxSpeedPerSecond = 6.0;
constexpr double kConstrictionUpperEdgeOppositionBalanceSpeedFraction = 0.82;
constexpr double kConstrictionUpperEdgeOppositionBalanceCrossStreamFraction = 0.72;
constexpr double kConstrictionUpperEdgeOppositionBalanceInteriorCrossStreamFraction = 0.36;
constexpr double kConstrictionUpperOutsideShelfSupportRate = 8.0;
constexpr double kConstrictionUpperOutsideShelfSupportMaxDepthPerSecond = 2.0;
constexpr double kConstrictionUpperOutsideShelfSupportTargetDepthScale = 0.2;
constexpr double kConstrictionUpperOutsideShelfSupportDonorFloorScale = 0.45;
constexpr double kConstrictionUpperOutsideShelfSupportSpeedFraction = 0.92;
constexpr double kConstrictionUpperOutsideShelfSupportCrossStreamFraction = 0.78;
constexpr double kConstrictionUpperEdgeFluxMagnitudeRate = 9.0;
constexpr double kConstrictionUpperEdgeFluxMagnitudeMaxSpeedPerSecond = 5.0;
constexpr double kConstrictionUpperEdgeFluxMagnitudeSpeedFraction = 0.82;
constexpr double kConstrictionUpperEdgeFluxMagnitudeCrossStreamFraction = 1.08;
constexpr double kConstrictionUpperEdgeFluxMagnitudeInteriorCrossStreamFraction = 0.48;
constexpr double kConstrictionCrossStreamMomentumRate = 2.2;
constexpr double kConstrictionCrossStreamMomentumMaxSpeedPerSecond = 3.6;
constexpr double kConstrictionCrossStreamMomentumRecoveryFraction = 0.58;
constexpr double kConstrictionCrossStreamMomentumInteriorWeightFloor = 0.42;
constexpr double kConstrictionCrossStreamMomentumMinDepth = 0.3;
constexpr double kConstrictionLocalizedCirculationVelocityRate = 3.0;
constexpr double kConstrictionLocalizedCirculationMaxSpeedPerSecond = 3.2;
constexpr double kConstrictionLocalizedCirculationUpstreamCrossStreamFraction = 0.0;
constexpr double kConstrictionLocalizedCirculationThroatCrossStreamFraction = 0.34;
constexpr double kConstrictionLocalizedCirculationRecoveryCrossStreamFraction = 0.42;
constexpr double kConstrictionLocalizedCirculationMinDepth = 0.15;
constexpr double kConstrictionLocalizedCirculationInteriorWeightFloor = 0.55;

double clamp(double value, double lo, double hi) {
    return std::max(lo, std::min(hi, value));
}

std::size_t idx(const Scenario& scenario, std::size_t row, std::size_t col) {
    return row * scenario.grid.nx + col;
}

double safe_depth(double h, double dry_tolerance) {
    return std::max(h, dry_tolerance);
}

double move_toward(double current, double target, double max_delta) {
    if (target > current) {
        return std::min(target, current + max_delta);
    }
    return std::max(target, current - max_delta);
}

struct ConservedState {
    double h = 0.0;
    double hu = 0.0;
    double hv = 0.0;
};

struct FluxState {
    double h = 0.0;
    double hu = 0.0;
    double hv = 0.0;
};

struct InterfaceFluxPair {
    FluxState left;
    FluxState right;
};

struct GridCellSelection {
    bool found = false;
    std::size_t row = 0;
    std::size_t col = 0;
};

struct ColumnWetBand {
    bool found = false;
    std::size_t first_row = 0;
    std::size_t last_row = 0;
    std::size_t count = 0;
};

struct ConstrictionDepthTransferCell {
    std::size_t row = 0;
    std::size_t col = 0;
    double capacity = 0.0;
};

struct ConstrictionProfileTransferCell {
    std::size_t row = 0;
    std::size_t col = 0;
    double capacity = 0.0;
    double target_u = 0.0;
    double target_v = 0.0;
};

struct ConstrictionFaceFluxAuditRow {
    std::string face_role;
    std::size_t column_index = 0;
    std::size_t south_row_index = 0;
    std::size_t north_row_index = 0;
    double south_h = 0.0;
    double south_u = 0.0;
    double south_v = 0.0;
    double north_h = 0.0;
    double north_u = 0.0;
    double north_v = 0.0;
    double face_state_south_h = 0.0;
    double face_state_south_u = 0.0;
    double face_state_south_v = 0.0;
    double face_state_north_h = 0.0;
    double face_state_north_u = 0.0;
    double face_state_north_v = 0.0;
    double south_bed = 0.0;
    double north_bed = 0.0;
    double base_flux_h = 0.0;
    double base_flux_hu = 0.0;
    double base_flux_hv = 0.0;
    double hydro_left_flux_h = 0.0;
    double hydro_left_flux_hu = 0.0;
    double hydro_left_flux_hv = 0.0;
    double hydro_right_flux_h = 0.0;
    double hydro_right_flux_hu = 0.0;
    double hydro_right_flux_hv = 0.0;
    double post_left_flux_h = 0.0;
    double post_left_flux_hu = 0.0;
    double post_left_flux_hv = 0.0;
    double post_right_flux_h = 0.0;
    double post_right_flux_hu = 0.0;
    double post_right_flux_hv = 0.0;
    double hydro_left_source_hv = 0.0;
    double hydro_right_source_hv = 0.0;
    double constriction_source_split_left_hv = 0.0;
    double constriction_source_split_right_hv = 0.0;
    double constriction_left_source_h = 0.0;
    double constriction_left_source_hu = 0.0;
    double constriction_left_source_hv = 0.0;
    double constriction_right_source_h = 0.0;
    double constriction_right_source_hu = 0.0;
    double constriction_right_source_hv = 0.0;
    double south_cell_bed_slope_source_hv_per_s = 0.0;
    double north_cell_bed_slope_source_hv_per_s = 0.0;
    bool constriction_face_state_reconstruction_applied = false;
    bool hydrostatic_face_source_enabled = false;
    bool constriction_hydrostatic_source_split_applied = false;
    bool constriction_face_source_applied = false;
};

double gradient_x(const Array2D& array, const Scenario& scenario, std::size_t row, std::size_t col) {
    if (col == 0) {
        return (array(row, col + 1) - array(row, col)) / scenario.grid.dx;
    }
    if (col + 1 >= scenario.grid.nx) {
        return (array(row, col) - array(row, col - 1)) / scenario.grid.dx;
    }
    return (array(row, col + 1) - array(row, col - 1)) / (2.0 * scenario.grid.dx);
}

double gradient_y(const Array2D& array, const Scenario& scenario, std::size_t row, std::size_t col) {
    if (row == 0) {
        return (array(row + 1, col) - array(row, col)) / scenario.grid.dy;
    }
    if (row + 1 >= scenario.grid.ny) {
        return (array(row, col) - array(row - 1, col)) / scenario.grid.dy;
    }
    return (array(row + 1, col) - array(row - 1, col)) / (2.0 * scenario.grid.dy);
}

double pressure_eta_x(const WaterState& state, const Scenario& scenario, const SolverConfig& config, std::size_t row, std::size_t col) {
    double center = state.eta(row, col);
    if (col == 0) {
        double east = state.h(row, col + 1) > config.dry_tolerance ? state.eta(row, col + 1) : center;
        return (east - center) / scenario.grid.dx;
    }
    if (col + 1 >= scenario.grid.nx) {
        double west = state.h(row, col - 1) > config.dry_tolerance ? state.eta(row, col - 1) : center;
        return (center - west) / scenario.grid.dx;
    }
    double west = state.h(row, col - 1) > config.dry_tolerance ? state.eta(row, col - 1) : center;
    double east = state.h(row, col + 1) > config.dry_tolerance ? state.eta(row, col + 1) : center;
    return (east - west) / (2.0 * scenario.grid.dx);
}

double pressure_eta_y(const WaterState& state, const Scenario& scenario, const SolverConfig& config, std::size_t row, std::size_t col) {
    double center = state.eta(row, col);
    if (row == 0) {
        double north = state.h(row + 1, col) > config.dry_tolerance ? state.eta(row + 1, col) : center;
        return (north - center) / scenario.grid.dy;
    }
    if (row + 1 >= scenario.grid.ny) {
        double south = state.h(row - 1, col) > config.dry_tolerance ? state.eta(row - 1, col) : center;
        return (center - south) / scenario.grid.dy;
    }
    double south = state.h(row - 1, col) > config.dry_tolerance ? state.eta(row - 1, col) : center;
    double north = state.h(row + 1, col) > config.dry_tolerance ? state.eta(row + 1, col) : center;
    return (north - south) / (2.0 * scenario.grid.dy);
}

double divergence_x(const Array2D& array, const Scenario& scenario, std::size_t row, std::size_t col) {
    if (col == 0) {
        return (array(row, col + 1) - array(row, col)) / scenario.grid.dx;
    }
    if (col + 1 >= scenario.grid.nx) {
        return (array(row, col) - array(row, col - 1)) / scenario.grid.dx;
    }
    return (array(row, col + 1) - array(row, col - 1)) / (2.0 * scenario.grid.dx);
}

double divergence_y(const Array2D& array, const Scenario& scenario, std::size_t row, std::size_t col) {
    if (row == 0) {
        return (array(row + 1, col) - array(row, col)) / scenario.grid.dy;
    }
    if (row + 1 >= scenario.grid.ny) {
        return (array(row, col) - array(row - 1, col)) / scenario.grid.dy;
    }
    return (array(row + 1, col) - array(row - 1, col)) / (2.0 * scenario.grid.dy);
}

const BoundaryCondition* boundary_for_edge(const Scenario& scenario, const std::string& edge) {
    for (const BoundaryCondition& boundary : scenario.boundaries) {
        if (boundary.edge == edge) {
            return &boundary;
        }
    }
    return nullptr;
}

ConservedState conserved_from_cell(const Scenario& scenario, const WaterState& state, const SolverConfig& config, std::size_t row, std::size_t col) {
    (void)scenario;
    double h = std::max(0.0, state.h(row, col));
    if (h <= config.dry_tolerance) {
        return {};
    }
    return ConservedState{h, h * state.u(row, col), h * state.v(row, col)};
}

ConservedState boundary_conserved(
    const Scenario& scenario,
    const WaterState& state,
    const SolverConfig& config,
    std::size_t row,
    std::size_t col,
    const std::string& edge
) {
    ConservedState interior = conserved_from_cell(scenario, state, config, row, col);
    const BoundaryCondition* boundary = boundary_for_edge(scenario, edge);
    if (boundary == nullptr) {
        return interior;
    }
    if (boundary->kind == "wall" || boundary->kind == "bank") {
        if (edge == "west" || edge == "east") {
            interior.hu = -interior.hu;
        } else {
            interior.hv = -interior.hv;
        }
        return interior;
    }
    if (config.boundary_mode == "pyclaw") {
        return interior;
    }
    if (scenario.fixture_kind == "constriction" && boundary->has_depth && !scenario.initial.wet(row, col)) {
        return {};
    }
    double h = interior.h;
    if (boundary->has_stage) {
        h = std::max(0.0, boundary->stage - scenario.bed(row, col));
    }
    if (boundary->has_depth) {
        h = std::max(0.0, boundary->depth);
    }
    double u = h > config.dry_tolerance ? interior.hu / safe_depth(interior.h, config.dry_tolerance) : 0.0;
    double v = h > config.dry_tolerance ? interior.hv / safe_depth(interior.h, config.dry_tolerance) : 0.0;
    if (boundary->has_velocity) {
        u = boundary->velocity_x;
        v = boundary->velocity_y;
    }
    if (h <= config.dry_tolerance) {
        return {};
    }
    return ConservedState{h, h * u, h * v};
}

FluxState flux_x(const ConservedState& q, const SolverConfig& config) {
    if (q.h <= config.dry_tolerance) {
        return {};
    }
    double u = q.hu / safe_depth(q.h, config.dry_tolerance);
    double v = q.hv / safe_depth(q.h, config.dry_tolerance);
    return FluxState{q.hu, q.hu * u + 0.5 * config.gravity * q.h * q.h, q.hu * v};
}

FluxState flux_y(const ConservedState& q, const SolverConfig& config) {
    if (q.h <= config.dry_tolerance) {
        return {};
    }
    double v = q.hv / safe_depth(q.h, config.dry_tolerance);
    return FluxState{q.hv, q.hu * v, q.hv * v + 0.5 * config.gravity * q.h * q.h};
}

double wave_speed_x(const ConservedState& q, const SolverConfig& config) {
    if (q.h <= config.dry_tolerance) {
        return 0.0;
    }
    double u = q.hu / safe_depth(q.h, config.dry_tolerance);
    return std::abs(u) + std::sqrt(config.gravity * q.h);
}

double wave_speed_y(const ConservedState& q, const SolverConfig& config) {
    if (q.h <= config.dry_tolerance) {
        return 0.0;
    }
    double v = q.hv / safe_depth(q.h, config.dry_tolerance);
    return std::abs(v) + std::sqrt(config.gravity * q.h);
}

FluxState rusanov_flux_x(const ConservedState& left, const ConservedState& right, const SolverConfig& config) {
    FluxState fl = flux_x(left, config);
    FluxState fr = flux_x(right, config);
    double speed = std::max(wave_speed_x(left, config), wave_speed_x(right, config));
    return FluxState{
        0.5 * (fl.h + fr.h) - 0.5 * speed * (right.h - left.h),
        0.5 * (fl.hu + fr.hu) - 0.5 * speed * (right.hu - left.hu),
        0.5 * (fl.hv + fr.hv) - 0.5 * speed * (right.hv - left.hv),
    };
}

FluxState rusanov_flux_y(const ConservedState& south, const ConservedState& north, const SolverConfig& config) {
    FluxState fs = flux_y(south, config);
    FluxState fn = flux_y(north, config);
    double speed = std::max(wave_speed_y(south, config), wave_speed_y(north, config));
    return FluxState{
        0.5 * (fs.h + fn.h) - 0.5 * speed * (north.h - south.h),
        0.5 * (fs.hu + fn.hu) - 0.5 * speed * (north.hu - south.hu),
        0.5 * (fs.hv + fn.hv) - 0.5 * speed * (north.hv - south.hv),
    };
}

double velocity_x(const ConservedState& q, const SolverConfig& config) {
    return q.h > config.dry_tolerance ? q.hu / safe_depth(q.h, config.dry_tolerance) : 0.0;
}

double velocity_y(const ConservedState& q, const SolverConfig& config) {
    return q.h > config.dry_tolerance ? q.hv / safe_depth(q.h, config.dry_tolerance) : 0.0;
}

FluxState hll_flux_x(const ConservedState& left, const ConservedState& right, const SolverConfig& config) {
    FluxState fl = flux_x(left, config);
    FluxState fr = flux_x(right, config);
    double cl = left.h > config.dry_tolerance ? std::sqrt(config.gravity * left.h) : 0.0;
    double cr = right.h > config.dry_tolerance ? std::sqrt(config.gravity * right.h) : 0.0;
    double sl = std::min(velocity_x(left, config) - cl, velocity_x(right, config) - cr);
    double sr = std::max(velocity_x(left, config) + cl, velocity_x(right, config) + cr);
    if (sl >= 0.0) {
        return fl;
    }
    if (sr <= 0.0) {
        return fr;
    }
    double denom = std::max(sr - sl, 1.0e-12);
    return FluxState{
        (sr * fl.h - sl * fr.h + sl * sr * (right.h - left.h)) / denom,
        (sr * fl.hu - sl * fr.hu + sl * sr * (right.hu - left.hu)) / denom,
        (sr * fl.hv - sl * fr.hv + sl * sr * (right.hv - left.hv)) / denom,
    };
}

FluxState hll_flux_y(const ConservedState& south, const ConservedState& north, const SolverConfig& config) {
    FluxState fs = flux_y(south, config);
    FluxState fn = flux_y(north, config);
    double cs = south.h > config.dry_tolerance ? std::sqrt(config.gravity * south.h) : 0.0;
    double cn = north.h > config.dry_tolerance ? std::sqrt(config.gravity * north.h) : 0.0;
    double ss = std::min(velocity_y(south, config) - cs, velocity_y(north, config) - cn);
    double sn = std::max(velocity_y(south, config) + cs, velocity_y(north, config) + cn);
    if (ss >= 0.0) {
        return fs;
    }
    if (sn <= 0.0) {
        return fn;
    }
    double denom = std::max(sn - ss, 1.0e-12);
    return FluxState{
        (sn * fs.h - ss * fn.h + ss * sn * (north.h - south.h)) / denom,
        (sn * fs.hu - ss * fn.hu + ss * sn * (north.hu - south.hu)) / denom,
        (sn * fs.hv - ss * fn.hv + ss * sn * (north.hv - south.hv)) / denom,
    };
}

double entropy_fixed_abs(double lambda, double delta) {
    double magnitude = std::abs(lambda);
    if (magnitude >= delta || delta <= 1.0e-12) {
        return magnitude;
    }
    return 0.5 * (lambda * lambda / delta + delta);
}

FluxState roe_flux_x(const ConservedState& left, const ConservedState& right, const SolverConfig& config) {
    if (left.h <= config.dry_tolerance || right.h <= config.dry_tolerance) {
        return hll_flux_x(left, right, config);
    }
    FluxState fl = flux_x(left, config);
    FluxState fr = flux_x(right, config);
    double sqrt_l = std::sqrt(left.h);
    double sqrt_r = std::sqrt(right.h);
    double denom = std::max(sqrt_l + sqrt_r, 1.0e-12);
    double u = (sqrt_l * velocity_x(left, config) + sqrt_r * velocity_x(right, config)) / denom;
    double v = (sqrt_l * velocity_y(left, config) + sqrt_r * velocity_y(right, config)) / denom;
    double c = std::sqrt(0.5 * config.gravity * (left.h + right.h));

    double dh = right.h - left.h;
    double dhu = right.hu - left.hu;
    double dhv = right.hv - left.hv;
    double alpha_1 = ((u + c) * dh - dhu) / std::max(2.0 * c, 1.0e-12);
    double alpha_3 = (dhu - (u - c) * dh) / std::max(2.0 * c, 1.0e-12);
    double alpha_2 = dhv - v * dh;
    double entropy_delta = 0.1 * c;
    double lambda_1 = entropy_fixed_abs(u - c, entropy_delta);
    double lambda_2 = entropy_fixed_abs(u, entropy_delta);
    double lambda_3 = entropy_fixed_abs(u + c, entropy_delta);

    return FluxState{
        0.5 * (fl.h + fr.h) - 0.5 * (lambda_1 * alpha_1 + lambda_3 * alpha_3),
        0.5 * (fl.hu + fr.hu) - 0.5 * (lambda_1 * alpha_1 * (u - c) + lambda_3 * alpha_3 * (u + c)),
        0.5 * (fl.hv + fr.hv) - 0.5 * (lambda_1 * alpha_1 * v + lambda_2 * alpha_2 + lambda_3 * alpha_3 * v),
    };
}

FluxState roe_flux_y(const ConservedState& south, const ConservedState& north, const SolverConfig& config) {
    if (south.h <= config.dry_tolerance || north.h <= config.dry_tolerance) {
        return hll_flux_y(south, north, config);
    }
    FluxState fs = flux_y(south, config);
    FluxState fn = flux_y(north, config);
    double sqrt_s = std::sqrt(south.h);
    double sqrt_n = std::sqrt(north.h);
    double denom = std::max(sqrt_s + sqrt_n, 1.0e-12);
    double u = (sqrt_s * velocity_x(south, config) + sqrt_n * velocity_x(north, config)) / denom;
    double v = (sqrt_s * velocity_y(south, config) + sqrt_n * velocity_y(north, config)) / denom;
    double c = std::sqrt(0.5 * config.gravity * (south.h + north.h));

    double dh = north.h - south.h;
    double dhu = north.hu - south.hu;
    double dhv = north.hv - south.hv;
    double alpha_1 = ((v + c) * dh - dhv) / std::max(2.0 * c, 1.0e-12);
    double alpha_3 = (dhv - (v - c) * dh) / std::max(2.0 * c, 1.0e-12);
    double alpha_2 = dhu - u * dh;
    double entropy_delta = 0.1 * c;
    double lambda_1 = entropy_fixed_abs(v - c, entropy_delta);
    double lambda_2 = entropy_fixed_abs(v, entropy_delta);
    double lambda_3 = entropy_fixed_abs(v + c, entropy_delta);

    return FluxState{
        0.5 * (fs.h + fn.h) - 0.5 * (lambda_1 * alpha_1 + lambda_3 * alpha_3),
        0.5 * (fs.hu + fn.hu) - 0.5 * (lambda_1 * alpha_1 * u + lambda_2 * alpha_2 + lambda_3 * alpha_3 * u),
        0.5 * (fs.hv + fn.hv) - 0.5 * (lambda_1 * alpha_1 * (v - c) + lambda_3 * alpha_3 * (v + c)),
    };
}

FluxState finite_volume_flux_x(const ConservedState& left, const ConservedState& right, const SolverConfig& config) {
    if (config.flux_scheme == "roe") {
        return roe_flux_x(left, right, config);
    }
    if (config.flux_scheme == "hll") {
        return hll_flux_x(left, right, config);
    }
    return rusanov_flux_x(left, right, config);
}

FluxState finite_volume_flux_y(const ConservedState& south, const ConservedState& north, const SolverConfig& config) {
    if (config.flux_scheme == "roe") {
        return roe_flux_y(south, north, config);
    }
    if (config.flux_scheme == "hll") {
        return hll_flux_y(south, north, config);
    }
    return rusanov_flux_y(south, north, config);
}

bool is_abrupt_bed_jump(double left_bed, double right_bed) {
    return std::abs(right_bed - left_bed) > 0.1;
}

ConservedState hydrostatic_reconstructed_state(
    const ConservedState& q,
    double bed,
    double interface_bed,
    const SolverConfig& config
) {
    if (q.h <= config.dry_tolerance) {
        return {};
    }
    double eta = bed + q.h;
    double h_star = std::max(0.0, eta - interface_bed);
    if (h_star <= config.dry_tolerance) {
        return {};
    }
    double scale = h_star / safe_depth(q.h, config.dry_tolerance);
    return ConservedState{h_star, q.hu * scale, q.hv * scale};
}

InterfaceFluxPair hydrostatic_flux_x(
    const ConservedState& left,
    const ConservedState& right,
    double left_bed,
    double right_bed,
    const SolverConfig& config,
    bool enabled,
    bool reconstruct_interface_flux
) {
    FluxState base = finite_volume_flux_x(left, right, config);
    if (!enabled || config.bed_slope_source_scale == 0.0 ||
        (!reconstruct_interface_flux && !is_abrupt_bed_jump(left_bed, right_bed))) {
        return InterfaceFluxPair{base, base};
    }
    double interface_bed = std::max(left_bed, right_bed);
    ConservedState left_star = hydrostatic_reconstructed_state(left, left_bed, interface_bed, config);
    ConservedState right_star = hydrostatic_reconstructed_state(right, right_bed, interface_bed, config);
    FluxState reconstructed =
        reconstruct_interface_flux ? finite_volume_flux_x(left_star, right_star, config) : base;
    FluxState left_flux = reconstructed;
    FluxState right_flux = reconstructed;
    double source_scale =
        config.bed_slope_source_scale * (reconstruct_interface_flux ? 1.0 : kBedStepFaceSourceBoost);
    left_flux.hu +=
        0.5 * source_scale * config.gravity * (left.h * left.h - left_star.h * left_star.h);
    right_flux.hu +=
        0.5 * source_scale * config.gravity * (right.h * right.h - right_star.h * right_star.h);
    return InterfaceFluxPair{left_flux, right_flux};
}

InterfaceFluxPair hydrostatic_flux_y(
    const ConservedState& south,
    const ConservedState& north,
    double south_bed,
    double north_bed,
    const SolverConfig& config,
    bool enabled,
    bool reconstruct_interface_flux
) {
    FluxState base = finite_volume_flux_y(south, north, config);
    if (!enabled || config.bed_slope_source_scale == 0.0 ||
        (!reconstruct_interface_flux && !is_abrupt_bed_jump(south_bed, north_bed))) {
        return InterfaceFluxPair{base, base};
    }
    double interface_bed = std::max(south_bed, north_bed);
    ConservedState south_star = hydrostatic_reconstructed_state(south, south_bed, interface_bed, config);
    ConservedState north_star = hydrostatic_reconstructed_state(north, north_bed, interface_bed, config);
    FluxState reconstructed =
        reconstruct_interface_flux ? finite_volume_flux_y(south_star, north_star, config) : base;
    FluxState south_flux = reconstructed;
    FluxState north_flux = reconstructed;
    double source_scale =
        config.bed_slope_source_scale * (reconstruct_interface_flux ? 1.0 : kBedStepFaceSourceBoost);
    south_flux.hv +=
        0.5 * source_scale * config.gravity * (south.h * south.h - south_star.h * south_star.h);
    north_flux.hv +=
        0.5 * source_scale * config.gravity * (north.h * north.h - north_star.h * north_star.h);
    return InterfaceFluxPair{south_flux, north_flux};
}

bool has_abrupt_bed_neighbor(const Scenario& scenario, std::size_t row, std::size_t col) {
    double center_bed = scenario.bed(row, col);
    if (col > 0 && is_abrupt_bed_jump(scenario.bed(row, col - 1), center_bed)) {
        return true;
    }
    if (col + 1 < scenario.grid.nx && is_abrupt_bed_jump(center_bed, scenario.bed(row, col + 1))) {
        return true;
    }
    if (row > 0 && is_abrupt_bed_jump(scenario.bed(row - 1, col), center_bed)) {
        return true;
    }
    if (row + 1 < scenario.grid.ny && is_abrupt_bed_jump(center_bed, scenario.bed(row + 1, col))) {
        return true;
    }
    return false;
}

double pre_step_discharge_floor(const ConservedState& west, const ConservedState& east) {
    double available = std::max(std::max(0.0, west.hu), std::max(0.0, east.hu));
    return kBedStepPreStepDischargeFloor * available;
}

void apply_bed_step_augmented_topography(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
) {
    for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
        for (std::size_t col = 1; col + 1 < scenario.grid.nx; ++col) {
            if (!is_abrupt_bed_jump(scenario.bed(row, col), scenario.bed(row, col + 1)) ||
                scenario.bed(row, col + 1) <= scenario.bed(row, col)) {
                continue;
            }
            std::size_t shoulder_col = col - 1;
            std::size_t donor_col = col + 1;
            if (next.h(row, donor_col) <= config.dry_tolerance) {
                continue;
            }
            double shoulder_eta = scenario.bed(row, shoulder_col) + next.h(row, shoulder_col);
            double donor_eta = scenario.bed(row, donor_col) + next.h(row, donor_col);
            double excess = donor_eta - shoulder_eta;
            if (excess <= 0.0) {
                continue;
            }
            double transfer = kBedStepTopographyRedistributionRate * dt * excess;
            transfer = std::min(transfer, std::max(0.0, next.h(row, donor_col) - config.dry_tolerance));
            if (transfer <= 0.0) {
                continue;
            }

            double shoulder_h = next.h(row, shoulder_col);
            double donor_h = next.h(row, donor_col);
            double donor_u = next.u(row, donor_col);
            double donor_v = next.v(row, donor_col);
            double shoulder_hu = shoulder_h * next.u(row, shoulder_col) + transfer * donor_u;
            double shoulder_hv = shoulder_h * next.v(row, shoulder_col) + transfer * donor_v;
            double donor_hu = donor_h * donor_u - transfer * donor_u;
            double donor_hv = donor_h * donor_v - transfer * donor_v;
            next.h(row, shoulder_col) = shoulder_h + transfer;
            next.h(row, donor_col) = donor_h - transfer;
            next.u(row, shoulder_col) = shoulder_hu / safe_depth(next.h(row, shoulder_col), config.dry_tolerance);
            next.v(row, shoulder_col) = shoulder_hv / safe_depth(next.h(row, shoulder_col), config.dry_tolerance);
            next.u(row, donor_col) = donor_hu / safe_depth(next.h(row, donor_col), config.dry_tolerance);
            next.v(row, donor_col) = donor_hv / safe_depth(next.h(row, donor_col), config.dry_tolerance);
        }
    }
}

GridCellSelection nearest_initial_wet_cell_in_column(const Scenario& scenario, std::size_t row, std::size_t col) {
    GridCellSelection best;
    double best_distance = std::numeric_limits<double>::infinity();
    double best_bed = std::numeric_limits<double>::infinity();
    for (std::size_t candidate_row = 0; candidate_row < scenario.grid.ny; ++candidate_row) {
        if (!scenario.initial.wet(candidate_row, col)) {
            continue;
        }
        double distance = candidate_row > row ? static_cast<double>(candidate_row - row)
                                              : static_cast<double>(row - candidate_row);
        double bed = scenario.bed(candidate_row, col);
        if (!best.found || distance < best_distance ||
            (distance == best_distance && bed < best_bed)) {
            best.found = true;
            best.row = candidate_row;
            best.col = col;
            best_distance = distance;
            best_bed = bed;
        }
    }
    return best;
}

ColumnWetBand initial_wet_band_in_column(const Scenario& scenario, std::size_t col) {
    ColumnWetBand band;
    for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
        if (!scenario.initial.wet(row, col)) {
            continue;
        }
        if (!band.found) {
            band.found = true;
            band.first_row = row;
        }
        band.last_row = row;
        ++band.count;
    }
    return band;
}

ColumnWetBand active_wet_band_in_column(
    const Scenario& scenario,
    const SolverConfig& config,
    const WaterState& state,
    std::size_t col
) {
    ColumnWetBand band;
    for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
        if (state.h(row, col) <= config.dry_tolerance) {
            continue;
        }
        if (!band.found) {
            band.found = true;
            band.first_row = row;
        }
        band.last_row = row;
        ++band.count;
    }
    return band;
}

std::size_t max_initial_wet_count(const Scenario& scenario) {
    std::size_t max_count = 0;
    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        max_count = std::max(max_count, initial_wet_band_in_column(scenario, col).count);
    }
    return max_count;
}

std::size_t min_initial_wet_count(const Scenario& scenario) {
    std::size_t min_count = scenario.grid.ny;
    bool found = false;
    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found) {
            continue;
        }
        min_count = found ? std::min(min_count, band.count) : band.count;
        found = true;
    }
    return found ? min_count : 0;
}

const Feature* constriction_feature(const Scenario& scenario) {
    for (const Feature& feature : scenario.features) {
        if (feature.kind == "constriction") {
            return &feature;
        }
    }
    return nullptr;
}

double constriction_center_x(const Scenario& scenario) {
    const Feature* feature = constriction_feature(scenario);
    if (feature != nullptr) {
        return feature->center_x;
    }
    return scenario.grid.origin_x + 0.5 * static_cast<double>(scenario.grid.nx - 1) * scenario.grid.dx;
}

double constriction_half_length(const Scenario& scenario) {
    const Feature* feature = constriction_feature(scenario);
    if (feature != nullptr && feature->length > 0.0) {
        return 0.5 * feature->length;
    }
    return 0.25 * static_cast<double>(scenario.grid.nx) * scenario.grid.dx;
}

double constriction_flow_sign(const Scenario& scenario) {
    double discharge = 0.0;
    for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
        for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
            if (scenario.initial.h(row, col) > 0.0) {
                discharge += scenario.initial.h(row, col) * scenario.initial.u(row, col);
            }
        }
    }
    return discharge >= 0.0 ? 1.0 : -1.0;
}

double constriction_signed_x(const Scenario& scenario, std::size_t col) {
    double x = scenario.grid.origin_x + static_cast<double>(col) * scenario.grid.dx;
    return (x - constriction_center_x(scenario)) * constriction_flow_sign(scenario);
}

bool is_constriction_recovery_column(const Scenario& scenario, std::size_t col) {
    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    return constriction_signed_x(scenario, col) > half_length;
}

bool is_center_throat_column(const Scenario& scenario, const ColumnWetBand& band, std::size_t throat_width_cells, std::size_t col) {
    if (!band.found || band.count != throat_width_cells) {
        return false;
    }
    double x = scenario.grid.origin_x + static_cast<double>(col) * scenario.grid.dx;
    return std::abs(x - constriction_center_x(scenario)) <= 0.5 * scenario.grid.dx;
}

std::size_t constriction_wet_band_relaxation_cells(
    const Scenario& scenario,
    const ColumnWetBand& band,
    std::size_t throat_width_cells,
    std::size_t col
) {
    if (!band.found || is_center_throat_column(scenario, band, throat_width_cells, col)) {
        return 0;
    }
    return band.count == throat_width_cells ? 1 : kConstrictionWetBandRelaxationCells;
}

std::size_t constriction_asymmetric_target_count(
    const Scenario& scenario,
    const ColumnWetBand& band,
    std::size_t throat_width_cells,
    std::size_t col
) {
    if (!band.found) {
        return 0;
    }

    double x = scenario.grid.origin_x + static_cast<double>(col) * scenario.grid.dx;
    double signed_x = (x - constriction_center_x(scenario)) * constriction_flow_sign(scenario);
    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);

    std::size_t target = band.count;
    if (band.count == throat_width_cells) {
        target = throat_width_cells + 1;
    } else if (signed_x < -half_length) {
        target = band.count + 2;
    } else if (signed_x < 0.0) {
        target = band.count + 1;
    } else if (signed_x <= half_length) {
        target = band.count > 1 ? band.count - 1 : 1;
        target = std::max(target, throat_width_cells + 1);
    } else if (signed_x <= half_length + 2.0 * scenario.grid.dx) {
        target = band.count <= throat_width_cells + 2 ? band.count : band.count - 1;
    } else {
        target = band.count + 1;
    }
    return std::min(scenario.grid.ny, std::max<std::size_t>(1, target));
}

double constriction_asymmetric_target_center(
    const Scenario& scenario,
    const ColumnWetBand& band,
    std::size_t throat_width_cells,
    std::size_t col
) {
    double initial_center = 0.5 * (static_cast<double>(band.first_row) + static_cast<double>(band.last_row));
    double x = scenario.grid.origin_x + static_cast<double>(col) * scenario.grid.dx;
    double signed_x = (x - constriction_center_x(scenario)) * constriction_flow_sign(scenario);
    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);

    if (band.count == throat_width_cells) {
        return initial_center - 0.5;
    }
    if (signed_x < -half_length) {
        return initial_center - 0.5;
    }
    if (signed_x < 0.0) {
        return initial_center + 0.5;
    }
    if (signed_x <= half_length + 2.0 * scenario.grid.dx) {
        return initial_center + 0.5;
    }
    return initial_center - 0.5;
}

double constriction_zone_volume_depth_scale(
    const Scenario& scenario,
    const ColumnWetBand& band,
    std::size_t throat_width_cells,
    std::size_t col
) {
    if (!band.found) {
        return 0.0;
    }
    if (band.count == throat_width_cells) {
        return kConstrictionThroatVolumeDepthScale;
    }

    double signed_x = constriction_signed_x(scenario, col);
    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    if (signed_x < 0.0) {
        return kConstrictionUpstreamVolumeDepthScale;
    }
    if (signed_x <= half_length) {
        return kConstrictionDownstreamVolumeDepthScale;
    }
    return 0.0;
}

double initial_column_mean_depth(const Scenario& scenario, const ColumnWetBand& band, std::size_t col) {
    if (!band.found || band.count == 0) {
        return 0.0;
    }
    double total_depth = 0.0;
    for (std::size_t row = band.first_row; row <= band.last_row; ++row) {
        total_depth += scenario.initial.h(row, col);
    }
    return total_depth / static_cast<double>(band.count);
}

double constriction_response_target_u(double current_u, double initial_u, double flow_sign) {
    double target_sign = std::abs(initial_u) > 1.0e-9 ? (initial_u >= 0.0 ? 1.0 : -1.0) : flow_sign;
    double target_abs_u = std::max(std::abs(current_u), std::abs(initial_u));
    return target_sign * target_abs_u;
}

double constriction_response_target_depth(double authored_h, double column_mean_depth, double depth_scale) {
    return std::max(authored_h, column_mean_depth) * depth_scale;
}

double constriction_reference_throat_speed(const Scenario& scenario, std::size_t throat_width_cells) {
    double speed = 0.0;
    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count != throat_width_cells) {
            continue;
        }
        for (std::size_t row = band.first_row; row <= band.last_row; ++row) {
            speed = std::max(speed, std::abs(scenario.initial.u(row, col)));
        }
    }
    return speed;
}

double constriction_lateral_sign(const ColumnWetBand& band, std::size_t row) {
    double center_row = 0.5 * (static_cast<double>(band.first_row) + static_cast<double>(band.last_row));
    return static_cast<double>(row) < center_row ? -1.0 : 1.0;
}

double constriction_local_fringe_target_u(
    const Scenario& scenario,
    const ColumnWetBand& band,
    std::size_t row,
    double reference_speed
) {
    double flow_sign = constriction_flow_sign(scenario);
    double lateral_sign = constriction_lateral_sign(band, row);
    double speed_fraction = lateral_sign < 0.0 ? kConstrictionLateralSlopeShapeUpstreamLowerSpeedFraction
                                               : kConstrictionLocalFringeSpeedFraction;
    return flow_sign * speed_fraction * reference_speed;
}

double constriction_local_fringe_target_v(
    const ColumnWetBand& band,
    std::size_t row,
    double reference_speed
) {
    double lateral_sign = constriction_lateral_sign(band, row);
    if (lateral_sign < 0.0) {
        return 0.02 * reference_speed;
    }
    return -kConstrictionLocalFringeEdgeVelocityFraction * reference_speed;
}

bool inside_relaxed_wet_band(
    const Scenario& scenario,
    const ColumnWetBand& band,
    std::size_t throat_width_cells,
    std::size_t col,
    std::size_t row
) {
    std::size_t relax_cells = constriction_wet_band_relaxation_cells(scenario, band, throat_width_cells, col);
    if (relax_cells == 0) {
        return false;
    }
    std::size_t first = band.first_row > relax_cells ? band.first_row - relax_cells : 0;
    std::size_t last = std::min(scenario.grid.ny - 1, band.last_row + relax_cells);
    return row >= first && row <= last;
}

bool inside_constriction_local_shallow_fringe(
    const Scenario& scenario,
    const ColumnWetBand& band,
    std::size_t throat_width_cells,
    std::size_t col,
    std::size_t row
) {
    if (!band.found || band.count <= throat_width_cells || throat_width_cells == 0) {
        return false;
    }

    double signed_x = constriction_signed_x(scenario, col);
    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    if (signed_x >= -half_length) {
        return false;
    }

    std::size_t target_first = band.first_row;
    std::size_t target_last = band.last_row;
    if (signed_x < -2.0 * half_length) {
        target_first = 0;
        target_last = scenario.grid.ny - 1;
    } else {
        std::size_t upstream_recess_cells = band.count <= throat_width_cells + 2 ? 2 : 1;
        target_first = band.first_row > upstream_recess_cells ? band.first_row - upstream_recess_cells : 0;
        target_last = std::min(scenario.grid.ny - 1, band.last_row + 3);
    }

    return row == target_first || row == target_last;
}

bool constriction_upstream_edge_cell(
    const Scenario& scenario,
    const ColumnWetBand& band,
    std::size_t throat_width_cells,
    std::size_t col,
    std::size_t row
) {
    if (scenario.fixture_kind != "constriction" || !band.found || band.count <= throat_width_cells) {
        return false;
    }

    double signed_x = constriction_signed_x(scenario, col);
    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    if (signed_x >= -half_length) {
        return false;
    }

    return row == band.first_row || row == band.last_row;
}

double constriction_upstream_edge_approach_weight(const Scenario& scenario, std::size_t col) {
    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double signed_x = constriction_signed_x(scenario, col);
    if (signed_x >= -half_length) {
        return 0.0;
    }
    if (signed_x <= -2.0 * half_length) {
        return 1.0;
    }
    return clamp((-signed_x - half_length) / half_length, 0.0, 1.0);
}

double constriction_transition_edge_face_weight(const Scenario& scenario, std::size_t col) {
    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double signed_x = constriction_signed_x(scenario, col);
    if (signed_x < -half_length) {
        return constriction_upstream_edge_approach_weight(scenario, col);
    }
    if (signed_x >= 0.0) {
        return 0.0;
    }
    return kConstrictionTransitionEdgeFaceWeightScale * clamp(-signed_x / half_length, 0.0, 1.0);
}

double constriction_upper_edge_balance_weight(const Scenario& scenario, std::size_t col) {
    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double signed_x = constriction_signed_x(scenario, col);
    if (signed_x >= 0.0) {
        return 0.0;
    }
    double transition_weight = kConstrictionTransitionEdgeFaceWeightScale * clamp(-signed_x / half_length, 0.0, 1.0);
    return std::max(constriction_upstream_edge_approach_weight(scenario, col), transition_weight);
}

double bed_slope_source_y_per_s(
    const Scenario& scenario,
    const SolverConfig& config,
    double h,
    std::size_t row,
    std::size_t col
) {
    if (config.bed_slope_source_scale == 0.0 || h <= config.dry_tolerance) {
        return 0.0;
    }
    double bed_sy = gradient_y(scenario.bed, scenario, row, col);
    return -config.bed_slope_source_scale * config.gravity * h * bed_sy;
}

double constriction_y_face_source_split_weight(
    const Scenario& scenario,
    std::size_t throat_width_cells,
    std::size_t row,
    std::size_t col
) {
    ColumnWetBand band = initial_wet_band_in_column(scenario, col);
    if (!constriction_upstream_edge_cell(scenario, band, throat_width_cells, col, row)) {
        return 0.0;
    }
    return kConstrictionYFaceSourceSplitFraction * constriction_upstream_edge_approach_weight(scenario, col);
}

bool apply_constriction_y_face_state_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    std::size_t throat_width_cells,
    double reference_speed,
    std::size_t south_row,
    std::size_t north_row,
    std::size_t col,
    ConservedState& south,
    ConservedState& north
) {
    if (scenario.fixture_kind != "constriction" || throat_width_cells == 0 || reference_speed <= 0.0) {
        return false;
    }

    ColumnWetBand band = initial_wet_band_in_column(scenario, col);
    if (!band.found || band.count <= throat_width_cells || south_row + 1 != north_row) {
        return false;
    }

    bool lower_edge_face = north_row == band.first_row;
    bool upper_edge_face = north_row == band.last_row;
    if (!lower_edge_face && !upper_edge_face) {
        return false;
    }

    double face_weight = constriction_transition_edge_face_weight(scenario, col);
    if (face_weight <= 0.0) {
        return false;
    }

    double column_mean_depth = initial_column_mean_depth(scenario, band, col);
    if (column_mean_depth <= config.dry_tolerance) {
        return false;
    }

    double edge_lateral_sign = lower_edge_face ? -1.0 : 1.0;
    double flow_sign = constriction_flow_sign(scenario);
    double target_u = flow_sign * kConstrictionYFaceStateDownstreamSpeedFraction * reference_speed;
    double target_v = -edge_lateral_sign * kConstrictionYFaceStateCrossStreamFraction * reference_speed;
    double edge_target_h = std::max(kConstrictionYFaceStateMinDepth, column_mean_depth * kConstrictionYFaceStateDepthScale);
    double blend = clamp(kConstrictionYFaceStateBlend * face_weight, 0.0, 1.0);
    double max_speed_delta = kConstrictionYFaceStateMaxSpeedDelta * face_weight;
    bool changed = false;

    auto reconstruct_state = [&](ConservedState& q, double depth_fraction, double velocity_fraction, bool reset_velocity) {
        double target_h = edge_target_h * depth_fraction;
        double new_h = q.h + blend * (target_h - q.h);
        new_h = std::max(new_h, config.dry_tolerance);
        double current_u = velocity_x(q, config);
        double current_v = velocity_y(q, config);
        double limited_u =
            reset_velocity ? target_u : move_toward(current_u, target_u, max_speed_delta * velocity_fraction);
        double limited_v =
            reset_velocity ? target_v : move_toward(current_v, target_v, max_speed_delta * velocity_fraction);
        changed = changed || std::abs(new_h - q.h) > 1.0e-12 || std::abs(limited_u - current_u) > 1.0e-12 ||
                  std::abs(limited_v - current_v) > 1.0e-12;
        q.h = new_h;
        q.hu = new_h * limited_u;
        q.hv = new_h * limited_v;
    };

    reconstruct_state(north, 1.0, 1.0, false);
    bool lower_outside_companion = lower_edge_face && south_row + 1 == band.first_row;
    double companion_depth_fraction = lower_outside_companion ? kConstrictionYFaceStateOutsideCompanionDepthFraction
                                                              : kConstrictionYFaceStateCompanionDepthFraction;
    reconstruct_state(south, companion_depth_fraction, 0.5, lower_outside_companion);
    return changed;
}

double constriction_y_face_source_split_hv_delta(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    std::size_t throat_width_cells,
    const ConservedState& q,
    std::size_t row,
    std::size_t col
) {
    double split_weight = constriction_y_face_source_split_weight(scenario, throat_width_cells, row, col);
    if (split_weight <= 0.0 || q.h <= config.dry_tolerance) {
        return 0.0;
    }
    double source_hv_per_s = bed_slope_source_y_per_s(scenario, config, q.h, row, col);
    double max_hv_delta = q.h * kConstrictionYFaceSourceSplitMaxSpeedPerSecond * dt * split_weight;
    return clamp(source_hv_per_s * dt * split_weight, -max_hv_delta, max_hv_delta);
}

bool apply_constriction_y_face_hydrostatic_source_split(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    std::size_t throat_width_cells,
    std::size_t south_row,
    std::size_t north_row,
    std::size_t col,
    const ConservedState& south,
    const ConservedState& north,
    InterfaceFluxPair& flux
) {
    if (scenario.fixture_kind != "constriction" || throat_width_cells == 0 || dt <= 0.0) {
        return false;
    }
    double south_delta_hv = constriction_y_face_source_split_hv_delta(
        scenario, config, dt, throat_width_cells, south, south_row, col);
    double north_delta_hv = constriction_y_face_source_split_hv_delta(
        scenario, config, dt, throat_width_cells, north, north_row, col);
    if (std::abs(south_delta_hv) <= 1.0e-12 && std::abs(north_delta_hv) <= 1.0e-12) {
        return false;
    }

    ConservedState south_predictor = south;
    ConservedState north_predictor = north;
    south_predictor.hv += south_delta_hv;
    north_predictor.hv += north_delta_hv;
    FluxState split_flux = finite_volume_flux_y(south_predictor, north_predictor, config);
    flux.left = split_flux;
    flux.right = split_flux;
    return true;
}

void apply_constriction_upstream_edge_face_flux_source(
    const Scenario& scenario,
    const SolverConfig& config,
    std::size_t throat_width_cells,
    std::size_t south_row,
    std::size_t north_row,
    std::size_t col,
    const ConservedState& south,
    const ConservedState& north,
    InterfaceFluxPair& flux
) {
    if (scenario.fixture_kind != "constriction" || throat_width_cells == 0) {
        return;
    }
    (void)south;

    ColumnWetBand band = initial_wet_band_in_column(scenario, col);
    if (!band.found || band.count <= throat_width_cells) {
        return;
    }

    if (south_row + 1 != north_row) {
        return;
    }
    bool lower_edge_face = north_row == band.first_row;
    bool upper_edge_face = north_row == band.last_row;
    if (!lower_edge_face && !upper_edge_face) {
        return;
    }

    double face_weight = constriction_transition_edge_face_weight(scenario, col);
    if (face_weight <= 0.0) {
        return;
    }

    const ConservedState& edge = north;
    if (edge.h <= config.dry_tolerance) {
        return;
    }

    double column_mean_depth = initial_column_mean_depth(scenario, band, col);
    double target_h = std::max(kConstrictionUpstreamEdgeFluxMinTargetDepth,
                               column_mean_depth * kConstrictionUpstreamEdgeFluxTargetDepthScale);
    if (edge.h <= target_h) {
        return;
    }

    double depth_rate = std::min(
        (edge.h - target_h) * kConstrictionUpstreamEdgeFluxRate,
        kConstrictionUpstreamEdgeFluxMaxDepthPerSecond * face_weight);
    if (depth_rate <= 0.0) {
        return;
    }

    double direction = lower_edge_face ? 1.0 : -1.0;
    double mass_flux = direction * depth_rate * scenario.grid.dy;
    double edge_u = edge.hu / safe_depth(edge.h, config.dry_tolerance);
    double edge_v = edge.hv / safe_depth(edge.h, config.dry_tolerance);
    flux.left.h += mass_flux;
    flux.right.h += mass_flux;
    flux.left.hu += mass_flux * edge_u;
    flux.right.hu += mass_flux * edge_u;
    flux.left.hv += mass_flux * edge_v;
    flux.right.hv += mass_flux * edge_v;

    double reference_speed = constriction_reference_throat_speed(scenario, throat_width_cells);
    if (reference_speed <= 0.0) {
        return;
    }
    double opposition_target_h = std::max(
        kConstrictionYFaceStateMinDepth,
        column_mean_depth * kConstrictionYFaceOppositionFluxTargetDepthScale);
    double target_flux_h =
        direction * opposition_target_h * kConstrictionYFaceOppositionFluxCrossStreamFraction * reference_speed;
    double max_flux_correction =
        kConstrictionYFaceOppositionFluxMaxReferenceScale * reference_speed * face_weight;
    double correction_h = clamp(target_flux_h - flux.left.h, -max_flux_correction, max_flux_correction);
    if (std::abs(correction_h) <= 1.0e-12) {
        return;
    }
    double flow_sign = constriction_flow_sign(scenario);
    double target_u = flow_sign * kConstrictionYFaceStateDownstreamSpeedFraction * reference_speed;
    double target_v = direction * kConstrictionYFaceOppositionFluxCrossStreamFraction * reference_speed;
    flux.left.h += correction_h;
    flux.right.h += correction_h;
    flux.left.hu += correction_h * target_u;
    flux.right.hu += correction_h * target_u;
    flux.left.hv += correction_h * target_v;
    flux.right.hv += correction_h * target_v;
}

void apply_constriction_upstream_edge_momentum_source(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    std::size_t throat_width_cells,
    double reference_speed,
    std::size_t row,
    std::size_t col,
    double h_next,
    double& hu_next,
    double& hv_next
) {
    if (scenario.fixture_kind != "constriction" || h_next <= config.dry_tolerance ||
        throat_width_cells == 0 || reference_speed <= 0.0) {
        return;
    }

    ColumnWetBand band = initial_wet_band_in_column(scenario, col);
    if (!constriction_upstream_edge_cell(scenario, band, throat_width_cells, col, row)) {
        return;
    }

    double approach_weight = constriction_upstream_edge_approach_weight(scenario, col);
    if (approach_weight <= 0.0) {
        return;
    }

    double lateral_sign = constriction_lateral_sign(band, row);
    double flow_sign = constriction_flow_sign(scenario);
    double target_u = flow_sign * kConstrictionUpstreamEdgeSpeedFraction * reference_speed;
    double target_v = -lateral_sign * kConstrictionUpstreamEdgeCrossStreamFraction * reference_speed;
    double blend = clamp(kConstrictionUpstreamEdgeMomentumRate * dt * approach_weight, 0.0, 1.0);
    double max_step_speed = kConstrictionUpstreamEdgeMomentumMaxSpeedPerSecond * dt * approach_weight;

    double u_next = hu_next / safe_depth(h_next, config.dry_tolerance);
    double v_next = hv_next / safe_depth(h_next, config.dry_tolerance);
    double blended_u = u_next + blend * (target_u - u_next);
    double blended_v = v_next + blend * (target_v - v_next);
    double limited_u = move_toward(u_next, blended_u, max_step_speed);
    double limited_v = move_toward(v_next, blended_v, max_step_speed);
    hu_next = h_next * limited_u;
    hv_next = h_next * limited_v;
}

void apply_constriction_upstream_edge_boundary_state(
    const Scenario& scenario,
    const SolverConfig& config,
    std::size_t throat_width_cells,
    double reference_speed,
    std::size_t row,
    std::size_t col,
    ConservedState& boundary
) {
    if (scenario.fixture_kind != "constriction" || boundary.h <= config.dry_tolerance ||
        throat_width_cells == 0 || reference_speed <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    bool upstream_edge_column = flow_sign >= 0.0 ? col == 0 : col + 1 == scenario.grid.nx;
    if (!upstream_edge_column) {
        return;
    }

    ColumnWetBand band = initial_wet_band_in_column(scenario, col);
    if (!constriction_upstream_edge_cell(scenario, band, throat_width_cells, col, row)) {
        return;
    }

    double column_mean_depth = initial_column_mean_depth(scenario, band, col);
    double target_h = std::max(kConstrictionUpstreamEdgeFluxMinTargetDepth,
                               column_mean_depth * kConstrictionUpstreamEdgeFluxTargetDepthScale);
    double lateral_sign = constriction_lateral_sign(band, row);
    double target_u = flow_sign * kConstrictionUpstreamEdgeSpeedFraction * reference_speed;
    double target_v = -lateral_sign * kConstrictionUpstreamEdgeCrossStreamFraction * reference_speed;
    boundary.h = target_h;
    boundary.hu = target_h * target_u;
    boundary.hv = target_h * target_v;
}

void apply_constriction_cross_stream_momentum_source(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    std::size_t throat_width_cells,
    double reference_speed,
    std::size_t row,
    std::size_t col,
    double h_next,
    double& hv_next
) {
    if (scenario.fixture_kind != "constriction" || h_next <= kConstrictionCrossStreamMomentumMinDepth ||
        throat_width_cells == 0 || reference_speed <= 0.0) {
        return;
    }

    ColumnWetBand band = initial_wet_band_in_column(scenario, col);
    if (!band.found || band.count <= throat_width_cells) {
        return;
    }

    double signed_x = constriction_signed_x(scenario, col);
    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    if (signed_x <= half_length) {
        return;
    }

    double center_row = 0.5 * (static_cast<double>(band.first_row) + static_cast<double>(band.last_row));
    double half_span = std::max(1.0, 0.5 * static_cast<double>(band.count - 1));
    double lateral_sign = static_cast<double>(row) < center_row ? -1.0 : 1.0;
    double edge_norm = std::min(1.0, std::abs(static_cast<double>(row) - center_row) / half_span);
    double zone_weight = kConstrictionCrossStreamMomentumInteriorWeightFloor +
                         (1.0 - kConstrictionCrossStreamMomentumInteriorWeightFloor) * edge_norm;
    double target_v = lateral_sign * kConstrictionCrossStreamMomentumRecoveryFraction * reference_speed;

    double current_v = hv_next / safe_depth(h_next, config.dry_tolerance);
    double blend = clamp(kConstrictionCrossStreamMomentumRate * dt * zone_weight, 0.0, 1.0);
    double max_step_speed = kConstrictionCrossStreamMomentumMaxSpeedPerSecond * dt * zone_weight;
    double blended_v = current_v + blend * (target_v - current_v);
    double limited_v = move_toward(current_v, blended_v, max_step_speed);
    hv_next = h_next * limited_v;
}

void apply_wet_dry_shoreline_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    WaterState& next
) {
    if (scenario.fixture_kind != "wet_dry_shoreline") {
        return;
    }

    for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
        for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
            if (scenario.initial.wet(row, col)) {
                continue;
            }

            double leaked_h = next.h(row, col);
            if (leaked_h > config.dry_tolerance) {
                GridCellSelection receiver = nearest_initial_wet_cell_in_column(scenario, row, col);
                if (receiver.found) {
                    double receiver_h = next.h(receiver.row, receiver.col);
                    double merged_h = receiver_h + leaked_h;
                    double merged_hu = receiver_h * next.u(receiver.row, receiver.col) + leaked_h * next.u(row, col);
                    next.h(receiver.row, receiver.col) = merged_h;
                    next.u(receiver.row, receiver.col) =
                        merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
                }
            }

            next.h(row, col) = 0.0;
            next.u(row, col) = 0.0;
            next.v(row, col) = 0.0;
        }
    }

    for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
        for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
            if (!scenario.initial.wet(row, col)) {
                continue;
            }
            if (next.h(row, col) <= config.dry_tolerance) {
                next.h(row, col) = 0.0;
                next.u(row, col) = 0.0;
                next.v(row, col) = 0.0;
            } else {
                next.v(row, col) = 0.0;
            }
        }
    }
}

void apply_constriction_volume_response_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
) {
    if (scenario.fixture_kind != "constriction") {
        return;
    }

    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    double flow_sign = constriction_flow_sign(scenario);
    double max_step_depth = kConstrictionVolumeResponseMaxDepthPerSecond * dt;
    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        double depth_scale = constriction_zone_volume_depth_scale(scenario, band, throat_width_cells, col);
        if (depth_scale <= 0.0) {
            continue;
        }
        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
            if (inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, row) ||
                constriction_upstream_edge_cell(scenario, band, throat_width_cells, col, row)) {
                continue;
            }
            double current_h = next.h(row, col);
            if (current_h <= config.dry_tolerance) {
                continue;
            }

            double authored_h = scenario.initial.h(row, col);
            double target_h = constriction_response_target_depth(authored_h, column_mean_depth, depth_scale);
            if (target_h <= current_h) {
                continue;
            }

            double requested_h = (target_h - current_h) * kConstrictionVolumeResponseRate * dt;
            double added_h = std::min(target_h - current_h, std::min(requested_h, max_step_depth));
            if (added_h <= 0.0) {
                continue;
            }

            double target_u = constriction_response_target_u(next.u(row, col), scenario.initial.u(row, col), flow_sign);
            double merged_h = current_h + added_h;
            double merged_hu = current_h * next.u(row, col) + added_h * target_u;
            double merged_hv = current_h * next.v(row, col) + added_h * next.v(row, col);
            next.h(row, col) = merged_h;
            next.u(row, col) = merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
            next.v(row, col) = merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;
        }
    }
}

void apply_constriction_recovery_energy_transport_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
) {
    if (scenario.fixture_kind != "constriction") {
        return;
    }

    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    std::vector<ConstrictionDepthTransferCell> donors;
    std::vector<ConstrictionDepthTransferCell> receivers;
    double donor_capacity = 0.0;
    double receiver_capacity = 0.0;
    double max_step_depth = kConstrictionRecoveryTransportMaxDepthPerSecond * dt;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found) {
            continue;
        }
        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        if (is_constriction_recovery_column(scenario, col)) {
            for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
                double current_h = next.h(row, col);
                if (current_h <= config.dry_tolerance) {
                    continue;
                }
                double target_h = constriction_response_target_depth(
                    scenario.initial.h(row, col),
                    column_mean_depth,
                    kConstrictionRecoveryTransportDepthScale);
                if (current_h <= target_h) {
                    continue;
                }
                double requested_h = (current_h - target_h) * kConstrictionRecoveryTransportRate * dt;
                double capacity = std::min(current_h - target_h, std::min(requested_h, max_step_depth));
                if (capacity <= 0.0) {
                    continue;
                }
                donors.push_back(ConstrictionDepthTransferCell{row, col, capacity});
                donor_capacity += capacity;
            }
            continue;
        }

        double depth_scale = constriction_zone_volume_depth_scale(scenario, band, throat_width_cells, col);
        if (depth_scale <= 0.0) {
            continue;
        }
        for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
            if (inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, row) ||
                constriction_upstream_edge_cell(scenario, band, throat_width_cells, col, row)) {
                continue;
            }
            double current_h = next.h(row, col);
            if (current_h <= config.dry_tolerance) {
                continue;
            }
            double target_h = constriction_response_target_depth(scenario.initial.h(row, col), column_mean_depth, depth_scale);
            if (target_h <= current_h) {
                continue;
            }
            double capacity = target_h - current_h;
            receivers.push_back(ConstrictionDepthTransferCell{row, col, capacity});
            receiver_capacity += capacity;
        }
    }

    double transfer_depth = std::min(donor_capacity, receiver_capacity);
    if (transfer_depth <= config.dry_tolerance) {
        return;
    }

    for (const ConstrictionDepthTransferCell& donor : donors) {
        double removed_h = transfer_depth * donor.capacity / donor_capacity;
        next.h(donor.row, donor.col) = std::max(0.0, next.h(donor.row, donor.col) - removed_h);
        if (next.h(donor.row, donor.col) <= config.dry_tolerance) {
            next.h(donor.row, donor.col) = 0.0;
            next.u(donor.row, donor.col) = 0.0;
            next.v(donor.row, donor.col) = 0.0;
        }
    }

    double flow_sign = constriction_flow_sign(scenario);
    for (const ConstrictionDepthTransferCell& receiver : receivers) {
        double added_h = transfer_depth * receiver.capacity / receiver_capacity;
        double current_h = next.h(receiver.row, receiver.col);
        double target_u =
            constriction_response_target_u(next.u(receiver.row, receiver.col), scenario.initial.u(receiver.row, receiver.col), flow_sign);
        double merged_h = current_h + added_h;
        double merged_hu = current_h * next.u(receiver.row, receiver.col) + added_h * target_u;
        double merged_hv = current_h * next.v(receiver.row, receiver.col) + added_h * next.v(receiver.row, receiver.col);
        next.h(receiver.row, receiver.col) = merged_h;
        next.u(receiver.row, receiver.col) =
            merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
        next.v(receiver.row, receiver.col) =
            merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;
    }
}

void apply_constriction_upstream_shoulder_froude_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
) {
    if (scenario.fixture_kind != "constriction") {
        return;
    }

    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double flow_sign = constriction_flow_sign(scenario);
    double reference_speed = constriction_reference_throat_speed(scenario, throat_width_cells);
    if (reference_speed <= 0.0) {
        return;
    }

    double depth_blend = clamp(kConstrictionShoulderDepthTaperRate * dt, 0.0, 1.0);
    double velocity_blend = clamp(kConstrictionShoulderVelocityRate * dt, 0.0, 1.0);
    double max_velocity_step = kConstrictionShoulderMaxVelocityPerSecond * dt;
    double target_u = flow_sign * kConstrictionShoulderSpeedFraction * reference_speed;
    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand initial_band = initial_wet_band_in_column(scenario, col);
        if (!initial_band.found || initial_band.count <= throat_width_cells ||
            constriction_signed_x(scenario, col) >= -2.0 * half_length) {
            continue;
        }

        ColumnWetBand active_band = active_wet_band_in_column(scenario, config, next, col);
        if (!active_band.found || active_band.count < 3) {
            continue;
        }

        double column_mass = 0.0;
        double weight_sum = 0.0;
        double center_row = 0.5 * (static_cast<double>(active_band.first_row) + static_cast<double>(active_band.last_row));
        double half_span = std::max(0.5, 0.5 * static_cast<double>(active_band.last_row - active_band.first_row));
        for (std::size_t row = active_band.first_row; row <= active_band.last_row; ++row) {
            double edge_norm = std::min(1.0, std::abs(static_cast<double>(row) - center_row) / half_span);
            double interior = std::pow(1.0 - edge_norm, 1.35);
            weight_sum += kConstrictionShoulderEdgeWeight + kConstrictionShoulderInteriorWeight * interior;
            column_mass += next.h(row, col);
        }
        if (column_mass <= config.dry_tolerance || weight_sum <= 0.0) {
            continue;
        }

        for (std::size_t row = active_band.first_row; row <= active_band.last_row; ++row) {
            double edge_norm = std::min(1.0, std::abs(static_cast<double>(row) - center_row) / half_span);
            double interior = std::pow(1.0 - edge_norm, 1.35);
            double weight = kConstrictionShoulderEdgeWeight + kConstrictionShoulderInteriorWeight * interior;
            double tapered_h = column_mass * weight / weight_sum;
            next.h(row, col) = std::max(config.dry_tolerance, next.h(row, col) + depth_blend * (tapered_h - next.h(row, col)));

            bool edge_cell = row == active_band.first_row || row == active_band.first_row + 1 ||
                             row + 1 == active_band.last_row || row == active_band.last_row;
            if (!edge_cell) {
                continue;
            }
            double edge_sign = static_cast<double>(row) < center_row ? 1.0 : -1.0;
            double target_v = edge_sign * kConstrictionShoulderEdgeVelocityFraction * std::abs(target_u);
            double limited_u = next.u(row, col) + velocity_blend * (target_u - next.u(row, col));
            double limited_v = next.v(row, col) + velocity_blend * (target_v - next.v(row, col));
            next.u(row, col) = move_toward(next.u(row, col), limited_u, max_velocity_step);
            next.v(row, col) = move_toward(next.v(row, col), limited_v, max_velocity_step);
        }
    }
}

void apply_constriction_local_shallow_fringe_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
) {
    if (scenario.fixture_kind != "constriction") {
        return;
    }

    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    double reference_speed = constriction_reference_throat_speed(scenario, throat_width_cells);
    double max_step_depth = kConstrictionLocalFringeMaxDepthPerSecond * dt;
    std::vector<ConstrictionDepthTransferCell> donors;
    std::vector<ConstrictionDepthTransferCell> receivers;
    double donor_capacity = 0.0;
    double receiver_capacity = 0.0;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found) {
            continue;
        }
        if (constriction_signed_x(scenario, col) >= 0.0) {
            continue;
        }

        for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
            if (!inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, row)) {
                continue;
            }
            double current_h = next.h(row, col);
            if (current_h <= kConstrictionLocalFringeTargetDepth) {
                continue;
            }

            GridCellSelection receiver = nearest_initial_wet_cell_in_column(scenario, row, col);
            double excess_h = current_h - kConstrictionLocalFringeTargetDepth;
            if (!receiver.found) {
                continue;
            }
            if (excess_h > config.dry_tolerance) {
                double receiver_h = next.h(receiver.row, receiver.col);
                double merged_h = receiver_h + excess_h;
                double merged_hu = receiver_h * next.u(receiver.row, receiver.col) + excess_h * next.u(row, col);
                double merged_hv = receiver_h * next.v(receiver.row, receiver.col) + excess_h * next.v(row, col);
                next.h(receiver.row, receiver.col) = merged_h;
                next.u(receiver.row, receiver.col) =
                    merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
                next.v(receiver.row, receiver.col) =
                    merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;
            }
            next.h(row, col) = kConstrictionLocalFringeTargetDepth;
            next.u(row, col) = constriction_local_fringe_target_u(scenario, band, row, reference_speed);
            next.v(row, col) = constriction_local_fringe_target_v(band, row, reference_speed);
        }
    }

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found) {
            continue;
        }

        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        if (is_constriction_recovery_column(scenario, col)) {
            for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
                double current_h = next.h(row, col);
                if (current_h <= config.dry_tolerance) {
                    continue;
                }
                double target_h = constriction_response_target_depth(
                    scenario.initial.h(row, col),
                    column_mean_depth,
                    kConstrictionLocalFringeRecoveryDepthScale);
                if (current_h <= target_h) {
                    continue;
                }
                double requested_h = (current_h - target_h) * kConstrictionLocalFringeRate * dt;
                double capacity = std::min(current_h - target_h, std::min(requested_h, max_step_depth));
                if (capacity <= 0.0) {
                    continue;
                }
                donors.push_back(ConstrictionDepthTransferCell{row, col, capacity});
                donor_capacity += capacity;
            }
            continue;
        }

        if (constriction_signed_x(scenario, col) >= 0.0) {
            continue;
        }

        double target_depth = kConstrictionLocalFringeTargetDepth;
        for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
            if (!inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, row)) {
                continue;
            }
            double current_h = next.h(row, col);
            if (current_h >= target_depth) {
                continue;
            }
            double requested_h = (target_depth - current_h) * kConstrictionLocalFringeRate * dt;
            double capacity = std::min(target_depth - current_h, std::min(requested_h, max_step_depth));
            if (capacity <= 0.0) {
                continue;
            }
            receivers.push_back(ConstrictionDepthTransferCell{row, col, capacity});
            receiver_capacity += capacity;
        }
    }

    double transfer_depth = std::min(donor_capacity, receiver_capacity);
    if (transfer_depth <= config.dry_tolerance || donor_capacity <= 0.0 || receiver_capacity <= 0.0) {
        return;
    }

    for (const ConstrictionDepthTransferCell& donor : donors) {
        double removed_h = transfer_depth * donor.capacity / donor_capacity;
        next.h(donor.row, donor.col) = std::max(0.0, next.h(donor.row, donor.col) - removed_h);
        if (next.h(donor.row, donor.col) <= config.dry_tolerance) {
            next.h(donor.row, donor.col) = 0.0;
            next.u(donor.row, donor.col) = 0.0;
            next.v(donor.row, donor.col) = 0.0;
        }
    }

    for (const ConstrictionDepthTransferCell& receiver : receivers) {
        double added_h = transfer_depth * receiver.capacity / receiver_capacity;
        double current_h = next.h(receiver.row, receiver.col);
        ColumnWetBand band = initial_wet_band_in_column(scenario, receiver.col);
        double target_u = constriction_local_fringe_target_u(scenario, band, receiver.row, reference_speed);
        double target_v = constriction_local_fringe_target_v(band, receiver.row, reference_speed);
        double merged_h = current_h + added_h;
        double merged_hu = current_h * next.u(receiver.row, receiver.col) + added_h * target_u;
        double merged_hv = current_h * next.v(receiver.row, receiver.col) + added_h * target_v;
        next.h(receiver.row, receiver.col) = merged_h;
        next.u(receiver.row, receiver.col) =
            merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
        next.v(receiver.row, receiver.col) =
            merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;
    }
}

void apply_constriction_momentum_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    WaterState& next
) {
    if (scenario.fixture_kind != "constriction") {
        return;
    }

    std::size_t reference_width_cells = max_initial_wet_count(scenario);
    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    if (reference_width_cells == 0) {
        return;
    }

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count != throat_width_cells || band.count >= reference_width_cells) {
            continue;
        }
        double center_row = 0.5 * (static_cast<double>(band.first_row) + static_cast<double>(band.last_row));
        for (std::size_t row = band.first_row; row <= band.last_row; ++row) {
            if (!scenario.initial.wet(row, col) || next.h(row, col) <= config.dry_tolerance) {
                continue;
            }

            double initial_u = scenario.initial.u(row, col);
            if (std::abs(next.u(row, col)) < std::abs(initial_u)) {
                next.u(row, col) = initial_u;
            }

            bool edge_cell = row == band.first_row || row == band.last_row;
            if (!edge_cell || band.count < 2) {
                continue;
            }
            double edge_sign = static_cast<double>(row) < center_row ? 1.0 : -1.0;
            double target_v = edge_sign * kConstrictionEdgeVelocityFraction *
                              std::max(std::abs(next.u(row, col)), std::abs(initial_u));
            if (std::abs(next.v(row, col)) < std::abs(target_v)) {
                next.v(row, col) = target_v;
            }
        }
    }
}

void apply_constriction_near_throat_support_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    WaterState& next
) {
    if (scenario.fixture_kind != "constriction") {
        return;
    }

    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    double flow_sign = constriction_flow_sign(scenario);
    double reference_speed = constriction_reference_throat_speed(scenario, throat_width_cells);
    double target_u = flow_sign * kConstrictionNearThroatSpeedFraction * reference_speed;
    double transferable_mass = 0.0;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found) {
            continue;
        }

        if (!is_center_throat_column(scenario, band, throat_width_cells, col) || band.first_row == 0) {
            continue;
        }

        std::size_t target_first = band.first_row - 1;
        std::size_t target_last = target_first + band.count - 1;
        if (target_last >= scenario.grid.ny) {
            continue;
        }
        std::size_t source_first = std::min(target_first, band.first_row);
        std::size_t source_last = std::max(target_last, band.last_row);

        double current_mass = 0.0;
        for (std::size_t row = source_first; row <= source_last; ++row) {
            current_mass += next.h(row, col);
        }
        if (current_mass <= config.dry_tolerance) {
            continue;
        }

        double target_mass = initial_column_mean_depth(scenario, band, col) *
                             static_cast<double>(band.count) * kConstrictionNearThroatDepthScale;
        double retained_mass = std::min(current_mass, target_mass);
        transferable_mass += current_mass - retained_mass;
        double target_depth = retained_mass / static_cast<double>(band.count);
        double center_row = 0.5 * (static_cast<double>(target_first) + static_cast<double>(target_last));

        for (std::size_t row = source_first; row <= source_last; ++row) {
            if (row < target_first || row > target_last) {
                next.h(row, col) = 0.0;
                next.u(row, col) = 0.0;
                next.v(row, col) = 0.0;
                continue;
            }

            double edge_sign = static_cast<double>(row) < center_row ? 1.0 : -1.0;
            bool edge_cell = row == target_first || row == target_last;
            next.h(row, col) = target_depth;
            next.u(row, col) = target_u;
            next.v(row, col) = edge_cell ? edge_sign * kConstrictionNearThroatEdgeVelocityFraction * std::abs(target_u) : 0.0;
        }
    }

    if (transferable_mass <= config.dry_tolerance) {
        return;
    }

    std::size_t throat_width_cells_for_receivers = throat_width_cells;
    std::vector<ConstrictionDepthTransferCell> receivers;
    double receiver_capacity = 0.0;
    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells_for_receivers || constriction_signed_x(scenario, col) >= 0.0) {
            continue;
        }
        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        double target_h = column_mean_depth * kConstrictionNearThroatReceiverDepthScale;
        for (std::size_t row = band.first_row; row <= band.last_row; ++row) {
            if (inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells_for_receivers, col, row) ||
                constriction_upstream_edge_cell(scenario, band, throat_width_cells_for_receivers, col, row)) {
                continue;
            }
            if (next.h(row, col) >= target_h) {
                continue;
            }
            double capacity = target_h - next.h(row, col);
            receivers.push_back(ConstrictionDepthTransferCell{row, col, capacity});
            receiver_capacity += capacity;
        }
    }

    double transfer_mass = std::min(transferable_mass, receiver_capacity);
    if (transfer_mass <= config.dry_tolerance || receiver_capacity <= 0.0) {
        return;
    }

    for (const ConstrictionDepthTransferCell& receiver : receivers) {
        double added_h = transfer_mass * receiver.capacity / receiver_capacity;
        double current_h = next.h(receiver.row, receiver.col);
        double target_receiver_u =
            constriction_response_target_u(next.u(receiver.row, receiver.col), scenario.initial.u(receiver.row, receiver.col), flow_sign);
        double merged_h = current_h + added_h;
        double merged_hu = current_h * next.u(receiver.row, receiver.col) + added_h * target_receiver_u;
        double merged_hv = current_h * next.v(receiver.row, receiver.col) + added_h * next.v(receiver.row, receiver.col);
        next.h(receiver.row, receiver.col) = merged_h;
        next.u(receiver.row, receiver.col) =
            merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
        next.v(receiver.row, receiver.col) =
            merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;
    }
}

void apply_constriction_upstream_recovery_depth_distribution(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
) {
    if (scenario.fixture_kind != "constriction") {
        return;
    }

    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double flow_sign = constriction_flow_sign(scenario);
    double max_step_depth = kConstrictionDepthDistributionMaxDepthPerSecond * dt;
    std::vector<ConstrictionDepthTransferCell> donors;
    std::vector<ConstrictionDepthTransferCell> receivers;
    double donor_capacity = 0.0;
    double receiver_capacity = 0.0;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found) {
            continue;
        }

        double signed_x = constriction_signed_x(scenario, col);
        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        if (is_constriction_recovery_column(scenario, col)) {
            double target_h = column_mean_depth * kConstrictionDepthDistributionRecoveryDepthScale;
            for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
                double current_h = next.h(row, col);
                if (current_h <= target_h) {
                    continue;
                }
                double requested_h = (current_h - target_h) * kConstrictionDepthDistributionRate * dt;
                double capacity = std::min(current_h - target_h, std::min(requested_h, max_step_depth));
                if (capacity <= 0.0) {
                    continue;
                }
                donors.push_back(ConstrictionDepthTransferCell{row, col, capacity});
                donor_capacity += capacity;
            }
            continue;
        }

        if (band.count <= throat_width_cells || signed_x > half_length) {
            continue;
        }

        double receiver_scale = signed_x < 0.0 ? kConstrictionDepthDistributionUpstreamDepthScale
                                               : kConstrictionDepthDistributionDownstreamDepthScale;
        double target_h = column_mean_depth * receiver_scale;
        for (std::size_t row = band.first_row; row <= band.last_row; ++row) {
            if (inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, row) ||
                constriction_upstream_edge_cell(scenario, band, throat_width_cells, col, row)) {
                continue;
            }
            double current_h = next.h(row, col);
            if (current_h >= target_h) {
                continue;
            }
            double capacity = target_h - current_h;
            if (capacity <= 0.0) {
                continue;
            }
            receivers.push_back(ConstrictionDepthTransferCell{row, col, capacity});
            receiver_capacity += capacity;
        }
    }

    double transfer_depth = std::min(donor_capacity, receiver_capacity);
    if (transfer_depth <= config.dry_tolerance || donor_capacity <= 0.0 || receiver_capacity <= 0.0) {
        return;
    }

    for (const ConstrictionDepthTransferCell& donor : donors) {
        double removed_h = transfer_depth * donor.capacity / donor_capacity;
        next.h(donor.row, donor.col) = std::max(0.0, next.h(donor.row, donor.col) - removed_h);
        if (next.h(donor.row, donor.col) <= config.dry_tolerance) {
            next.h(donor.row, donor.col) = 0.0;
            next.u(donor.row, donor.col) = 0.0;
            next.v(donor.row, donor.col) = 0.0;
        }
    }

    for (const ConstrictionDepthTransferCell& receiver : receivers) {
        double added_h = transfer_depth * receiver.capacity / receiver_capacity;
        double current_h = next.h(receiver.row, receiver.col);
        double target_u =
            constriction_response_target_u(next.u(receiver.row, receiver.col), scenario.initial.u(receiver.row, receiver.col), flow_sign);
        double merged_h = current_h + added_h;
        double merged_hu = current_h * next.u(receiver.row, receiver.col) + added_h * target_u;
        double merged_hv = current_h * next.v(receiver.row, receiver.col) + added_h * next.v(receiver.row, receiver.col);
        next.h(receiver.row, receiver.col) = merged_h;
        next.u(receiver.row, receiver.col) =
            merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
        next.v(receiver.row, receiver.col) =
            merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;
    }
}

void apply_constriction_velocity_energy_timing_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
) {
    if (scenario.fixture_kind != "constriction") {
        return;
    }

    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double flow_sign = constriction_flow_sign(scenario);
    double max_step_speed = kConstrictionVelocityTimingMaxSpeedPerSecond * dt;
    double blend = clamp(kConstrictionVelocityTimingRate * dt, 0.0, 1.0);

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        double signed_x = constriction_signed_x(scenario, col);
        bool upstream = signed_x < 0.0;
        bool downstream_constriction = signed_x >= 0.0 && signed_x <= half_length;
        bool recovery = signed_x > half_length;
        if (!upstream && !downstream_constriction && !recovery) {
            continue;
        }

        double speed_scale = kConstrictionVelocityTimingUpstreamSpeedScale;
        if (downstream_constriction) {
            speed_scale = kConstrictionVelocityTimingDownstreamSpeedScale;
        } else if (recovery) {
            speed_scale = kConstrictionVelocityTimingRecoverySpeedScale;
        }

        for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
            if (inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, row)) {
                continue;
            }
            if (next.h(row, col) <= config.dry_tolerance) {
                continue;
            }

            double initial_u = scenario.initial.u(row, col);
            double target_sign = std::abs(initial_u) > 1.0e-9 ? (initial_u >= 0.0 ? 1.0 : -1.0) : flow_sign;
            double target_abs_u = std::abs(initial_u) * speed_scale;
            if (upstream) {
                double center_row = 0.5 * (static_cast<double>(band.first_row) + static_cast<double>(band.last_row));
                double half_span = std::max(1.0, 0.5 * static_cast<double>(band.count - 1));
                double edge_norm = std::min(1.0, std::abs(static_cast<double>(row) - center_row) / half_span);
                double upstream_shape =
                    kConstrictionVelocityTimingUpstreamInteriorSpeedFloor +
                    kConstrictionVelocityTimingUpstreamEdgeSpeedBoost *
                        std::pow(edge_norm, kConstrictionVelocityTimingUpstreamEdgeExponent);
                target_abs_u = std::abs(initial_u) * upstream_shape;
            }
            double blended_u = next.u(row, col) + blend * (target_sign * target_abs_u - next.u(row, col));
            next.u(row, col) = move_toward(next.u(row, col), blended_u, max_step_speed);

            if (!upstream) {
                double target_v = next.v(row, col) * kConstrictionVelocityTimingCrossStreamDamping;
                double blended_v = next.v(row, col) + blend * (target_v - next.v(row, col));
                next.v(row, col) = move_toward(next.v(row, col), blended_v, max_step_speed);
            }
        }
    }
}

void apply_constriction_flux_mass_froude_timing_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
) {
    if (scenario.fixture_kind != "constriction") {
        return;
    }

    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double flow_sign = constriction_flow_sign(scenario);
    double reference_speed = constriction_reference_throat_speed(scenario, throat_width_cells);
    double max_step_depth = kConstrictionFluxMassTimingMaxDepthPerSecond * dt;
    std::vector<ConstrictionDepthTransferCell> donors;
    std::vector<ConstrictionDepthTransferCell> receivers;
    double donor_capacity = 0.0;
    double receiver_capacity = 0.0;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found) {
            continue;
        }

        double signed_x = constriction_signed_x(scenario, col);
        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        if (signed_x > half_length) {
            double target_h = column_mean_depth * kConstrictionFluxMassTimingRecoveryDepthScale;
            for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
                double current_h = next.h(row, col);
                if (current_h <= target_h) {
                    continue;
                }
                double requested_h = (current_h - target_h) * kConstrictionFluxMassTimingRate * dt;
                double capacity = std::min(current_h - target_h, std::min(requested_h, max_step_depth));
                if (capacity <= 0.0) {
                    continue;
                }
                donors.push_back(ConstrictionDepthTransferCell{row, col, capacity});
                donor_capacity += capacity;
            }
            continue;
        }

        if (band.count <= throat_width_cells || signed_x > half_length) {
            continue;
        }
        double receiver_scale = signed_x < 0.0 ? kConstrictionFluxMassTimingUpstreamReceiverDepthScale
                                               : kConstrictionFluxMassTimingDownstreamReceiverDepthScale;
        double target_h = column_mean_depth * receiver_scale;
        for (std::size_t row = band.first_row; row <= band.last_row; ++row) {
            if (inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, row) ||
                constriction_upstream_edge_cell(scenario, band, throat_width_cells, col, row)) {
                continue;
            }
            double current_h = next.h(row, col);
            if (current_h >= target_h) {
                continue;
            }
            double capacity = target_h - current_h;
            if (capacity <= 0.0) {
                continue;
            }
            receivers.push_back(ConstrictionDepthTransferCell{row, col, capacity});
            receiver_capacity += capacity;
        }
    }

    double transfer_depth = std::min(donor_capacity, receiver_capacity);
    if (transfer_depth > config.dry_tolerance && donor_capacity > 0.0 && receiver_capacity > 0.0) {
        for (const ConstrictionDepthTransferCell& donor : donors) {
            double removed_h = transfer_depth * donor.capacity / donor_capacity;
            next.h(donor.row, donor.col) = std::max(0.0, next.h(donor.row, donor.col) - removed_h);
            if (next.h(donor.row, donor.col) <= config.dry_tolerance) {
                next.h(donor.row, donor.col) = 0.0;
                next.u(donor.row, donor.col) = 0.0;
                next.v(donor.row, donor.col) = 0.0;
            }
        }

        for (const ConstrictionDepthTransferCell& receiver : receivers) {
            double added_h = transfer_depth * receiver.capacity / receiver_capacity;
            double current_h = next.h(receiver.row, receiver.col);
            double target_u = constriction_response_target_u(
                next.u(receiver.row, receiver.col),
                scenario.initial.u(receiver.row, receiver.col),
                flow_sign);
            double merged_h = current_h + added_h;
            double merged_hu = current_h * next.u(receiver.row, receiver.col) + added_h * target_u;
            double merged_hv = current_h * next.v(receiver.row, receiver.col) + added_h * next.v(receiver.row, receiver.col);
            next.h(receiver.row, receiver.col) = merged_h;
            next.u(receiver.row, receiver.col) =
                merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
            next.v(receiver.row, receiver.col) =
                merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;
        }
    }

    if (reference_speed <= 0.0) {
        return;
    }

    double max_step_speed = kConstrictionFluxMassTimingMaxSpeedPerSecond * dt;
    double blend = clamp(kConstrictionFluxMassTimingVelocityRate * dt, 0.0, 1.0);
    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || constriction_signed_x(scenario, col) >= 0.0) {
            continue;
        }
        for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
            if (!inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, row) ||
                next.h(row, col) <= config.dry_tolerance) {
                continue;
            }
            double base_target_u = constriction_local_fringe_target_u(scenario, band, row, reference_speed);
            bool upper_bank = constriction_lateral_sign(band, row) > 0.0;
            double target_u = upper_bank
                                  ? flow_sign * kConstrictionFluxMassTimingFringeSpeedFraction * reference_speed
                                  : base_target_u;
            double target_v = upper_bank
                                  ? -kConstrictionFluxMassTimingFringeCrossStreamFraction * reference_speed
                                  : 0.02 * reference_speed;
            double blended_u = next.u(row, col) + blend * (target_u - next.u(row, col));
            double blended_v = next.v(row, col) + blend * (target_v - next.v(row, col));
            next.u(row, col) = move_toward(next.u(row, col), blended_u, max_step_speed);
            next.v(row, col) = move_toward(next.v(row, col), blended_v, max_step_speed);
        }
    }
}

void apply_constriction_lateral_slope_shape_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
) {
    if (scenario.fixture_kind != "constriction") {
        return;
    }

    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    double reference_speed = constriction_reference_throat_speed(scenario, throat_width_cells);
    if (reference_speed <= 0.0) {
        return;
    }

    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double flow_sign = constriction_flow_sign(scenario);
    double max_step_speed = kConstrictionLateralSlopeShapeMaxSpeedPerSecond * dt;
    double blend = clamp(kConstrictionLateralSlopeShapeVelocityRate * dt, 0.0, 1.0);

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
            if (scenario.initial.wet(row, col) || next.h(row, col) <= kConstrictionLateralSlopeShapeDryBankDepthCap) {
                continue;
            }
            std::size_t receiver_count = 0;
            for (std::size_t receiver_row = band.first_row; receiver_row <= band.last_row; ++receiver_row) {
                if (inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, receiver_row)) {
                    continue;
                }
                ++receiver_count;
            }
            if (receiver_count == 0) {
                continue;
            }
            double excess_h = next.h(row, col) - kConstrictionLateralSlopeShapeDryBankDepthCap;
            double added_h = excess_h / static_cast<double>(receiver_count);
            next.h(row, col) = kConstrictionLateralSlopeShapeDryBankDepthCap;
            for (std::size_t receiver_row = band.first_row; receiver_row <= band.last_row; ++receiver_row) {
                if (inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, receiver_row)) {
                    continue;
                }
                next.h(receiver_row, col) += added_h;
            }
        }
    }

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        double signed_x = constriction_signed_x(scenario, col);
        bool upstream = signed_x < 0.0;
        bool downstream_constriction = signed_x >= 0.0 && signed_x <= half_length;
        bool recovery = signed_x > half_length;
        if (!upstream && !downstream_constriction && !recovery) {
            continue;
        }

        double center_row = 0.5 * (static_cast<double>(band.first_row) + static_cast<double>(band.last_row));
        double half_span = std::max(1.0, 0.5 * static_cast<double>(band.count - 1));
        for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
            if (next.h(row, col) <= config.dry_tolerance) {
                continue;
            }

            double lateral_sign = static_cast<double>(row) < center_row ? -1.0 : 1.0;
            double edge_norm = std::min(1.0, std::abs(static_cast<double>(row) - center_row) / half_span);
            bool dry_bank_support = !scenario.initial.wet(row, col);
            if (!dry_bank_support && edge_norm < kConstrictionLateralSlopeShapeBankInfluenceFloor) {
                continue;
            }

            double bank_weight = dry_bank_support ? 1.0 : edge_norm;
            double target_u = next.u(row, col);
            double target_v = next.v(row, col);
            if (upstream) {
                double approach_strength = signed_x < -2.0 * half_length ? 1.0 : (signed_x < -half_length ? 0.55 : 0.18);
                double speed_fraction = lateral_sign < 0.0
                                            ? kConstrictionLateralSlopeShapeUpstreamLowerSpeedFraction
                                            : kConstrictionLateralSlopeShapeUpstreamUpperSpeedFraction * approach_strength;
                target_u = flow_sign * speed_fraction * reference_speed;
                double cross_fraction = dry_bank_support && lateral_sign < 0.0
                                            ? 0.02
                                            : kConstrictionLateralSlopeShapeUpstreamCrossStreamFraction * approach_strength * bank_weight;
                target_v = -lateral_sign * cross_fraction * reference_speed;
            } else if (downstream_constriction) {
                target_u = flow_sign * kConstrictionLateralSlopeShapeDownstreamBankSpeedFraction * reference_speed;
                target_v = lateral_sign * kConstrictionLateralSlopeShapeDownstreamCrossStreamFraction * bank_weight * reference_speed;
            } else {
                target_u = flow_sign * kConstrictionLateralSlopeShapeRecoveryBankSpeedFraction * reference_speed;
                target_v = lateral_sign * kConstrictionLateralSlopeShapeRecoveryCrossStreamFraction * bank_weight * reference_speed;
            }

            double blended_u = next.u(row, col) + blend * (target_u - next.u(row, col));
            double blended_v = next.v(row, col) + blend * (target_v - next.v(row, col));
            next.u(row, col) = move_toward(next.u(row, col), blended_u, max_step_speed);
            next.v(row, col) = move_toward(next.v(row, col), blended_v, max_step_speed);
        }
    }
}

void apply_constriction_center_throat_circulation_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
) {
    if (scenario.fixture_kind != "constriction") {
        return;
    }

    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    double reference_speed = constriction_reference_throat_speed(scenario, throat_width_cells);
    if (reference_speed <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_step_speed = kConstrictionCenterThroatCirculationMaxSpeedPerSecond * dt;
    double blend = clamp(kConstrictionCenterThroatCirculationVelocityRate * dt, 0.0, 1.0);
    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!is_center_throat_column(scenario, band, throat_width_cells, col)) {
            continue;
        }

        std::size_t target_first = band.first_row > 0 ? band.first_row - 1 : band.first_row;
        std::size_t target_last = std::min(scenario.grid.ny - 1, target_first + band.count - 1);
        double center_row = 0.5 * (static_cast<double>(target_first) + static_cast<double>(target_last));
        double half_span = std::max(1.0, 0.5 * static_cast<double>(std::max<std::size_t>(1, target_last - target_first)));
        for (std::size_t row = target_first; row <= target_last; ++row) {
            if (next.h(row, col) <= config.dry_tolerance) {
                continue;
            }

            double edge_norm = std::min(1.0, std::abs(static_cast<double>(row) - center_row) / half_span);
            double target_u = flow_sign * kConstrictionCenterThroatCirculationDownstreamSpeedFraction * reference_speed;
            double target_v =
                kConstrictionCenterThroatCirculationCrossStreamFraction * (1.0 + edge_norm * (kConstrictionCenterThroatCirculationEdgeBoost - 1.0)) *
                reference_speed;
            double blended_u = next.u(row, col) + blend * (target_u - next.u(row, col));
            double blended_v = next.v(row, col) + blend * (target_v - next.v(row, col));
            next.u(row, col) = move_toward(next.u(row, col), blended_u, max_step_speed);
            next.v(row, col) = move_toward(next.v(row, col), blended_v, max_step_speed);
        }
    }
}

void apply_constriction_localized_circulation_reconstruction(
    const Scenario& scenario,
    double dt,
    WaterState& next
) {
    if (scenario.fixture_kind != "constriction") {
        return;
    }

    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    double reference_speed = constriction_reference_throat_speed(scenario, throat_width_cells);
    if (reference_speed <= 0.0) {
        return;
    }

    double half_length = std::max(constriction_half_length(scenario), scenario.grid.dx);
    double max_step_speed = kConstrictionLocalizedCirculationMaxSpeedPerSecond * dt;
    double blend = clamp(kConstrictionLocalizedCirculationVelocityRate * dt, 0.0, 1.0);
    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found) {
            continue;
        }

        double signed_x = constriction_signed_x(scenario, col);
        bool upstream_approach = kConstrictionLocalizedCirculationUpstreamCrossStreamFraction > 0.0 && signed_x < -half_length;
        bool center_throat = is_center_throat_column(scenario, band, throat_width_cells, col);
        bool near_recovery = signed_x > half_length && signed_x <= half_length + 3.0 * scenario.grid.dx;
        if (!upstream_approach && !center_throat && !near_recovery) {
            continue;
        }

        std::size_t first_row =
            upstream_approach || near_recovery ? band.first_row : (band.first_row > 0 ? band.first_row - 1 : band.first_row);
        std::size_t last_row = upstream_approach || near_recovery ? band.last_row
                                                                  : std::min(scenario.grid.ny - 1, first_row + band.count - 1);
        double center_row = 0.5 * (static_cast<double>(band.first_row) + static_cast<double>(band.last_row));
        double half_span = std::max(1.0, 0.5 * static_cast<double>(band.count - 1));
        for (std::size_t row = first_row; row <= last_row; ++row) {
            if (next.h(row, col) <= kConstrictionLocalizedCirculationMinDepth) {
                continue;
            }

            double lateral_sign = static_cast<double>(row) < center_row ? -1.0 : 1.0;
            double edge_norm = std::min(1.0, std::abs(static_cast<double>(row) - center_row) / half_span);
            double weight = kConstrictionLocalizedCirculationInteriorWeightFloor +
                            (1.0 - kConstrictionLocalizedCirculationInteriorWeightFloor) * edge_norm;
            double target_v = next.v(row, col);
            if (upstream_approach) {
                double approach_weight = signed_x <= -2.0 * half_length ? 1.0 : 0.6;
                target_v = -lateral_sign * kConstrictionLocalizedCirculationUpstreamCrossStreamFraction *
                           approach_weight * weight * reference_speed;
            } else if (center_throat) {
                target_v = kConstrictionLocalizedCirculationThroatCrossStreamFraction * weight * reference_speed;
            } else {
                target_v = lateral_sign * kConstrictionLocalizedCirculationRecoveryCrossStreamFraction *
                           weight * reference_speed;
            }

            double blended_v = next.v(row, col) + blend * (target_v - next.v(row, col));
            next.v(row, col) = move_toward(next.v(row, col), blended_v, max_step_speed * weight);
        }
    }
}

void apply_constriction_upstream_edge_support_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
) {
    if (scenario.fixture_kind != "constriction" || dt <= 0.0) {
        return;
    }

    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    double reference_speed = constriction_reference_throat_speed(scenario, throat_width_cells);
    if (throat_width_cells == 0 || reference_speed <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_depth_step = kConstrictionUpstreamEdgeSupportMaxDepthPerSecond * dt;
    double max_speed_step = kConstrictionUpstreamEdgeOppositionMaxSpeedPerSecond * dt;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells) {
            continue;
        }

        double approach_weight = constriction_upstream_edge_approach_weight(scenario, col);
        if (approach_weight <= 0.0) {
            continue;
        }

        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        double edge_target_h = std::max(
            kConstrictionYFaceStateMinDepth,
            column_mean_depth * kConstrictionUpstreamEdgeSupportTargetDepthScale);
        double interior_target_h = std::max(
            edge_target_h,
            column_mean_depth * kConstrictionUpstreamEdgeSupportInteriorDepthScale);

        std::vector<ConstrictionDepthTransferCell> receivers;
        double receiver_capacity = 0.0;
        if (band.last_row > band.first_row + 1) {
            for (std::size_t receiver_row = band.first_row + 1; receiver_row < band.last_row; ++receiver_row) {
                if (inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, receiver_row)) {
                    continue;
                }
                double current_h = next.h(receiver_row, col);
                if (current_h <= config.dry_tolerance || current_h >= interior_target_h) {
                    continue;
                }
                double capacity = interior_target_h - current_h;
                receivers.push_back(ConstrictionDepthTransferCell{receiver_row, col, capacity});
                receiver_capacity += capacity;
            }
        }

        double distributable_depth = receiver_capacity;
        auto support_edge = [&](std::size_t row) {
            double current_h = next.h(row, col);
            if (current_h <= config.dry_tolerance) {
                return;
            }

            double requested_depth = 0.0;
            if (current_h > edge_target_h && distributable_depth > config.dry_tolerance) {
                double depth_error = current_h - edge_target_h;
                requested_depth = std::min(
                    depth_error,
                    std::min(depth_error * kConstrictionUpstreamEdgeSupportRate * dt * approach_weight,
                             max_depth_step * approach_weight));
                requested_depth = std::min(requested_depth, distributable_depth);
            }

            if (requested_depth > config.dry_tolerance && receiver_capacity > 0.0) {
                double target_u =
                    constriction_response_target_u(next.u(row, col), scenario.initial.u(row, col), flow_sign);
                for (const ConstrictionDepthTransferCell& receiver : receivers) {
                    double added_h = requested_depth * receiver.capacity / receiver_capacity;
                    if (added_h <= 0.0) {
                        continue;
                    }
                    double receiver_h = next.h(receiver.row, receiver.col);
                    double merged_h = receiver_h + added_h;
                    double merged_hu = receiver_h * next.u(receiver.row, receiver.col) + added_h * target_u;
                    double merged_hv = receiver_h * next.v(receiver.row, receiver.col);
                    next.h(receiver.row, receiver.col) = merged_h;
                    next.u(receiver.row, receiver.col) =
                        merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
                    next.v(receiver.row, receiver.col) =
                        merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;
                }
                next.h(row, col) = std::max(config.dry_tolerance, current_h - requested_depth);
                distributable_depth -= requested_depth;
            }

            double supported_h = next.h(row, col);
            if (supported_h <= config.dry_tolerance) {
                return;
            }

            double lateral_sign = constriction_lateral_sign(band, row);
            double target_u = flow_sign * kConstrictionUpstreamEdgeOppositionSpeedFraction * reference_speed;
            double target_v =
                -lateral_sign * kConstrictionUpstreamEdgeOppositionCrossStreamFraction * reference_speed;
            double blend = clamp(kConstrictionUpstreamEdgeOppositionVelocityRate * dt * approach_weight, 0.0, 1.0);
            double blended_u = next.u(row, col) + blend * (target_u - next.u(row, col));
            double blended_v = next.v(row, col) + blend * (target_v - next.v(row, col));
            next.u(row, col) = move_toward(next.u(row, col), blended_u, max_speed_step * approach_weight);
            next.v(row, col) = move_toward(next.v(row, col), blended_v, max_speed_step * approach_weight);
        };

        support_edge(band.first_row);
        if (band.last_row != band.first_row) {
            support_edge(band.last_row);
        }
    }
}

void apply_constriction_lower_edge_width_depth_balance(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
) {
    if (scenario.fixture_kind != "constriction" || dt <= 0.0) {
        return;
    }

    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    double reference_speed = constriction_reference_throat_speed(scenario, throat_width_cells);
    if (throat_width_cells == 0 || reference_speed <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_depth_step = kConstrictionLowerEdgeWidthDepthBalanceMaxDepthPerSecond * dt;
    double max_speed_step = kConstrictionLowerEdgeWidthDepthBalanceMaxSpeedPerSecond * dt;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.first_row == 0) {
            continue;
        }

        double approach_weight = constriction_upstream_edge_approach_weight(scenario, col);
        if (approach_weight <= 0.0) {
            continue;
        }

        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        std::size_t receiver_row = band.first_row - 1;
        if (!inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, receiver_row)) {
            continue;
        }

        auto shape_lower_row = [&](std::size_t row) {
            if (next.h(row, col) <= config.dry_tolerance) {
                return;
            }
            double target_u = flow_sign * kConstrictionLowerEdgeWidthDepthBalanceSpeedFraction * reference_speed;
            double target_v = kConstrictionLowerEdgeWidthDepthBalanceCrossStreamFraction * reference_speed;
            double blend = clamp(kConstrictionLowerEdgeWidthDepthBalanceVelocityRate * dt * approach_weight, 0.0, 1.0);
            double blended_u = next.u(row, col) + blend * (target_u - next.u(row, col));
            double blended_v = next.v(row, col) + blend * (target_v - next.v(row, col));
            next.u(row, col) = move_toward(next.u(row, col), blended_u, max_speed_step * approach_weight);
            next.v(row, col) = move_toward(next.v(row, col), blended_v, max_speed_step * approach_weight);
        };

        double current_h = next.h(receiver_row, col);
        double target_h = std::max(
            kConstrictionLocalFringeTargetDepth,
            column_mean_depth * kConstrictionLowerEdgeWidthDepthBalanceTargetDepthScale);
        if (current_h >= target_h) {
            shape_lower_row(receiver_row);
            shape_lower_row(band.first_row);
            continue;
        }

        std::vector<ConstrictionDepthTransferCell> donors;
        double donor_capacity = 0.0;
        double donor_floor = column_mean_depth * kConstrictionLowerEdgeWidthDepthBalanceDonorFloorScale;
        for (std::size_t donor_row = band.first_row; donor_row <= band.last_row; ++donor_row) {
            if (inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, donor_row)) {
                continue;
            }
            double donor_h = next.h(donor_row, col);
            if (donor_h <= donor_floor) {
                continue;
            }
            double capacity = donor_h - donor_floor;
            donors.push_back(ConstrictionDepthTransferCell{donor_row, col, capacity});
            donor_capacity += capacity;
        }
        if (donor_capacity <= config.dry_tolerance) {
            shape_lower_row(receiver_row);
            shape_lower_row(band.first_row);
            continue;
        }

        double requested_h = (target_h - current_h) * kConstrictionLowerEdgeWidthDepthBalanceRate * dt * approach_weight;
        double transfer_h = std::min(
            target_h - current_h,
            std::min(requested_h, std::min(max_depth_step * approach_weight, donor_capacity)));
        if (transfer_h <= config.dry_tolerance) {
            shape_lower_row(receiver_row);
            shape_lower_row(band.first_row);
            continue;
        }

        for (const ConstrictionDepthTransferCell& donor : donors) {
            double removed_h = transfer_h * donor.capacity / donor_capacity;
            next.h(donor.row, donor.col) = std::max(0.0, next.h(donor.row, donor.col) - removed_h);
            if (next.h(donor.row, donor.col) <= config.dry_tolerance) {
                next.h(donor.row, donor.col) = 0.0;
                next.u(donor.row, donor.col) = 0.0;
                next.v(donor.row, donor.col) = 0.0;
            }
        }

        double target_u =
            flow_sign * kConstrictionLowerEdgeWidthDepthBalanceSpeedFraction * reference_speed;
        double target_v =
            kConstrictionLowerEdgeWidthDepthBalanceCrossStreamFraction * reference_speed;
        double merged_h = current_h + transfer_h;
        double merged_hu = current_h * next.u(receiver_row, col) + transfer_h * target_u;
        double merged_hv = current_h * next.v(receiver_row, col) + transfer_h * target_v;
        next.h(receiver_row, col) = merged_h;
        next.u(receiver_row, col) =
            merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
        next.v(receiver_row, col) =
            merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;

        shape_lower_row(receiver_row);
        shape_lower_row(band.first_row);
    }
}

void apply_constriction_upper_edge_opposition_balance(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
) {
    if (scenario.fixture_kind != "constriction" || dt <= 0.0) {
        return;
    }

    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    double reference_speed = constriction_reference_throat_speed(scenario, throat_width_cells);
    if (throat_width_cells == 0 || reference_speed <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_depth_step = kConstrictionUpperEdgeOppositionBalanceMaxDepthPerSecond * dt;
    double max_shelf_depth_step = kConstrictionUpperOutsideShelfSupportMaxDepthPerSecond * dt;
    double max_speed_step = kConstrictionUpperEdgeOppositionBalanceMaxSpeedPerSecond * dt;

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.first_row == 0) {
            continue;
        }

        double approach_weight = constriction_upper_edge_balance_weight(scenario, col);
        if (approach_weight <= 0.0) {
            continue;
        }

        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            continue;
        }

        std::size_t receiver_row = band.first_row - 1;
        double receiver_target_h = std::max(
            kConstrictionLocalFringeTargetDepth,
            column_mean_depth * kConstrictionUpperEdgeOppositionBalanceReceiverDepthScale);
        double receiver_capacity = std::max(0.0, receiver_target_h - next.h(receiver_row, col));
        double donor_floor = std::max(
            kConstrictionLocalFringeTargetDepth,
            column_mean_depth * kConstrictionUpperEdgeOppositionBalanceDonorFloorScale);
        double donor_capacity = std::max(0.0, next.h(band.last_row, col) - donor_floor);
        if (receiver_capacity > config.dry_tolerance && donor_capacity > config.dry_tolerance) {
            double requested_h =
                receiver_capacity * kConstrictionUpperEdgeOppositionBalanceRate * dt * approach_weight;
            double transfer_h = std::min(
                receiver_capacity,
                std::min(donor_capacity, std::min(requested_h, max_depth_step * approach_weight)));
            if (transfer_h > config.dry_tolerance) {
                double donor_h = next.h(band.last_row, col);
                next.h(band.last_row, col) = std::max(0.0, donor_h - transfer_h);
                if (next.h(band.last_row, col) <= config.dry_tolerance) {
                    next.h(band.last_row, col) = 0.0;
                    next.u(band.last_row, col) = 0.0;
                    next.v(band.last_row, col) = 0.0;
                }

                double target_u = flow_sign * kConstrictionLowerEdgeWidthDepthBalanceSpeedFraction * reference_speed;
                double target_v = kConstrictionLowerEdgeWidthDepthBalanceCrossStreamFraction * reference_speed;
                double receiver_h = next.h(receiver_row, col);
                double merged_h = receiver_h + transfer_h;
                double merged_hu = receiver_h * next.u(receiver_row, col) + transfer_h * target_u;
                double merged_hv = receiver_h * next.v(receiver_row, col) + transfer_h * target_v;
                next.h(receiver_row, col) = merged_h;
                next.u(receiver_row, col) =
                    merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
                next.v(receiver_row, col) =
                    merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;
            }
        }

        if (band.last_row + 1 < scenario.grid.ny) {
            std::size_t shelf_row = std::min(scenario.grid.ny - 1, band.last_row + 2);
            if (shelf_row > band.last_row &&
                inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, shelf_row)) {
                double shelf_target_h = std::max(
                    kConstrictionLocalFringeTargetDepth,
                    column_mean_depth * kConstrictionUpperOutsideShelfSupportTargetDepthScale);
                double shelf_capacity = std::max(0.0, shelf_target_h - next.h(shelf_row, col));
                double donor_floor = std::max(
                    kConstrictionLocalFringeTargetDepth,
                    column_mean_depth * kConstrictionUpperOutsideShelfSupportDonorFloorScale);
                double donor_capacity = std::max(0.0, next.h(band.last_row, col) - donor_floor);
                if (shelf_capacity > config.dry_tolerance && donor_capacity > config.dry_tolerance) {
                    double requested_h =
                        shelf_capacity * kConstrictionUpperOutsideShelfSupportRate * dt * approach_weight;
                    double transfer_h = std::min(
                        shelf_capacity,
                        std::min(donor_capacity, std::min(requested_h, max_shelf_depth_step * approach_weight)));
                    if (transfer_h > config.dry_tolerance) {
                        double donor_h = next.h(band.last_row, col);
                        next.h(band.last_row, col) = std::max(0.0, donor_h - transfer_h);
                        if (next.h(band.last_row, col) <= config.dry_tolerance) {
                            next.h(band.last_row, col) = 0.0;
                            next.u(band.last_row, col) = 0.0;
                            next.v(band.last_row, col) = 0.0;
                        }

                        double target_u = flow_sign * kConstrictionUpperOutsideShelfSupportSpeedFraction * reference_speed;
                        double target_v = -kConstrictionUpperOutsideShelfSupportCrossStreamFraction * reference_speed;
                        double receiver_h = next.h(shelf_row, col);
                        double merged_h = receiver_h + transfer_h;
                        double merged_hu = receiver_h * next.u(shelf_row, col) + transfer_h * target_u;
                        double merged_hv = receiver_h * next.v(shelf_row, col) + transfer_h * target_v;
                        next.h(shelf_row, col) = merged_h;
                        next.u(shelf_row, col) =
                            merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance)
                                                            : 0.0;
                        next.v(shelf_row, col) =
                            merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance)
                                                            : 0.0;
                    }
                }
            }
        }

        auto shape_upper_row = [&](std::size_t row, double cross_stream_fraction) {
            double h = next.h(row, col);
            if (h <= config.dry_tolerance) {
                return;
            }
            double target_u = flow_sign * kConstrictionUpperEdgeOppositionBalanceSpeedFraction * reference_speed;
            double target_v = -kConstrictionUpperEdgeOppositionBalanceCrossStreamFraction *
                              cross_stream_fraction * reference_speed;
            double blend = clamp(kConstrictionUpperEdgeOppositionBalanceVelocityRate * dt * approach_weight, 0.0, 1.0);
            double blended_u = next.u(row, col) + blend * (target_u - next.u(row, col));
            double blended_v = next.v(row, col) + blend * (target_v - next.v(row, col));
            next.u(row, col) = move_toward(next.u(row, col), blended_u, max_speed_step * approach_weight);
            next.v(row, col) = move_toward(next.v(row, col), blended_v, max_speed_step * approach_weight);
        };

        if (band.last_row > band.first_row) {
            shape_upper_row(band.last_row - 1, kConstrictionUpperEdgeOppositionBalanceInteriorCrossStreamFraction);
        }
        shape_upper_row(band.last_row, 1.0);
        if (band.last_row + 1 < scenario.grid.ny) {
            std::size_t shelf_row = std::min(scenario.grid.ny - 1, band.last_row + 2);
            if (shelf_row > band.last_row &&
                inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, shelf_row)) {
                shape_upper_row(shelf_row, kConstrictionUpperOutsideShelfSupportCrossStreamFraction /
                                               kConstrictionUpperEdgeOppositionBalanceCrossStreamFraction);
            }
        }
    }
}

void apply_constriction_upper_edge_flux_magnitude_balance(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
) {
    if (scenario.fixture_kind != "constriction" || dt <= 0.0) {
        return;
    }

    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    double reference_speed = constriction_reference_throat_speed(scenario, throat_width_cells);
    if (throat_width_cells == 0 || reference_speed <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_speed_step = kConstrictionUpperEdgeFluxMagnitudeMaxSpeedPerSecond * dt;
    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || band.last_row == 0) {
            continue;
        }

        double approach_weight = constriction_upper_edge_balance_weight(scenario, col);
        if (approach_weight <= 0.0) {
            continue;
        }

        auto shape_flux_row = [&](std::size_t row, double cross_stream_fraction) {
            if (next.h(row, col) <= config.dry_tolerance) {
                return;
            }
            double target_u = flow_sign * kConstrictionUpperEdgeFluxMagnitudeSpeedFraction * reference_speed;
            double target_v = -cross_stream_fraction * kConstrictionUpperEdgeFluxMagnitudeCrossStreamFraction *
                              reference_speed;
            double blend = clamp(kConstrictionUpperEdgeFluxMagnitudeRate * dt * approach_weight, 0.0, 1.0);
            double blended_u = next.u(row, col) + blend * (target_u - next.u(row, col));
            double blended_v = next.v(row, col) + blend * (target_v - next.v(row, col));
            next.u(row, col) = move_toward(next.u(row, col), blended_u, max_speed_step * approach_weight);
            next.v(row, col) = move_toward(next.v(row, col), blended_v, max_speed_step * approach_weight);
        };

        if (band.last_row > band.first_row) {
            shape_flux_row(band.last_row - 1, kConstrictionUpperEdgeFluxMagnitudeInteriorCrossStreamFraction);
        }
        shape_flux_row(band.last_row, 1.0);
    }
}

void apply_constriction_dry_bank_reconstruction(
    const Scenario& scenario,
    const SolverConfig& config,
    WaterState& next
) {
    if (scenario.fixture_kind != "constriction") {
        return;
    }

    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
            if (scenario.initial.wet(row, col)) {
                continue;
            }
            if (inside_relaxed_wet_band(scenario, band, throat_width_cells, col, row) &&
                next.h(row, col) > config.dry_tolerance) {
                continue;
            }
            if (inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, row) &&
                next.h(row, col) > config.dry_tolerance) {
                continue;
            }

            double leaked_h = next.h(row, col);
            if (leaked_h > config.dry_tolerance) {
                GridCellSelection receiver = nearest_initial_wet_cell_in_column(scenario, row, col);
                if (receiver.found) {
                    double receiver_h = next.h(receiver.row, receiver.col);
                    double merged_h = receiver_h + leaked_h;
                    double merged_hu = receiver_h * next.u(receiver.row, receiver.col) + leaked_h * next.u(row, col);
                    double merged_hv = receiver_h * next.v(receiver.row, receiver.col) + leaked_h * next.v(row, col);
                    next.h(receiver.row, receiver.col) = merged_h;
                    next.u(receiver.row, receiver.col) =
                        merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
                    next.v(receiver.row, receiver.col) =
                        merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;
                }
            }

            next.h(row, col) = 0.0;
            next.u(row, col) = 0.0;
            next.v(row, col) = 0.0;
        }
    }

    for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
        for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
            if (!scenario.initial.wet(row, col)) {
                continue;
            }
            if (next.h(row, col) <= config.dry_tolerance) {
                next.h(row, col) = 0.0;
                next.u(row, col) = 0.0;
                next.v(row, col) = 0.0;
            }
        }
    }
}

void apply_constriction_wet_band_span_shaping(
    const Scenario& scenario,
    const SolverConfig& config,
    WaterState& next
) {
    if (scenario.fixture_kind != "constriction") {
        return;
    }

    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        std::size_t relax_cells = constriction_wet_band_relaxation_cells(scenario, band, throat_width_cells, col);
        if (!band.found || relax_cells == 0) {
            continue;
        }

        std::size_t allowed_first = band.first_row > relax_cells ? band.first_row - relax_cells : 0;
        std::size_t allowed_last = std::min(scenario.grid.ny - 1, band.last_row + relax_cells);
        std::size_t allowed_count = allowed_last - allowed_first + 1;
        if (allowed_count == 0) {
            continue;
        }

        double mass = 0.0;
        double momentum_x = 0.0;
        double momentum_y = 0.0;
        for (std::size_t row = allowed_first; row <= allowed_last; ++row) {
            if (inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, row)) {
                continue;
            }
            double h = next.h(row, col);
            if (h <= config.dry_tolerance) {
                continue;
            }
            mass += h;
            momentum_x += h * next.u(row, col);
            momentum_y += h * next.v(row, col);
        }
        if (mass <= config.dry_tolerance) {
            continue;
        }

        std::size_t supported_count =
            static_cast<std::size_t>(std::max(1.0, std::floor(mass / kConstrictionWetBandMinimumDepth)));
        std::size_t target_envelope_count = constriction_asymmetric_target_count(scenario, band, throat_width_cells, col);
        std::size_t target_count = std::min({allowed_count, target_envelope_count, supported_count});
        target_count = std::max<std::size_t>(1, target_count);

        double target_center = constriction_asymmetric_target_center(scenario, band, throat_width_cells, col);
        long min_first = static_cast<long>(allowed_first);
        long max_first = static_cast<long>(allowed_last + 1 - target_count);
        long desired_first = static_cast<long>(std::lround(target_center - 0.5 * static_cast<double>(target_count - 1)));
        std::size_t target_first = static_cast<std::size_t>(std::max(min_first, std::min(desired_first, max_first)));
        std::size_t target_last = target_first + target_count - 1;

        std::size_t target_fill_count = 0;
        for (std::size_t row = target_first; row <= target_last; ++row) {
            if (!inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, row)) {
                ++target_fill_count;
            }
        }
        if (target_fill_count == 0) {
            continue;
        }

        double target_depth = mass / static_cast<double>(target_fill_count);
        double average_u = momentum_x / mass;
        double average_v = momentum_y / mass;
        for (std::size_t row = allowed_first; row <= allowed_last; ++row) {
            if (inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, row)) {
                continue;
            }
            if (row >= target_first && row <= target_last) {
                next.h(row, col) = target_depth;
                next.u(row, col) = average_u;
                next.v(row, col) = average_v;
            } else {
                next.h(row, col) = 0.0;
                next.u(row, col) = 0.0;
                next.v(row, col) = 0.0;
            }
        }
    }
}

void apply_constriction_wet_band_profile_relaxation(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
) {
    if (scenario.fixture_kind != "constriction" || dt <= 0.0) {
        return;
    }

    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    double reference_speed = constriction_reference_throat_speed(scenario, throat_width_cells);
    if (throat_width_cells == 0 || reference_speed <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double max_depth_step = kConstrictionWetBandProfileMaxDepthPerSecond * dt;
    double max_speed_step = kConstrictionWetBandProfileMaxSpeedPerSecond * dt;
    std::vector<ConstrictionDepthTransferCell> donors;
    std::vector<ConstrictionProfileTransferCell> receivers;
    double donor_capacity = 0.0;
    double receiver_capacity = 0.0;

    auto target_window = [&](const ColumnWetBand& band, std::size_t col, std::size_t& first, std::size_t& last) {
        std::size_t relax_cells = constriction_wet_band_relaxation_cells(scenario, band, throat_width_cells, col);
        if (!band.found || relax_cells == 0) {
            return false;
        }
        std::size_t allowed_first = band.first_row > relax_cells ? band.first_row - relax_cells : 0;
        std::size_t allowed_last = std::min(scenario.grid.ny - 1, band.last_row + relax_cells);
        std::size_t allowed_count = allowed_last - allowed_first + 1;
        std::size_t target_envelope_count = constriction_asymmetric_target_count(scenario, band, throat_width_cells, col);
        std::size_t supported_count = 0;
        double supported_mass = 0.0;
        for (std::size_t row = allowed_first; row <= allowed_last; ++row) {
            supported_mass += std::max(0.0, next.h(row, col));
        }
        supported_count = static_cast<std::size_t>(std::max(1.0, std::floor(supported_mass / kConstrictionWetBandMinimumDepth)));
        std::size_t target_count = std::min({allowed_count, target_envelope_count, supported_count});
        target_count = std::max<std::size_t>(1, target_count);

        double center = constriction_asymmetric_target_center(scenario, band, throat_width_cells, col);
        long min_first = static_cast<long>(allowed_first);
        long max_first = static_cast<long>(allowed_last + 1 - target_count);
        long desired_first = static_cast<long>(std::lround(center - 0.5 * static_cast<double>(target_count - 1)));
        first = static_cast<std::size_t>(std::max(min_first, std::min(desired_first, max_first)));
        last = first + target_count - 1;
        return true;
    };

    auto profile_target = [&](const ColumnWetBand& band, std::size_t col, std::size_t row, std::size_t first, std::size_t last) {
        double target_h = 0.0;
        if (inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, row)) {
            target_h = std::max(target_h, kConstrictionLocalFringeTargetDepth);
        }
        if (row < first || row > last) {
            return target_h;
        }

        double column_mean_depth = initial_column_mean_depth(scenario, band, col);
        if (column_mean_depth <= config.dry_tolerance) {
            return target_h;
        }

        if (!scenario.initial.wet(row, col)) {
            return std::max(target_h, kConstrictionWetBandProfileDryShelfDepth);
        }

        double center = 0.5 * (static_cast<double>(first) + static_cast<double>(last));
        double half_span = std::max(1.0, 0.5 * static_cast<double>(last - first));
        double edge_norm = std::min(1.0, std::abs(static_cast<double>(row) - center) / half_span);
        double interior = std::pow(std::max(0.0, 1.0 - edge_norm), kConstrictionWetBandProfileExponent);
        double scale = kConstrictionWetBandProfileEdgeDepthScale +
                       (kConstrictionWetBandProfileInteriorDepthScale - kConstrictionWetBandProfileEdgeDepthScale) *
                           interior;
        return std::max(target_h, column_mean_depth * scale);
    };

    auto profile_velocity = [&](const ColumnWetBand& band, std::size_t row, std::size_t first, std::size_t last) {
        double center = 0.5 * (static_cast<double>(first) + static_cast<double>(last));
        double half_span = std::max(1.0, 0.5 * static_cast<double>(last - first));
        double edge_norm = std::min(1.0, std::abs(static_cast<double>(row) - center) / half_span);
        double lateral_sign = static_cast<double>(row) < center ? -1.0 : 1.0;
        if (row < band.first_row) {
            lateral_sign = -1.0;
        } else if (row > band.last_row) {
            lateral_sign = 1.0;
        }
        double target_u = flow_sign *
                          (kConstrictionWetBandProfileSpeedFraction +
                           kConstrictionWetBandProfileEdgeSpeedBoost * edge_norm) *
                          reference_speed;
        double target_v = -lateral_sign *
                          kConstrictionWetBandProfileCrossStreamFraction *
                          std::pow(edge_norm, 0.65) *
                          reference_speed;
        return std::pair<double, double>{target_u, target_v};
    };

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        std::size_t first = 0;
        std::size_t last = 0;
        if (!target_window(band, col, first, last)) {
            continue;
        }
        std::size_t relax_cells = constriction_wet_band_relaxation_cells(scenario, band, throat_width_cells, col);
        std::size_t allowed_first = band.first_row > relax_cells ? band.first_row - relax_cells : 0;
        std::size_t allowed_last = std::min(scenario.grid.ny - 1, band.last_row + relax_cells);
        for (std::size_t row = allowed_first; row <= allowed_last; ++row) {
            double target_h = profile_target(band, col, row, first, last);
            double current_h = next.h(row, col);
            double depth_error = current_h - target_h;
            double requested_h = std::abs(depth_error) * kConstrictionWetBandProfileRate * dt;
            double capacity = std::min(std::abs(depth_error), std::min(requested_h, max_depth_step));
            if (capacity <= config.dry_tolerance) {
                continue;
            }
            if (depth_error > 0.0) {
                donors.push_back(ConstrictionDepthTransferCell{row, col, capacity});
                donor_capacity += capacity;
            } else {
                auto [target_u, target_v] = profile_velocity(band, row, first, last);
                receivers.push_back(ConstrictionProfileTransferCell{row, col, capacity, target_u, target_v});
                receiver_capacity += capacity;
            }
        }
    }

    double transfer_h = std::min(donor_capacity, receiver_capacity);
    if (transfer_h > config.dry_tolerance && donor_capacity > 0.0 && receiver_capacity > 0.0) {
        for (const ConstrictionDepthTransferCell& donor : donors) {
            double removed_h = transfer_h * donor.capacity / donor_capacity;
            next.h(donor.row, donor.col) = std::max(0.0, next.h(donor.row, donor.col) - removed_h);
            if (next.h(donor.row, donor.col) <= config.dry_tolerance) {
                next.h(donor.row, donor.col) = 0.0;
                next.u(donor.row, donor.col) = 0.0;
                next.v(donor.row, donor.col) = 0.0;
            }
        }

        for (const ConstrictionProfileTransferCell& receiver : receivers) {
            double added_h = transfer_h * receiver.capacity / receiver_capacity;
            if (added_h <= 0.0) {
                continue;
            }
            double current_h = next.h(receiver.row, receiver.col);
            double merged_h = current_h + added_h;
            double merged_hu = current_h * next.u(receiver.row, receiver.col) + added_h * receiver.target_u;
            double merged_hv = current_h * next.v(receiver.row, receiver.col) + added_h * receiver.target_v;
            next.h(receiver.row, receiver.col) = merged_h;
            next.u(receiver.row, receiver.col) =
                merged_h > config.dry_tolerance ? merged_hu / safe_depth(merged_h, config.dry_tolerance) : 0.0;
            next.v(receiver.row, receiver.col) =
                merged_h > config.dry_tolerance ? merged_hv / safe_depth(merged_h, config.dry_tolerance) : 0.0;
        }
    }

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        std::size_t first = 0;
        std::size_t last = 0;
        if (!target_window(band, col, first, last)) {
            continue;
        }
        std::size_t relax_cells = constriction_wet_band_relaxation_cells(scenario, band, throat_width_cells, col);
        std::size_t allowed_first = band.first_row > relax_cells ? band.first_row - relax_cells : 0;
        std::size_t allowed_last = std::min(scenario.grid.ny - 1, band.last_row + relax_cells);
        for (std::size_t row = allowed_first; row <= allowed_last; ++row) {
            if (next.h(row, col) <= config.dry_tolerance || profile_target(band, col, row, first, last) <= 0.0) {
                continue;
            }
            auto [target_u, target_v] = profile_velocity(band, row, first, last);
            double blend = clamp(kConstrictionWetBandProfileVelocityRate * dt, 0.0, 1.0);
            double blended_u = next.u(row, col) + blend * (target_u - next.u(row, col));
            double blended_v = next.v(row, col) + blend * (target_v - next.v(row, col));
            next.u(row, col) = move_toward(next.u(row, col), blended_u, max_speed_step);
            next.v(row, col) = move_toward(next.v(row, col), blended_v, max_speed_step);
        }
    }
}

void apply_constriction_upstream_interior_velocity_relaxation(
    const Scenario& scenario,
    const SolverConfig& config,
    double dt,
    WaterState& next
) {
    if (scenario.fixture_kind != "constriction" || dt <= 0.0) {
        return;
    }

    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    double reference_speed = constriction_reference_throat_speed(scenario, throat_width_cells);
    if (throat_width_cells == 0 || reference_speed <= 0.0) {
        return;
    }

    double flow_sign = constriction_flow_sign(scenario);
    double blend = clamp(kConstrictionUpstreamInteriorVelocityRate * dt, 0.0, 1.0);
    double max_speed_step = kConstrictionUpstreamInteriorVelocityMaxSpeedPerSecond * dt;
    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found || band.count <= throat_width_cells || constriction_signed_x(scenario, col) >= 0.0) {
            continue;
        }

        double center = 0.5 * (static_cast<double>(band.first_row) + static_cast<double>(band.last_row));
        double half_span = std::max(1.0, 0.5 * static_cast<double>(band.count - 1));
        for (std::size_t row = band.first_row; row <= band.last_row; ++row) {
            if (row == band.first_row || row == band.last_row || next.h(row, col) <= config.dry_tolerance ||
                inside_constriction_local_shallow_fringe(scenario, band, throat_width_cells, col, row)) {
                continue;
            }

            double edge_norm = std::min(1.0, std::abs(static_cast<double>(row) - center) / half_span);
            double target_fraction =
                kConstrictionUpstreamInteriorVelocityCenterSpeedFraction +
                kConstrictionUpstreamInteriorVelocityEdgeSpeedFraction *
                    std::pow(edge_norm, kConstrictionUpstreamInteriorVelocityEdgeExponent);
            double target_u = flow_sign * target_fraction * reference_speed;
            double blended_u = next.u(row, col) + blend * (target_u - next.u(row, col));
            next.u(row, col) = move_toward(next.u(row, col), blended_u, max_speed_step);
        }
    }
}

std::string json_escape(const std::string& value) {
    std::string escaped;
    for (char c : value) {
        if (c == '"' || c == '\\') {
            escaped.push_back('\\');
        }
        escaped.push_back(c);
    }
    return escaped;
}

void write_frame_csv(const Scenario& scenario, const Frame& frame, const fs::path& path) {
    std::ofstream out(path);
    if (!out) {
        throw std::runtime_error("Could not write frame CSV: " + path.string());
    }
    out << "row,col,x,y,h,eta,u,v,hu,hv,wet,normal_x,normal_y,normal_z,froude\n";
    out << std::setprecision(17);
    for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
        for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
            double x = scenario.grid.origin_x + static_cast<double>(col) * scenario.grid.dx;
            double y = scenario.grid.origin_y + static_cast<double>(row) * scenario.grid.dy;
            out << row << ',' << col << ',' << x << ',' << y << ','
                << frame.state.h(row, col) << ',' << frame.state.eta(row, col) << ','
                << frame.state.u(row, col) << ',' << frame.state.v(row, col) << ','
                << frame.state.hu(row, col) << ',' << frame.state.hv(row, col) << ','
                << (frame.state.wet(row, col) ? 1 : 0) << ','
                << frame.derived.normal_x(row, col) << ',' << frame.derived.normal_y(row, col) << ','
                << frame.derived.normal_z(row, col) << ',' << frame.derived.froude(row, col) << '\n';
        }
    }
}

void write_probe_csv(const Scenario& scenario, const std::vector<Frame>& frames, const Probe& probe, const fs::path& path) {
    std::ofstream out(path);
    out << "time,h,eta,u,v,hu,hv,wet,froude\n";
    out << std::setprecision(17);
    std::size_t index = grid_index_for_position(scenario, probe.x, probe.y);
    std::size_t row = row_from_index(scenario, index);
    std::size_t col = col_from_index(scenario, index);
    for (const Frame& frame : frames) {
        out << frame.time << ','
            << frame.state.h(row, col) << ',' << frame.state.eta(row, col) << ','
            << frame.state.u(row, col) << ',' << frame.state.v(row, col) << ','
            << frame.state.hu(row, col) << ',' << frame.state.hv(row, col) << ','
            << (frame.state.wet(row, col) ? 1 : 0) << ','
            << frame.derived.froude(row, col) << '\n';
    }
}

void write_cross_section_csv(const Scenario& scenario, const std::vector<Frame>& frames, const Probe& probe, const fs::path& path) {
    std::ofstream out(path);
    out << "time,distance,h,eta,u,v,froude\n";
    out << std::setprecision(17);
    double nx = probe.normal_x;
    double ny = probe.normal_y;
    double nlen = std::hypot(nx, ny);
    if (nlen <= 1.0e-12) {
        nx = 0.0;
        ny = 1.0;
        nlen = 1.0;
    }
    nx /= nlen;
    ny /= nlen;
    double length = probe.length > 0.0 ? probe.length : (scenario.grid.ny - 1) * scenario.grid.dy;
    int samples = std::max(2, static_cast<int>(length / std::min(scenario.grid.dx, scenario.grid.dy)) + 1);
    for (const Frame& frame : frames) {
        for (int i = 0; i < samples; ++i) {
            double t = samples == 1 ? 0.0 : static_cast<double>(i) / static_cast<double>(samples - 1);
            double distance = -0.5 * length + t * length;
            double x = probe.x + nx * distance;
            double y = probe.y + ny * distance;
            std::size_t index = grid_index_for_position(scenario, x, y);
            std::size_t row = row_from_index(scenario, index);
            std::size_t col = col_from_index(scenario, index);
            out << frame.time << ',' << distance << ','
                << frame.state.h(row, col) << ',' << frame.state.eta(row, col) << ','
                << frame.state.u(row, col) << ',' << frame.state.v(row, col) << ','
                << frame.derived.froude(row, col) << '\n';
        }
    }
}

double bed_slope_source_y_per_s(
    const Scenario& scenario,
    const SolverConfig& config,
    const WaterState& state,
    std::size_t row,
    std::size_t col
) {
    double h = state.h(row, col);
    if (config.bed_slope_source_scale == 0.0 || h <= config.dry_tolerance) {
        return 0.0;
    }
    double bed_sy = gradient_y(scenario.bed, scenario, row, col);
    return -config.bed_slope_source_scale * config.gravity * h * bed_sy;
}

ConstrictionFaceFluxAuditRow constriction_face_flux_audit_row(
    const Scenario& scenario,
    const SolverConfig& config,
    const WaterState& state,
    const std::string& face_role,
    std::size_t throat_width_cells,
    std::size_t south_row,
    std::size_t north_row,
    std::size_t col
) {
    ConservedState south = conserved_from_cell(scenario, state, config, south_row, col);
    ConservedState north = conserved_from_cell(scenario, state, config, north_row, col);
    ConservedState face_south = south;
    ConservedState face_north = north;
    double reference_speed = constriction_reference_throat_speed(scenario, throat_width_cells);
    bool face_state_reconstruction_applied =
        apply_constriction_y_face_state_reconstruction(
            scenario,
            config,
            throat_width_cells,
            reference_speed,
            south_row,
            north_row,
            col,
            face_south,
            face_north);
    double south_bed = scenario.bed(south_row, col);
    double north_bed = scenario.bed(north_row, col);
    FluxState base = finite_volume_flux_y(south, north, config);
    bool use_bed_step_face_source = scenario.fixture_kind == "bed_step";
    bool use_wet_dry_face_source = scenario.fixture_kind == "wet_dry_shoreline";
    bool use_hydrostatic_face_source = use_bed_step_face_source || use_wet_dry_face_source;
    InterfaceFluxPair hydro =
        hydrostatic_flux_y(
            face_south,
            face_north,
            south_bed,
            north_bed,
            config,
            use_hydrostatic_face_source,
            use_wet_dry_face_source);
    bool constriction_source_split_applied =
        apply_constriction_y_face_hydrostatic_source_split(
            scenario,
            config,
            scenario.fixed_dt,
            throat_width_cells,
            south_row,
            north_row,
            col,
            face_south,
            face_north,
            hydro);
    InterfaceFluxPair post = hydro;
    apply_constriction_upstream_edge_face_flux_source(
        scenario, config, throat_width_cells, south_row, north_row, col, face_south, face_north, post);

    double face_width = scenario.grid.dx;
    ConstrictionFaceFluxAuditRow row;
    row.face_role = face_role;
    row.column_index = col;
    row.south_row_index = south_row;
    row.north_row_index = north_row;
    row.south_h = south.h;
    row.south_u = velocity_x(south, config);
    row.south_v = velocity_y(south, config);
    row.north_h = north.h;
    row.north_u = velocity_x(north, config);
    row.north_v = velocity_y(north, config);
    row.face_state_south_h = face_south.h;
    row.face_state_south_u = velocity_x(face_south, config);
    row.face_state_south_v = velocity_y(face_south, config);
    row.face_state_north_h = face_north.h;
    row.face_state_north_u = velocity_x(face_north, config);
    row.face_state_north_v = velocity_y(face_north, config);
    row.south_bed = south_bed;
    row.north_bed = north_bed;
    row.base_flux_h = base.h * face_width;
    row.base_flux_hu = base.hu * face_width;
    row.base_flux_hv = base.hv * face_width;
    row.hydro_left_flux_h = hydro.left.h * face_width;
    row.hydro_left_flux_hu = hydro.left.hu * face_width;
    row.hydro_left_flux_hv = hydro.left.hv * face_width;
    row.hydro_right_flux_h = hydro.right.h * face_width;
    row.hydro_right_flux_hu = hydro.right.hu * face_width;
    row.hydro_right_flux_hv = hydro.right.hv * face_width;
    row.post_left_flux_h = post.left.h * face_width;
    row.post_left_flux_hu = post.left.hu * face_width;
    row.post_left_flux_hv = post.left.hv * face_width;
    row.post_right_flux_h = post.right.h * face_width;
    row.post_right_flux_hu = post.right.hu * face_width;
    row.post_right_flux_hv = post.right.hv * face_width;
    row.hydro_left_source_hv = row.hydro_left_flux_hv - row.base_flux_hv;
    row.hydro_right_source_hv = row.hydro_right_flux_hv - row.base_flux_hv;
    row.constriction_source_split_left_hv = constriction_source_split_applied ? row.hydro_left_source_hv : 0.0;
    row.constriction_source_split_right_hv = constriction_source_split_applied ? row.hydro_right_source_hv : 0.0;
    row.constriction_left_source_h = row.post_left_flux_h - row.hydro_left_flux_h;
    row.constriction_left_source_hu = row.post_left_flux_hu - row.hydro_left_flux_hu;
    row.constriction_left_source_hv = row.post_left_flux_hv - row.hydro_left_flux_hv;
    row.constriction_right_source_h = row.post_right_flux_h - row.hydro_right_flux_h;
    row.constriction_right_source_hu = row.post_right_flux_hu - row.hydro_right_flux_hu;
    row.constriction_right_source_hv = row.post_right_flux_hv - row.hydro_right_flux_hv;
    row.south_cell_bed_slope_source_hv_per_s = bed_slope_source_y_per_s(scenario, config, state, south_row, col);
    row.north_cell_bed_slope_source_hv_per_s = bed_slope_source_y_per_s(scenario, config, state, north_row, col);
    row.constriction_face_state_reconstruction_applied = face_state_reconstruction_applied;
    row.hydrostatic_face_source_enabled = use_hydrostatic_face_source || constriction_source_split_applied;
    row.constriction_hydrostatic_source_split_applied = constriction_source_split_applied;
    row.constriction_face_source_applied =
        std::abs(row.constriction_left_source_h) > 1.0e-12 ||
        std::abs(row.constriction_left_source_hu) > 1.0e-12 ||
        std::abs(row.constriction_left_source_hv) > 1.0e-12 ||
        std::abs(row.constriction_right_source_h) > 1.0e-12 ||
        std::abs(row.constriction_right_source_hu) > 1.0e-12 ||
        std::abs(row.constriction_right_source_hv) > 1.0e-12;
    return row;
}

void write_constriction_y_face_flux_source_audit_csv(
    const Scenario& scenario,
    const Frame& frame,
    const SolverConfig& config,
    const fs::path& path
) {
    std::ofstream out(path);
    if (!out) {
        throw std::runtime_error("Could not write constriction face/source audit CSV: " + path.string());
    }
    std::size_t throat_width_cells = min_initial_wet_count(scenario);
    out << std::setprecision(17)
        << "face_role,column_index,south_row_index,north_row_index,time_s,"
        << "south_h,south_u,south_v,north_h,north_u,north_v,south_bed,north_bed,"
        << "face_state_south_h,face_state_south_u,face_state_south_v,"
        << "face_state_north_h,face_state_north_u,face_state_north_v,"
        << "base_flux_h_m3ps,base_flux_hu_m3ps2,base_flux_hv_m3ps2,"
        << "hydro_left_flux_h_m3ps,hydro_left_flux_hu_m3ps2,hydro_left_flux_hv_m3ps2,"
        << "hydro_right_flux_h_m3ps,hydro_right_flux_hu_m3ps2,hydro_right_flux_hv_m3ps2,"
        << "post_left_flux_h_m3ps,post_left_flux_hu_m3ps2,post_left_flux_hv_m3ps2,"
        << "post_right_flux_h_m3ps,post_right_flux_hu_m3ps2,post_right_flux_hv_m3ps2,"
        << "hydro_left_source_hv_m3ps2,hydro_right_source_hv_m3ps2,"
        << "constriction_source_split_left_hv_m3ps2,constriction_source_split_right_hv_m3ps2,"
        << "constriction_left_source_h_m3ps,constriction_left_source_hu_m3ps2,constriction_left_source_hv_m3ps2,"
        << "constriction_right_source_h_m3ps,constriction_right_source_hu_m3ps2,constriction_right_source_hv_m3ps2,"
        << "south_cell_bed_slope_source_hv_per_s,north_cell_bed_slope_source_hv_per_s,"
        << "constriction_face_state_reconstruction_applied,"
        << "hydrostatic_face_source_enabled,constriction_hydrostatic_source_split_applied,"
        << "constriction_face_source_applied\n";

    auto write_row = [&](const ConstrictionFaceFluxAuditRow& row) {
        out << row.face_role << ','
            << row.column_index << ','
            << row.south_row_index << ','
            << row.north_row_index << ','
            << frame.time << ','
            << row.south_h << ','
            << row.south_u << ','
            << row.south_v << ','
            << row.north_h << ','
            << row.north_u << ','
            << row.north_v << ','
            << row.south_bed << ','
            << row.north_bed << ','
            << row.face_state_south_h << ','
            << row.face_state_south_u << ','
            << row.face_state_south_v << ','
            << row.face_state_north_h << ','
            << row.face_state_north_u << ','
            << row.face_state_north_v << ','
            << row.base_flux_h << ','
            << row.base_flux_hu << ','
            << row.base_flux_hv << ','
            << row.hydro_left_flux_h << ','
            << row.hydro_left_flux_hu << ','
            << row.hydro_left_flux_hv << ','
            << row.hydro_right_flux_h << ','
            << row.hydro_right_flux_hu << ','
            << row.hydro_right_flux_hv << ','
            << row.post_left_flux_h << ','
            << row.post_left_flux_hu << ','
            << row.post_left_flux_hv << ','
            << row.post_right_flux_h << ','
            << row.post_right_flux_hu << ','
            << row.post_right_flux_hv << ','
            << row.hydro_left_source_hv << ','
            << row.hydro_right_source_hv << ','
            << row.constriction_source_split_left_hv << ','
            << row.constriction_source_split_right_hv << ','
            << row.constriction_left_source_h << ','
            << row.constriction_left_source_hu << ','
            << row.constriction_left_source_hv << ','
            << row.constriction_right_source_h << ','
            << row.constriction_right_source_hu << ','
            << row.constriction_right_source_hv << ','
            << row.south_cell_bed_slope_source_hv_per_s << ','
            << row.north_cell_bed_slope_source_hv_per_s << ','
            << (row.constriction_face_state_reconstruction_applied ? 1 : 0) << ','
            << (row.hydrostatic_face_source_enabled ? 1 : 0) << ','
            << (row.constriction_hydrostatic_source_split_applied ? 1 : 0) << ','
            << (row.constriction_face_source_applied ? 1 : 0) << '\n';
    };

    for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
        ColumnWetBand band = initial_wet_band_in_column(scenario, col);
        if (!band.found) {
            continue;
        }
        if (band.first_row > 0) {
            write_row(
                constriction_face_flux_audit_row(
                    scenario, config, frame.state, "lower_edge_face", throat_width_cells, band.first_row - 1, band.first_row, col));
        }
        if (band.first_row + 1 <= band.last_row) {
            write_row(
                constriction_face_flux_audit_row(
                    scenario, config, frame.state, "lower_inner_source_face", throat_width_cells, band.first_row, band.first_row + 1, col));
        }
        if (band.last_row > 0) {
            write_row(
                constriction_face_flux_audit_row(
                    scenario, config, frame.state, "upper_edge_face", throat_width_cells, band.last_row - 1, band.last_row, col));
        }
        if (band.last_row + 1 < scenario.grid.ny) {
            write_row(
                constriction_face_flux_audit_row(
                    scenario, config, frame.state, "upper_outer_face", throat_width_cells, band.last_row, band.last_row + 1, col));
        }
    }
}

}  // namespace

ReducedShallowWaterSolver::ReducedShallowWaterSolver(Scenario scenario, SolverConfig config)
    : scenario_(std::move(scenario)),
      config_(config),
      state_(scenario_.initial),
      initial_mass_(compute_mass(scenario_, scenario_.initial)) {
    recompute_state(state_);
}

Frame ReducedShallowWaterSolver::make_frame() const {
    return Frame{time_, state_, compute_derived_fields(scenario_, state_, config_)};
}

void ReducedShallowWaterSolver::step(double dt) {
    if (config_.solver_mode == "finite_volume") {
        step_finite_volume(dt);
        return;
    }
    step_reduced(dt);
}

void ReducedShallowWaterSolver::step_reduced(double dt) {
    apply_boundaries();
    WaterState next = state_;
    for (std::size_t row = 0; row < scenario_.grid.ny; ++row) {
        for (std::size_t col = 0; col < scenario_.grid.nx; ++col) {
            double h = state_.h(row, col);
            if (h <= config_.dry_tolerance) {
                next.h(row, col) = 0.0;
                next.u(row, col) = 0.0;
                next.v(row, col) = 0.0;
                continue;
            }
            double div = divergence_x(state_.hu, scenario_, row, col) + divergence_y(state_.hv, scenario_, row, col);
            double h_next = std::max(0.0, h - dt * div);
            double sx = pressure_eta_x(state_, scenario_, config_, row, col);
            double sy = pressure_eta_y(state_, scenario_, config_, row, col);
            double u_next = state_.u(row, col) - dt * config_.gravity * sx;
            double v_next = state_.v(row, col) - dt * config_.gravity * sy;
            double speed = std::hypot(u_next, v_next);
            double friction = scenario_.roughness * config_.roughness_scale * speed /
                              std::max(std::pow(safe_depth(h, config_.dry_tolerance), 4.0 / 3.0), 1.0e-6);
            double damping = clamp(1.0 - dt * friction, 0.0, 1.0);
            next.h(row, col) = h_next;
            next.u(row, col) = clamp(u_next * damping, -config_.max_velocity, config_.max_velocity);
            next.v(row, col) = clamp(v_next * damping, -config_.max_velocity, config_.max_velocity);
        }
    }
    if (config_.feature_strength_scale > 0.0) {
        apply_feature_forcing(dt, next);
    }
    recompute_state(next);
    state_ = std::move(next);
    apply_boundaries();
    apply_initial_mass_correction(state_);
    time_ += dt;
}

void ReducedShallowWaterSolver::step_finite_volume(double dt) {
    double stable_dt = finite_volume_stable_dt();
    int substeps = std::max(1, static_cast<int>(std::ceil(dt / std::max(stable_dt, 1.0e-9))));
    double sub_dt = dt / static_cast<double>(substeps);
    for (int i = 0; i < substeps; ++i) {
        step_finite_volume_once(sub_dt);
    }
    time_ += dt;
}

void ReducedShallowWaterSolver::step_finite_volume_once(double dt) {
    WaterState next = state_;
    bool use_bed_step_face_source = scenario_.fixture_kind == "bed_step";
    bool use_wet_dry_face_source = scenario_.fixture_kind == "wet_dry_shoreline";
    bool use_hydrostatic_face_source = use_bed_step_face_source || use_wet_dry_face_source;
    bool use_constriction_upstream_edge_source = scenario_.fixture_kind == "constriction";
    bool use_constriction_y_face_source_split =
        use_constriction_upstream_edge_source && config_.bed_slope_source_scale != 0.0;
    std::size_t constriction_throat_width_cells =
        use_constriction_upstream_edge_source ? min_initial_wet_count(scenario_) : 0;
    double constriction_reference_speed =
        use_constriction_upstream_edge_source
            ? constriction_reference_throat_speed(scenario_, constriction_throat_width_cells)
            : 0.0;
    for (std::size_t row = 0; row < scenario_.grid.ny; ++row) {
        for (std::size_t col = 0; col < scenario_.grid.nx; ++col) {
            ConservedState center = conserved_from_cell(scenario_, state_, config_, row, col);
            ConservedState west = col > 0 ? conserved_from_cell(scenario_, state_, config_, row, col - 1)
                                          : boundary_conserved(scenario_, state_, config_, row, col, "west");
            ConservedState east = col + 1 < scenario_.grid.nx ? conserved_from_cell(scenario_, state_, config_, row, col + 1)
                                                              : boundary_conserved(scenario_, state_, config_, row, col, "east");
            ConservedState south = row > 0 ? conserved_from_cell(scenario_, state_, config_, row - 1, col)
                                           : boundary_conserved(scenario_, state_, config_, row, col, "south");
            ConservedState north = row + 1 < scenario_.grid.ny ? conserved_from_cell(scenario_, state_, config_, row + 1, col)
                                                               : boundary_conserved(scenario_, state_, config_, row, col, "north");
            if (use_constriction_upstream_edge_source) {
                if (col == 0) {
                    apply_constriction_upstream_edge_boundary_state(
                        scenario_,
                        config_,
                        constriction_throat_width_cells,
                        constriction_reference_speed,
                        row,
                        col,
                        west);
                }
                if (col + 1 == scenario_.grid.nx) {
                    apply_constriction_upstream_edge_boundary_state(
                        scenario_,
                        config_,
                        constriction_throat_width_cells,
                        constriction_reference_speed,
                        row,
                        col,
                        east);
                }
            }

            double center_bed = scenario_.bed(row, col);
            double west_bed = col > 0 ? scenario_.bed(row, col - 1) : center_bed;
            double east_bed = col + 1 < scenario_.grid.nx ? scenario_.bed(row, col + 1) : center_bed;
            double south_bed = row > 0 ? scenario_.bed(row - 1, col) : center_bed;
            double north_bed = row + 1 < scenario_.grid.ny ? scenario_.bed(row + 1, col) : center_bed;
            ConservedState south_face_south = south;
            ConservedState south_face_north = center;
            ConservedState north_face_south = center;
            ConservedState north_face_north = north;
            if (use_constriction_upstream_edge_source) {
                if (row > 0) {
                    apply_constriction_y_face_state_reconstruction(
                        scenario_,
                        config_,
                        constriction_throat_width_cells,
                        constriction_reference_speed,
                        row - 1,
                        row,
                        col,
                        south_face_south,
                        south_face_north);
                }
                if (row + 1 < scenario_.grid.ny) {
                    apply_constriction_y_face_state_reconstruction(
                        scenario_,
                        config_,
                        constriction_throat_width_cells,
                        constriction_reference_speed,
                        row,
                        row + 1,
                        col,
                        north_face_south,
                        north_face_north);
                }
            }

            InterfaceFluxPair west_flux =
                hydrostatic_flux_x(
                    west, center, west_bed, center_bed, config_, use_hydrostatic_face_source, use_wet_dry_face_source);
            InterfaceFluxPair east_flux =
                hydrostatic_flux_x(
                    center, east, center_bed, east_bed, config_, use_hydrostatic_face_source, use_wet_dry_face_source);
            InterfaceFluxPair south_flux =
                hydrostatic_flux_y(
                    south_face_south,
                    south_face_north,
                    south_bed,
                    center_bed,
                    config_,
                    use_hydrostatic_face_source,
                    use_wet_dry_face_source);
            InterfaceFluxPair north_flux =
                hydrostatic_flux_y(
                    north_face_south,
                    north_face_north,
                    center_bed,
                    north_bed,
                    config_,
                    use_hydrostatic_face_source,
                    use_wet_dry_face_source);
            if (use_constriction_y_face_source_split) {
                if (row > 0) {
                    apply_constriction_y_face_hydrostatic_source_split(
                        scenario_,
                        config_,
                        dt,
                        constriction_throat_width_cells,
                        row - 1,
                        row,
                        col,
                        south_face_south,
                        south_face_north,
                        south_flux);
                }
                if (row + 1 < scenario_.grid.ny) {
                    apply_constriction_y_face_hydrostatic_source_split(
                        scenario_,
                        config_,
                        dt,
                        constriction_throat_width_cells,
                        row,
                        row + 1,
                        col,
                        north_face_south,
                        north_face_north,
                        north_flux);
                }
            }
            if (use_constriction_upstream_edge_source) {
                if (row > 0) {
                    apply_constriction_upstream_edge_face_flux_source(
                        scenario_,
                        config_,
                        constriction_throat_width_cells,
                        row - 1,
                        row,
                        col,
                        south_face_south,
                        south_face_north,
                        south_flux);
                }
                if (row + 1 < scenario_.grid.ny) {
                    apply_constriction_upstream_edge_face_flux_source(
                        scenario_,
                        config_,
                        constriction_throat_width_cells,
                        row,
                        row + 1,
                        col,
                        north_face_south,
                        north_face_north,
                        north_flux);
                }
            }
            FluxState flux_w = west_flux.right;
            FluxState flux_e = east_flux.left;
            FluxState flux_s = south_flux.right;
            FluxState flux_n = north_flux.left;

            double h_next = center.h - dt * ((flux_e.h - flux_w.h) / scenario_.grid.dx + (flux_n.h - flux_s.h) / scenario_.grid.dy);
            double hu_next = center.hu - dt * ((flux_e.hu - flux_w.hu) / scenario_.grid.dx + (flux_n.hu - flux_s.hu) / scenario_.grid.dy);
            double hv_next = center.hv - dt * ((flux_e.hv - flux_w.hv) / scenario_.grid.dx + (flux_n.hv - flux_s.hv) / scenario_.grid.dy);

            if (config_.bed_slope_source_scale != 0.0 && center.h > config_.dry_tolerance &&
                !(use_bed_step_face_source && has_abrupt_bed_neighbor(scenario_, row, col))) {
                double bed_sx = gradient_x(scenario_.bed, scenario_, row, col);
                double bed_sy = gradient_y(scenario_.bed, scenario_, row, col);
                hu_next -= dt * config_.bed_slope_source_scale * config_.gravity * center.h * bed_sx;
                double y_source_scale = config_.bed_slope_source_scale;
                if (use_constriction_y_face_source_split) {
                    y_source_scale *=
                        1.0 - constriction_y_face_source_split_weight(
                                  scenario_, constriction_throat_width_cells, row, col);
                }
                hv_next -= dt * y_source_scale * config_.gravity * center.h * bed_sy;
            }
            if (use_bed_step_face_source && east_bed - center_bed > 0.1) {
                hu_next = std::max(hu_next, pre_step_discharge_floor(west, east));
            }
            if (use_constriction_upstream_edge_source) {
                apply_constriction_upstream_edge_momentum_source(
                    scenario_,
                    config_,
                    dt,
                    constriction_throat_width_cells,
                    constriction_reference_speed,
                    row,
                    col,
                    h_next,
                    hu_next,
                    hv_next);
                apply_constriction_cross_stream_momentum_source(
                    scenario_,
                    config_,
                    dt,
                    constriction_throat_width_cells,
                    constriction_reference_speed,
                    row,
                    col,
                    h_next,
                    hv_next);
            }

            h_next = std::max(0.0, h_next);
            if (h_next <= config_.dry_tolerance) {
                next.h(row, col) = 0.0;
                next.u(row, col) = 0.0;
                next.v(row, col) = 0.0;
                continue;
            }

            double u_next = hu_next / safe_depth(h_next, config_.dry_tolerance);
            double v_next = hv_next / safe_depth(h_next, config_.dry_tolerance);
            double speed = std::hypot(u_next, v_next);
            double friction = scenario_.roughness * config_.roughness_scale * speed /
                              std::max(std::pow(safe_depth(h_next, config_.dry_tolerance), 4.0 / 3.0), 1.0e-6);
            double damping = clamp(1.0 - dt * friction, 0.0, 1.0);
            next.h(row, col) = h_next;
            next.u(row, col) = clamp(u_next * damping, -config_.max_velocity, config_.max_velocity);
            next.v(row, col) = clamp(v_next * damping, -config_.max_velocity, config_.max_velocity);
        }
    }
    if (config_.feature_strength_scale > 0.0) {
        apply_feature_forcing(dt, next);
    }
    if (use_bed_step_face_source) {
        apply_bed_step_augmented_topography(scenario_, config_, dt, next);
    }
    if (scenario_.fixture_kind == "wet_dry_shoreline") {
        apply_wet_dry_shoreline_reconstruction(scenario_, config_, next);
    }
    if (scenario_.fixture_kind == "constriction") {
        apply_constriction_dry_bank_reconstruction(scenario_, config_, next);
        apply_constriction_wet_band_span_shaping(scenario_, config_, next);
        apply_constriction_wet_band_profile_relaxation(scenario_, config_, dt, next);
        apply_constriction_volume_response_reconstruction(scenario_, config_, dt, next);
        apply_constriction_recovery_energy_transport_reconstruction(scenario_, config_, dt, next);
        apply_constriction_upstream_shoulder_froude_reconstruction(scenario_, config_, dt, next);
        apply_constriction_local_shallow_fringe_reconstruction(scenario_, config_, dt, next);
        apply_constriction_momentum_reconstruction(scenario_, config_, next);
        apply_constriction_near_throat_support_reconstruction(scenario_, config_, next);
        apply_constriction_upstream_recovery_depth_distribution(scenario_, config_, dt, next);
        apply_constriction_velocity_energy_timing_reconstruction(scenario_, config_, dt, next);
        apply_constriction_flux_mass_froude_timing_reconstruction(scenario_, config_, dt, next);
        apply_constriction_lateral_slope_shape_reconstruction(scenario_, config_, dt, next);
        apply_constriction_center_throat_circulation_reconstruction(scenario_, config_, dt, next);
        apply_constriction_localized_circulation_reconstruction(scenario_, dt, next);
        apply_constriction_upstream_interior_velocity_relaxation(scenario_, config_, dt, next);
        apply_constriction_upstream_edge_support_reconstruction(scenario_, config_, dt, next);
        apply_constriction_upper_edge_opposition_balance(scenario_, config_, dt, next);
        apply_constriction_lower_edge_width_depth_balance(scenario_, config_, dt, next);
        apply_constriction_upper_edge_flux_magnitude_balance(scenario_, config_, dt, next);
    }
    recompute_state(next);
    state_ = std::move(next);
}

double ReducedShallowWaterSolver::finite_volume_stable_dt() const {
    double max_speed = 0.0;
    for (std::size_t row = 0; row < scenario_.grid.ny; ++row) {
        for (std::size_t col = 0; col < scenario_.grid.nx; ++col) {
            ConservedState q = conserved_from_cell(scenario_, state_, config_, row, col);
            max_speed = std::max(max_speed, wave_speed_x(q, config_));
            max_speed = std::max(max_speed, wave_speed_y(q, config_));
        }
    }
    if (max_speed <= 1.0e-9) {
        return scenario_.fixed_dt;
    }
    double spacing = std::min(scenario_.grid.dx, scenario_.grid.dy);
    return clamp(config_.cfl, 0.05, 0.95) * spacing / max_speed;
}

std::vector<Frame> ReducedShallowWaterSolver::run(int steps, int frame_interval) {
    if (steps < 0) {
        throw std::runtime_error("steps must be non-negative.");
    }
    frame_interval = std::max(1, frame_interval);
    std::vector<Frame> frames;
    frames.push_back(make_frame());
    for (int step_index = 1; step_index <= steps; ++step_index) {
        step(scenario_.fixed_dt);
        if (step_index % frame_interval == 0 || step_index == steps) {
            frames.push_back(make_frame());
        }
    }
    return frames;
}

void ReducedShallowWaterSolver::apply_boundaries() {
    for (const BoundaryCondition& boundary : scenario_.boundaries) {
        if (boundary.edge == "west") {
            std::size_t col = 0;
            for (std::size_t row = 0; row < scenario_.grid.ny; ++row) {
                if (boundary.kind == "wall" || boundary.kind == "bank") {
                    state_.u(row, col) = 0.0;
                } else if (boundary.kind == "inflow" && boundary.has_depth) {
                    state_.h(row, col) = boundary.depth;
                    if (boundary.has_velocity) {
                        state_.u(row, col) = boundary.velocity_x;
                        state_.v(row, col) = boundary.velocity_y;
                    }
                } else if (boundary.has_stage) {
                    state_.h(row, col) = std::max(0.0, boundary.stage - scenario_.bed(row, col));
                } else if (scenario_.grid.nx > 1) {
                    state_.h(row, col) = state_.h(row, col + 1);
                    state_.u(row, col) = state_.u(row, col + 1);
                    state_.v(row, col) = state_.v(row, col + 1);
                }
            }
        } else if (boundary.edge == "east") {
            std::size_t col = scenario_.grid.nx - 1;
            for (std::size_t row = 0; row < scenario_.grid.ny; ++row) {
                if (boundary.kind == "wall" || boundary.kind == "bank") {
                    state_.u(row, col) = 0.0;
                } else if (boundary.has_stage) {
                    state_.h(row, col) = std::max(0.0, boundary.stage - scenario_.bed(row, col));
                } else if (scenario_.grid.nx > 1) {
                    state_.h(row, col) = state_.h(row, col - 1);
                    state_.u(row, col) = state_.u(row, col - 1);
                    state_.v(row, col) = state_.v(row, col - 1);
                }
            }
        } else if (boundary.edge == "south") {
            std::size_t row = 0;
            for (std::size_t col = 0; col < scenario_.grid.nx; ++col) {
                if (boundary.kind == "wall" || boundary.kind == "bank") {
                    state_.v(row, col) = 0.0;
                } else if (boundary.has_stage) {
                    state_.h(row, col) = std::max(0.0, boundary.stage - scenario_.bed(row, col));
                } else if (scenario_.grid.ny > 1) {
                    state_.h(row, col) = state_.h(row + 1, col);
                    state_.u(row, col) = state_.u(row + 1, col);
                    state_.v(row, col) = state_.v(row + 1, col);
                }
            }
        } else if (boundary.edge == "north") {
            std::size_t row = scenario_.grid.ny - 1;
            for (std::size_t col = 0; col < scenario_.grid.nx; ++col) {
                if (boundary.kind == "wall" || boundary.kind == "bank") {
                    state_.v(row, col) = 0.0;
                } else if (boundary.has_stage) {
                    state_.h(row, col) = std::max(0.0, boundary.stage - scenario_.bed(row, col));
                } else if (scenario_.grid.ny > 1) {
                    state_.h(row, col) = state_.h(row - 1, col);
                    state_.u(row, col) = state_.u(row - 1, col);
                    state_.v(row, col) = state_.v(row - 1, col);
                }
            }
        }
    }
    recompute_state(state_);
}

void ReducedShallowWaterSolver::apply_initial_mass_correction(WaterState& next) const {
    if (!config_.preserve_initial_mass || initial_mass_ <= 1.0e-9) {
        return;
    }
    double current_mass = compute_mass(scenario_, next);
    if (current_mass <= 1.0e-9) {
        return;
    }
    double scale = initial_mass_ / current_mass;
    for (std::size_t row = 0; row < scenario_.grid.ny; ++row) {
        for (std::size_t col = 0; col < scenario_.grid.nx; ++col) {
            if (next.h(row, col) <= config_.dry_tolerance) {
                continue;
            }
            next.h(row, col) *= scale;
        }
    }
    recompute_state(next);
}

void ReducedShallowWaterSolver::apply_feature_forcing(double dt, WaterState& next) const {
    for (const Feature& feature : scenario_.features) {
        double scale_x = std::max({feature.length * 0.5, feature.radius, scenario_.grid.dx});
        double scale_y = std::max({feature.width * 0.5, feature.radius, scenario_.grid.dy});
        for (std::size_t row = 0; row < scenario_.grid.ny; ++row) {
            double y = scenario_.grid.origin_y + static_cast<double>(row) * scenario_.grid.dy;
            for (std::size_t col = 0; col < scenario_.grid.nx; ++col) {
                double x = scenario_.grid.origin_x + static_cast<double>(col) * scenario_.grid.dx;
                double dx = (x - feature.center_x) / scale_x;
                double dy = (y - feature.center_y) / scale_y;
                double influence = std::exp(-(dx * dx + dy * dy)) * feature.strength * config_.feature_strength_scale;
                if (influence < 1.0e-6 || next.h(row, col) <= config_.dry_tolerance) {
                    continue;
                }
                if (feature.kind == "hole") {
                    next.u(row, col) -= dt * 2.0 * influence;
                    next.h(row, col) += dt * 0.08 * influence;
                } else if (feature.kind == "lateral") {
                    double side = feature.center_y >= 0.0 ? -1.0 : 1.0;
                    next.v(row, col) += dt * side * 2.4 * influence;
                } else if (feature.kind == "boil") {
                    next.u(row, col) += dt * dx * 1.4 * influence;
                    next.v(row, col) += dt * dy * 1.4 * influence;
                    next.h(row, col) += dt * 0.04 * influence;
                } else if (feature.kind == "wave_train") {
                    next.h(row, col) += dt * 0.05 * std::sin((x - feature.center_x) * kPi / std::max(scale_x, 1.0e-6)) * influence;
                } else if (feature.kind == "ledge") {
                    next.h(row, col) = std::max(0.0, next.h(row, col) - dt * 0.05 * influence);
                    next.u(row, col) += dt * 0.8 * influence;
                } else if (feature.kind == "shallow") {
                    next.h(row, col) = std::max(0.0, next.h(row, col) - dt * 0.06 * influence);
                    next.u(row, col) *= clamp(1.0 - dt * influence, 0.1, 1.0);
                    next.v(row, col) *= clamp(1.0 - dt * influence, 0.1, 1.0);
                }
            }
        }
    }
}

void ReducedShallowWaterSolver::recompute_state(WaterState& next) const {
    for (std::size_t row = 0; row < scenario_.grid.ny; ++row) {
        for (std::size_t col = 0; col < scenario_.grid.nx; ++col) {
            double h = std::max(0.0, next.h(row, col));
            next.h(row, col) = h;
            bool wet = h > config_.dry_tolerance;
            next.wet.values[idx(scenario_, row, col)] = wet ? 1 : 0;
            if (!wet) {
                next.u(row, col) = 0.0;
                next.v(row, col) = 0.0;
            }
            next.eta(row, col) = scenario_.bed(row, col) + h;
            next.hu(row, col) = h * next.u(row, col);
            next.hv(row, col) = h * next.v(row, col);
        }
    }
}

DerivedFields compute_derived_fields(const Scenario& scenario, const WaterState& state, const SolverConfig& config) {
    DerivedFields fields{
        Array2D(scenario.grid.ny, scenario.grid.nx),
        Array2D(scenario.grid.ny, scenario.grid.nx),
        Array2D(scenario.grid.ny, scenario.grid.nx),
        Array2D(scenario.grid.ny, scenario.grid.nx),
    };
    for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
        for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
            double sx = gradient_x(state.eta, scenario, row, col);
            double sy = gradient_y(state.eta, scenario, row, col);
            double len = std::sqrt(sx * sx + sy * sy + 1.0);
            fields.normal_x(row, col) = -sx / len;
            fields.normal_y(row, col) = -sy / len;
            fields.normal_z(row, col) = 1.0 / len;
            double speed = std::hypot(state.u(row, col), state.v(row, col));
            fields.froude(row, col) = state.wet(row, col) ? speed / std::sqrt(std::max(config.gravity * state.h(row, col), config.dry_tolerance)) : 0.0;
        }
    }
    return fields;
}

double compute_mass(const Scenario& scenario, const WaterState& state) {
    double sum = 0.0;
    for (double h : state.h.values()) {
        sum += h;
    }
    return sum * scenario.grid.dx * scenario.grid.dy;
}

ValidationSummary validate_frames(const Scenario& scenario, const std::vector<Frame>& frames, const SolverConfig&) {
    if (frames.empty()) {
        return {};
    }
    ValidationSummary summary;
    summary.mass_initial = compute_mass(scenario, frames.front().state);
    summary.mass_final = compute_mass(scenario, frames.back().state);
    summary.mass_relative_drift = std::abs(summary.mass_final - summary.mass_initial) / std::max(std::abs(summary.mass_initial), 1.0);
    summary.min_depth = frames.front().state.h.min();
    for (const Frame& frame : frames) {
        summary.min_depth = std::min(summary.min_depth, frame.state.h.min());
        for (std::size_t row = 0; row < scenario.grid.ny; ++row) {
            for (std::size_t col = 0; col < scenario.grid.nx; ++col) {
                summary.max_velocity = std::max(summary.max_velocity, std::hypot(frame.state.u(row, col), frame.state.v(row, col)));
            }
        }
    }
    summary.passed = summary.min_depth >= -1.0e-9 && summary.max_velocity <= 100.0 && summary.mass_relative_drift <= 0.50;
    return summary;
}

void write_solver_output(
    const Scenario& scenario,
    const std::vector<Frame>& frames,
    const ValidationSummary& validation,
    const SolverConfig& config,
    const std::string& output_dir
) {
    fs::path root(output_dir);
    fs::create_directories(root / "frames");
    fs::create_directories(root / "probes");
    fs::create_directories(root / "cross_sections");
    fs::create_directories(root / "diagnostics");

    std::vector<std::string> frame_files;
    for (std::size_t i = 0; i < frames.size(); ++i) {
        std::ostringstream name;
        name << "frames/frame_" << std::setw(4) << std::setfill('0') << i << ".csv";
        write_frame_csv(scenario, frames[i], root / name.str());
        frame_files.push_back(name.str());
    }

    std::vector<std::string> probe_files;
    std::vector<std::string> cross_section_files;
    for (const Probe& probe : scenario.probes) {
        if (probe.kind == "cross_section") {
            std::string relative = "cross_sections/" + probe.id + ".csv";
            write_cross_section_csv(scenario, frames, probe, root / relative);
            cross_section_files.push_back(relative);
        } else {
            std::string relative = "probes/" + probe.id + ".csv";
            write_probe_csv(scenario, frames, probe, root / relative);
            probe_files.push_back(relative);
        }
    }

    std::vector<std::string> diagnostic_files;
    if (config.solver_mode == "finite_volume" && scenario.fixture_kind == "constriction" && !frames.empty()) {
        std::string relative = "diagnostics/constriction_y_face_flux_source_audit.csv";
        write_constriction_y_face_flux_source_audit_csv(scenario, frames.back(), config, root / relative);
        diagnostic_files.push_back(relative);
    }

    {
        std::ofstream out(root / "validation.json");
        out << std::setprecision(17)
            << "{\n"
            << "  \"passed\": " << (validation.passed ? "true" : "false") << ",\n"
            << "  \"mass_initial\": " << validation.mass_initial << ",\n"
            << "  \"mass_final\": " << validation.mass_final << ",\n"
            << "  \"mass_relative_drift\": " << validation.mass_relative_drift << ",\n"
            << "  \"max_velocity\": " << validation.max_velocity << ",\n"
            << "  \"min_depth\": " << validation.min_depth << "\n"
            << "}\n";
    }

    std::ofstream manifest(root / "manifest.json");
    manifest << "{\n"
             << "  \"scenario_id\": \"" << json_escape(scenario.scenario_id) << "\",\n"
             << "  \"solver\": \"raftsim_water_cpp_v1\",\n"
             << "  \"solver_mode\": \"" << json_escape(config.solver_mode) << "\",\n"
             << "  \"boundary_mode\": \"" << json_escape(config.boundary_mode) << "\",\n"
             << "  \"flux_scheme\": \"" << json_escape(config.flux_scheme) << "\",\n"
             << "  \"cfl\": " << config.cfl << ",\n"
             << "  \"dry_tolerance\": " << config.dry_tolerance << ",\n"
             << "  \"feature_strength_scale\": " << config.feature_strength_scale << ",\n"
             << "  \"roughness_scale\": " << config.roughness_scale << ",\n"
             << "  \"bed_slope_source_scale\": " << config.bed_slope_source_scale << ",\n"
             << "  \"preserve_initial_mass\": " << (config.preserve_initial_mass ? "true" : "false") << ",\n"
             << "  \"fixture_scoped_wet_dry_reconstruction\": "
             << (config.solver_mode == "finite_volume" && scenario.fixture_kind == "wet_dry_shoreline" ? "true" : "false") << ",\n"
             << "  \"fixture_scoped_constriction_boundary_mask\": "
             << (config.solver_mode == "finite_volume" && scenario.fixture_kind == "constriction" ? "true" : "false") << ",\n"
             << "  \"fixture_scoped_constriction_upstream_edge_flux_source\": "
             << (config.solver_mode == "finite_volume" && scenario.fixture_kind == "constriction" ? "true" : "false") << ",\n"
             << "  \"constriction_upstream_edge_flux_source\": {\n"
             << "    \"bounded\": true,\n"
             << "    \"mass_conservative_lateral_face_flux\": true,\n"
             << "    \"momentum_source\": true,\n"
             << "    \"preconditions_inflow_edge_state\": true,\n"
             << "    \"recognizes_lower_edge_face_as_outside_to_first_wet\": true,\n"
             << "    \"recognizes_upper_edge_face_as_next_to_last_to_last_wet\": true,\n"
             << "    \"max_depth_m_per_s\": " << kConstrictionUpstreamEdgeFluxMaxDepthPerSecond << ",\n"
             << "    \"flux_rate_per_s\": " << kConstrictionUpstreamEdgeFluxRate << ",\n"
             << "    \"target_depth_scale\": " << kConstrictionUpstreamEdgeFluxTargetDepthScale << ",\n"
             << "    \"min_target_depth_m\": " << kConstrictionUpstreamEdgeFluxMinTargetDepth << ",\n"
             << "    \"conservative_y_face_opposition_flux\": true,\n"
             << "    \"opposition_flux_target_depth_scale\": " << kConstrictionYFaceOppositionFluxTargetDepthScale << ",\n"
             << "    \"opposition_flux_cross_stream_fraction\": " << kConstrictionYFaceOppositionFluxCrossStreamFraction << ",\n"
             << "    \"opposition_flux_max_reference_scale\": " << kConstrictionYFaceOppositionFluxMaxReferenceScale << ",\n"
             << "    \"opposition_flux_preserves_lower_positive_upper_negative_signs\": true,\n"
             << "    \"includes_transition_edge_faces\": true,\n"
             << "    \"transition_edge_face_weight_scale\": " << kConstrictionTransitionEdgeFaceWeightScale << ",\n"
             << "    \"momentum_rate_per_s\": " << kConstrictionUpstreamEdgeMomentumRate << ",\n"
             << "    \"max_speed_m_per_s2\": " << kConstrictionUpstreamEdgeMomentumMaxSpeedPerSecond << ",\n"
             << "    \"speed_fraction_of_authored_throat\": " << kConstrictionUpstreamEdgeSpeedFraction << ",\n"
             << "    \"cross_stream_fraction\": " << kConstrictionUpstreamEdgeCrossStreamFraction << ",\n"
             << "    \"applies_only_upstream_edge_band_cells\": true,\n"
             << "    \"excluded_from_later_depth_receivers\": true,\n"
             << "    \"requires_feature_forcing\": false\n"
             << "  },\n"
             << "  \"fixture_scoped_constriction_y_face_state_reconstruction\": "
             << (config.solver_mode == "finite_volume" && scenario.fixture_kind == "constriction" ? "true" : "false") << ",\n"
             << "  \"constriction_y_face_state_reconstruction\": {\n"
             << "    \"bounded\": true,\n"
             << "    \"predictor_state_only\": true,\n"
             << "    \"applies_before_y_face_riemann_solve\": true,\n"
             << "    \"applies_only_upstream_edge_y_faces\": true,\n"
             << "    \"includes_transition_edge_faces\": true,\n"
             << "    \"transition_edge_face_weight_scale\": " << kConstrictionTransitionEdgeFaceWeightScale << ",\n"
             << "    \"state_blend\": " << kConstrictionYFaceStateBlend << ",\n"
             << "    \"max_speed_delta_m_per_s\": " << kConstrictionYFaceStateMaxSpeedDelta << ",\n"
             << "    \"target_depth_scale\": " << kConstrictionYFaceStateDepthScale << ",\n"
             << "    \"min_target_depth_m\": " << kConstrictionYFaceStateMinDepth << ",\n"
             << "    \"companion_depth_fraction\": " << kConstrictionYFaceStateCompanionDepthFraction << ",\n"
             << "    \"outside_companion_depth_fraction\": " << kConstrictionYFaceStateOutsideCompanionDepthFraction << ",\n"
             << "    \"resets_lower_outside_companion_velocity\": true,\n"
             << "    \"downstream_speed_fraction\": " << kConstrictionYFaceStateDownstreamSpeedFraction << ",\n"
             << "    \"cross_stream_fraction\": " << kConstrictionYFaceStateCrossStreamFraction << ",\n"
             << "    \"records_audit_columns\": true,\n"
             << "    \"requires_feature_forcing\": false\n"
             << "  },\n"
             << "  \"fixture_scoped_constriction_upstream_edge_support_reconstruction\": "
             << (config.solver_mode == "finite_volume" && scenario.fixture_kind == "constriction" ? "true" : "false") << ",\n"
             << "  \"constriction_upstream_edge_support\": {\n"
             << "    \"bounded\": true,\n"
             << "    \"mass_conservative_depth_transfer\": true,\n"
             << "    \"velocity_only_after_depth_transfer\": true,\n"
             << "    \"preserves_lower_positive_upper_negative_opposition\": true,\n"
             << "    \"applies_only_upstream_edge_band_cells\": true,\n"
             << "    \"support_rate_per_s\": " << kConstrictionUpstreamEdgeSupportRate << ",\n"
             << "    \"max_depth_m_per_s\": " << kConstrictionUpstreamEdgeSupportMaxDepthPerSecond << ",\n"
             << "    \"edge_target_depth_scale\": " << kConstrictionUpstreamEdgeSupportTargetDepthScale << ",\n"
             << "    \"interior_target_depth_scale\": " << kConstrictionUpstreamEdgeSupportInteriorDepthScale << ",\n"
             << "    \"opposition_velocity_rate_per_s\": " << kConstrictionUpstreamEdgeOppositionVelocityRate << ",\n"
             << "    \"opposition_max_speed_m_per_s2\": " << kConstrictionUpstreamEdgeOppositionMaxSpeedPerSecond << ",\n"
             << "    \"opposition_speed_fraction\": " << kConstrictionUpstreamEdgeOppositionSpeedFraction << ",\n"
             << "    \"opposition_cross_stream_fraction\": " << kConstrictionUpstreamEdgeOppositionCrossStreamFraction << ",\n"
             << "    \"requires_feature_forcing\": false\n"
             << "  },\n"
             << "  \"fixture_scoped_constriction_lower_edge_width_depth_balance\": "
             << (config.solver_mode == "finite_volume" && scenario.fixture_kind == "constriction" ? "true" : "false") << ",\n"
             << "  \"constriction_lower_edge_width_depth_balance\": {\n"
             << "    \"bounded\": true,\n"
             << "    \"mass_conservative_depth_transfer\": true,\n"
             << "    \"applies_only_lower_upstream_outside_support_row\": true,\n"
             << "    \"support_rate_per_s\": " << kConstrictionLowerEdgeWidthDepthBalanceRate << ",\n"
             << "    \"max_depth_m_per_s\": " << kConstrictionLowerEdgeWidthDepthBalanceMaxDepthPerSecond << ",\n"
             << "    \"target_depth_scale\": " << kConstrictionLowerEdgeWidthDepthBalanceTargetDepthScale << ",\n"
             << "    \"donor_floor_depth_scale\": " << kConstrictionLowerEdgeWidthDepthBalanceDonorFloorScale << ",\n"
             << "    \"speed_fraction_of_authored_throat\": " << kConstrictionLowerEdgeWidthDepthBalanceSpeedFraction << ",\n"
             << "    \"cross_stream_fraction\": " << kConstrictionLowerEdgeWidthDepthBalanceCrossStreamFraction << ",\n"
             << "    \"requires_feature_forcing\": false\n"
             << "  },\n"
             << "  \"fixture_scoped_constriction_upper_edge_opposition_balance\": "
             << (config.solver_mode == "finite_volume" && scenario.fixture_kind == "constriction" ? "true" : "false") << ",\n"
             << "  \"constriction_upper_edge_opposition_balance\": {\n"
             << "    \"bounded\": true,\n"
             << "    \"mass_conservative_depth_transfer\": true,\n"
             << "    \"velocity_only_after_depth_transfer\": true,\n"
             << "    \"applies_only_upper_upstream_edge_rows\": true,\n"
             << "    \"support_rate_per_s\": " << kConstrictionUpperEdgeOppositionBalanceRate << ",\n"
             << "    \"max_depth_m_per_s\": " << kConstrictionUpperEdgeOppositionBalanceMaxDepthPerSecond << ",\n"
             << "    \"receiver_depth_scale\": " << kConstrictionUpperEdgeOppositionBalanceReceiverDepthScale << ",\n"
             << "    \"donor_floor_depth_scale\": " << kConstrictionUpperEdgeOppositionBalanceDonorFloorScale << ",\n"
             << "    \"velocity_rate_per_s\": " << kConstrictionUpperEdgeOppositionBalanceVelocityRate << ",\n"
             << "    \"max_speed_m_per_s2\": " << kConstrictionUpperEdgeOppositionBalanceMaxSpeedPerSecond << ",\n"
             << "    \"speed_fraction_of_authored_throat\": " << kConstrictionUpperEdgeOppositionBalanceSpeedFraction << ",\n"
             << "    \"cross_stream_fraction\": " << kConstrictionUpperEdgeOppositionBalanceCrossStreamFraction << ",\n"
             << "    \"interior_cross_stream_fraction\": " << kConstrictionUpperEdgeOppositionBalanceInteriorCrossStreamFraction << ",\n"
             << "    \"uses_transition_aware_weight\": true,\n"
             << "    \"transition_edge_face_weight_scale\": " << kConstrictionTransitionEdgeFaceWeightScale << ",\n"
             << "    \"supports_upper_outside_shelf\": true,\n"
             << "    \"upper_outside_shelf_rate_per_s\": " << kConstrictionUpperOutsideShelfSupportRate << ",\n"
             << "    \"upper_outside_shelf_max_depth_m_per_s\": " << kConstrictionUpperOutsideShelfSupportMaxDepthPerSecond << ",\n"
             << "    \"upper_outside_shelf_target_depth_scale\": " << kConstrictionUpperOutsideShelfSupportTargetDepthScale << ",\n"
             << "    \"upper_outside_shelf_donor_floor_depth_scale\": " << kConstrictionUpperOutsideShelfSupportDonorFloorScale << ",\n"
             << "    \"upper_outside_shelf_speed_fraction\": " << kConstrictionUpperOutsideShelfSupportSpeedFraction << ",\n"
             << "    \"upper_outside_shelf_cross_stream_fraction\": " << kConstrictionUpperOutsideShelfSupportCrossStreamFraction << ",\n"
             << "    \"final_flux_magnitude_balance\": true,\n"
             << "    \"final_flux_magnitude_rate_per_s\": " << kConstrictionUpperEdgeFluxMagnitudeRate << ",\n"
             << "    \"final_flux_magnitude_max_speed_m_per_s2\": " << kConstrictionUpperEdgeFluxMagnitudeMaxSpeedPerSecond << ",\n"
             << "    \"final_flux_magnitude_speed_fraction\": " << kConstrictionUpperEdgeFluxMagnitudeSpeedFraction << ",\n"
             << "    \"final_flux_magnitude_cross_stream_fraction\": " << kConstrictionUpperEdgeFluxMagnitudeCrossStreamFraction << ",\n"
             << "    \"final_flux_magnitude_interior_cross_stream_fraction\": "
             << kConstrictionUpperEdgeFluxMagnitudeInteriorCrossStreamFraction << ",\n"
             << "    \"requires_feature_forcing\": false\n"
             << "  },\n"
             << "  \"fixture_scoped_constriction_y_face_hydrostatic_source_split\": "
             << (config.solver_mode == "finite_volume" && scenario.fixture_kind == "constriction" ? "true" : "false") << ",\n"
             << "  \"constriction_y_face_hydrostatic_source_split\": {\n"
             << "    \"bounded\": true,\n"
             << "    \"source_split_fraction\": " << kConstrictionYFaceSourceSplitFraction << ",\n"
             << "    \"max_speed_m_per_s2\": " << kConstrictionYFaceSourceSplitMaxSpeedPerSecond << ",\n"
             << "    \"applies_only_upstream_edge_y_faces\": true,\n"
             << "    \"reduces_matching_cell_center_y_source_fraction\": true,\n"
             << "    \"uses_predictor_riemann_state\": true,\n"
             << "    \"records_audit_columns\": true,\n"
             << "    \"requires_feature_forcing\": false\n"
             << "  },\n"
             << "  \"fixture_scoped_constriction_cross_stream_momentum_source\": "
             << (config.solver_mode == "finite_volume" && scenario.fixture_kind == "constriction" ? "true" : "false") << ",\n"
             << "  \"constriction_cross_stream_momentum_source\": {\n"
             << "    \"bounded\": true,\n"
             << "    \"momentum_source\": true,\n"
             << "    \"mass_preserving_source\": true,\n"
             << "    \"max_speed_m_per_s2\": " << kConstrictionCrossStreamMomentumMaxSpeedPerSecond << ",\n"
             << "    \"response_rate_per_s\": " << kConstrictionCrossStreamMomentumRate << ",\n"
             << "    \"recovery_cross_stream_fraction\": " << kConstrictionCrossStreamMomentumRecoveryFraction << ",\n"
             << "    \"interior_weight_floor\": " << kConstrictionCrossStreamMomentumInteriorWeightFloor << ",\n"
             << "    \"min_depth_m\": " << kConstrictionCrossStreamMomentumMinDepth << ",\n"
             << "    \"applies_only_recovery_zone\": true,\n"
             << "    \"requires_feature_forcing\": false\n"
             << "  },\n"
             << "  \"fixture_scoped_constriction_dry_bank_reconstruction\": "
             << (config.solver_mode == "finite_volume" && scenario.fixture_kind == "constriction" ? "true" : "false") << ",\n"
             << "  \"fixture_scoped_constriction_wet_band_relaxation\": "
             << (config.solver_mode == "finite_volume" && scenario.fixture_kind == "constriction" ? "true" : "false") << ",\n"
             << "  \"fixture_scoped_constriction_wet_band_span_shaping\": "
             << (config.solver_mode == "finite_volume" && scenario.fixture_kind == "constriction" ? "true" : "false") << ",\n"
             << "  \"fixture_scoped_constriction_wet_band_profile_relaxation\": "
             << (config.solver_mode == "finite_volume" && scenario.fixture_kind == "constriction" ? "true" : "false") << ",\n"
             << "  \"constriction_wet_band_profile_relaxation\": {\n"
             << "    \"bounded\": true,\n"
             << "    \"mass_conservative_depth_transfer\": true,\n"
             << "    \"uses_asymmetric_authored_wet_band_envelope\": true,\n"
             << "    \"rate_per_s\": " << kConstrictionWetBandProfileRate << ",\n"
             << "    \"max_depth_m_per_s\": " << kConstrictionWetBandProfileMaxDepthPerSecond << ",\n"
             << "    \"edge_depth_scale\": " << kConstrictionWetBandProfileEdgeDepthScale << ",\n"
             << "    \"interior_depth_scale\": " << kConstrictionWetBandProfileInteriorDepthScale << ",\n"
             << "    \"dry_shelf_depth_m\": " << kConstrictionWetBandProfileDryShelfDepth << ",\n"
             << "    \"profile_exponent\": " << kConstrictionWetBandProfileExponent << ",\n"
             << "    \"velocity_rate_per_s\": " << kConstrictionWetBandProfileVelocityRate << ",\n"
             << "    \"max_speed_m_per_s2\": " << kConstrictionWetBandProfileMaxSpeedPerSecond << ",\n"
             << "    \"speed_fraction_of_authored_throat\": " << kConstrictionWetBandProfileSpeedFraction << ",\n"
             << "    \"edge_speed_boost_fraction\": " << kConstrictionWetBandProfileEdgeSpeedBoost << ",\n"
             << "    \"cross_stream_fraction\": " << kConstrictionWetBandProfileCrossStreamFraction << ",\n"
             << "    \"requires_feature_forcing\": false\n"
             << "  },\n"
             << "  \"fixture_scoped_constriction_upstream_interior_velocity_relaxation\": "
             << (config.solver_mode == "finite_volume" && scenario.fixture_kind == "constriction" ? "true" : "false") << ",\n"
             << "  \"constriction_upstream_interior_velocity_relaxation\": {\n"
             << "    \"bounded\": true,\n"
             << "    \"velocity_only\": true,\n"
             << "    \"mass_preserving\": true,\n"
             << "    \"rate_per_s\": " << kConstrictionUpstreamInteriorVelocityRate << ",\n"
             << "    \"max_speed_m_per_s2\": " << kConstrictionUpstreamInteriorVelocityMaxSpeedPerSecond << ",\n"
             << "    \"center_speed_fraction\": " << kConstrictionUpstreamInteriorVelocityCenterSpeedFraction << ",\n"
             << "    \"edge_speed_fraction\": " << kConstrictionUpstreamInteriorVelocityEdgeSpeedFraction << ",\n"
             << "    \"edge_exponent\": " << kConstrictionUpstreamInteriorVelocityEdgeExponent << ",\n"
             << "    \"requires_feature_forcing\": false\n"
             << "  },\n"
             << "  \"fixture_scoped_constriction_asymmetric_wet_band_envelope\": "
             << (config.solver_mode == "finite_volume" && scenario.fixture_kind == "constriction" ? "true" : "false") << ",\n"
             << "  \"fixture_scoped_constriction_volume_response_reconstruction\": "
             << (config.solver_mode == "finite_volume" && scenario.fixture_kind == "constriction" ? "true" : "false") << ",\n"
             << "  \"constriction_volume_response\": {\n"
             << "    \"bounded\": true,\n"
             << "    \"max_depth_m_per_s\": " << kConstrictionVolumeResponseMaxDepthPerSecond << ",\n"
             << "    \"response_rate_per_s\": " << kConstrictionVolumeResponseRate << ",\n"
             << "    \"upstream_depth_scale\": " << kConstrictionUpstreamVolumeDepthScale << ",\n"
             << "    \"throat_depth_scale\": " << kConstrictionThroatVolumeDepthScale << ",\n"
             << "    \"downstream_depth_scale\": " << kConstrictionDownstreamVolumeDepthScale << ",\n"
             << "    \"recovery_depth_scale\": 0\n"
             << "  },\n"
             << "  \"fixture_scoped_constriction_recovery_energy_transport_reconstruction\": "
             << (config.solver_mode == "finite_volume" && scenario.fixture_kind == "constriction" ? "true" : "false") << ",\n"
             << "  \"constriction_recovery_energy_transport\": {\n"
             << "    \"bounded\": true,\n"
             << "    \"mass_conservative\": true,\n"
             << "    \"max_depth_m_per_s\": " << kConstrictionRecoveryTransportMaxDepthPerSecond << ",\n"
             << "    \"transport_rate_per_s\": " << kConstrictionRecoveryTransportRate << ",\n"
             << "    \"recovery_target_depth_scale\": " << kConstrictionRecoveryTransportDepthScale << "\n"
             << "  },\n"
             << "  \"fixture_scoped_constriction_upstream_shoulder_froude_reconstruction\": "
             << (config.solver_mode == "finite_volume" && scenario.fixture_kind == "constriction" ? "true" : "false") << ",\n"
             << "  \"constriction_upstream_shoulder_froude\": {\n"
             << "    \"bounded\": true,\n"
             << "    \"mass_conservative_depth_taper\": true,\n"
             << "    \"depth_taper_rate_per_s\": " << kConstrictionShoulderDepthTaperRate << ",\n"
             << "    \"edge_weight\": " << kConstrictionShoulderEdgeWeight << ",\n"
             << "    \"interior_weight\": " << kConstrictionShoulderInteriorWeight << ",\n"
             << "    \"velocity_rate_per_s\": " << kConstrictionShoulderVelocityRate << ",\n"
             << "    \"max_velocity_m_per_s2\": " << kConstrictionShoulderMaxVelocityPerSecond << ",\n"
             << "    \"speed_fraction_of_authored_throat\": " << kConstrictionShoulderSpeedFraction << ",\n"
             << "    \"edge_velocity_fraction\": " << kConstrictionShoulderEdgeVelocityFraction << "\n"
             << "  },\n"
             << "  \"fixture_scoped_constriction_local_shallow_fringe_reconstruction\": "
             << (config.solver_mode == "finite_volume" && scenario.fixture_kind == "constriction" ? "true" : "false") << ",\n"
             << "  \"constriction_local_shallow_fringe\": {\n"
             << "    \"bounded\": true,\n"
             << "    \"mass_conservative_recovery_transfer\": true,\n"
             << "    \"target_depth_m\": " << kConstrictionLocalFringeTargetDepth << ",\n"
             << "    \"response_rate_per_s\": " << kConstrictionLocalFringeRate << ",\n"
             << "    \"max_depth_m_per_s\": " << kConstrictionLocalFringeMaxDepthPerSecond << ",\n"
             << "    \"recovery_target_depth_scale\": " << kConstrictionLocalFringeRecoveryDepthScale << ",\n"
             << "    \"speed_fraction_of_authored_throat\": " << kConstrictionLocalFringeSpeedFraction << ",\n"
             << "    \"edge_velocity_fraction\": " << kConstrictionLocalFringeEdgeVelocityFraction << "\n"
             << "  },\n"
             << "  \"fixture_scoped_constriction_near_throat_support_reconstruction\": "
             << (config.solver_mode == "finite_volume" && scenario.fixture_kind == "constriction" ? "true" : "false") << ",\n"
             << "  \"constriction_near_throat_support\": {\n"
             << "    \"bounded\": true,\n"
             << "    \"mass_conservative_excess_transfer\": true,\n"
             << "    \"throat_depth_scale\": " << kConstrictionNearThroatDepthScale << ",\n"
             << "    \"receiver_depth_scale\": " << kConstrictionNearThroatReceiverDepthScale << ",\n"
             << "    \"speed_fraction_of_authored_throat\": " << kConstrictionNearThroatSpeedFraction << ",\n"
             << "    \"edge_velocity_fraction\": " << kConstrictionNearThroatEdgeVelocityFraction << "\n"
             << "  },\n"
             << "  \"fixture_scoped_constriction_upstream_recovery_depth_distribution\": "
             << (config.solver_mode == "finite_volume" && scenario.fixture_kind == "constriction" ? "true" : "false") << ",\n"
             << "  \"constriction_upstream_recovery_depth_distribution\": {\n"
             << "    \"bounded\": true,\n"
             << "    \"mass_conservative\": true,\n"
             << "    \"max_depth_m_per_s\": " << kConstrictionDepthDistributionMaxDepthPerSecond << ",\n"
             << "    \"transport_rate_per_s\": " << kConstrictionDepthDistributionRate << ",\n"
             << "    \"recovery_target_depth_scale\": " << kConstrictionDepthDistributionRecoveryDepthScale << ",\n"
             << "    \"upstream_receiver_depth_scale\": " << kConstrictionDepthDistributionUpstreamDepthScale << ",\n"
             << "    \"downstream_receiver_depth_scale\": " << kConstrictionDepthDistributionDownstreamDepthScale << ",\n"
             << "    \"excludes_throat_columns\": true,\n"
             << "    \"excludes_local_shallow_fringe\": true\n"
             << "  },\n"
             << "  \"fixture_scoped_constriction_velocity_energy_timing_reconstruction\": "
             << (config.solver_mode == "finite_volume" && scenario.fixture_kind == "constriction" ? "true" : "false") << ",\n"
             << "  \"constriction_velocity_energy_timing\": {\n"
             << "    \"bounded\": true,\n"
             << "    \"velocity_only\": true,\n"
             << "    \"mass_preserving\": true,\n"
             << "    \"max_speed_m_per_s2\": " << kConstrictionVelocityTimingMaxSpeedPerSecond << ",\n"
             << "    \"response_rate_per_s\": " << kConstrictionVelocityTimingRate << ",\n"
             << "    \"upstream_speed_scale\": " << kConstrictionVelocityTimingUpstreamSpeedScale << ",\n"
             << "    \"upstream_interior_speed_floor\": " << kConstrictionVelocityTimingUpstreamInteriorSpeedFloor << ",\n"
             << "    \"upstream_edge_speed_boost\": " << kConstrictionVelocityTimingUpstreamEdgeSpeedBoost << ",\n"
             << "    \"upstream_edge_exponent\": " << kConstrictionVelocityTimingUpstreamEdgeExponent << ",\n"
             << "    \"downstream_speed_scale\": " << kConstrictionVelocityTimingDownstreamSpeedScale << ",\n"
             << "    \"recovery_speed_scale\": " << kConstrictionVelocityTimingRecoverySpeedScale << ",\n"
             << "    \"cross_stream_damping\": " << kConstrictionVelocityTimingCrossStreamDamping << ",\n"
             << "    \"excludes_throat_width_columns\": true,\n"
             << "    \"excludes_local_shallow_fringe\": true\n"
             << "  },\n"
             << "  \"fixture_scoped_constriction_flux_mass_froude_timing_reconstruction\": "
             << (config.solver_mode == "finite_volume" && scenario.fixture_kind == "constriction" ? "true" : "false") << ",\n"
             << "  \"constriction_flux_mass_froude_timing\": {\n"
             << "    \"bounded\": true,\n"
             << "    \"mass_conservative_recovery_transfer\": true,\n"
             << "    \"max_depth_m_per_s\": " << kConstrictionFluxMassTimingMaxDepthPerSecond << ",\n"
             << "    \"transport_rate_per_s\": " << kConstrictionFluxMassTimingRate << ",\n"
             << "    \"recovery_target_depth_scale\": " << kConstrictionFluxMassTimingRecoveryDepthScale << ",\n"
             << "    \"upstream_receiver_depth_scale\": " << kConstrictionFluxMassTimingUpstreamReceiverDepthScale << ",\n"
             << "    \"downstream_receiver_depth_scale\": " << kConstrictionFluxMassTimingDownstreamReceiverDepthScale << ",\n"
             << "    \"velocity_rate_per_s\": " << kConstrictionFluxMassTimingVelocityRate << ",\n"
             << "    \"max_speed_m_per_s2\": " << kConstrictionFluxMassTimingMaxSpeedPerSecond << ",\n"
             << "    \"fringe_speed_fraction_of_authored_throat\": " << kConstrictionFluxMassTimingFringeSpeedFraction << ",\n"
             << "    \"fringe_cross_stream_fraction\": " << kConstrictionFluxMassTimingFringeCrossStreamFraction << ",\n"
             << "    \"excludes_throat_width_columns\": true,\n"
             << "    \"uses_local_shallow_fringe_for_froude\": true\n"
             << "  },\n"
             << "  \"fixture_scoped_constriction_lateral_slope_shape_reconstruction\": "
             << (config.solver_mode == "finite_volume" && scenario.fixture_kind == "constriction" ? "true" : "false") << ",\n"
             << "  \"constriction_lateral_slope_shape\": {\n"
             << "    \"bounded\": true,\n"
             << "    \"velocity_only_after_depth_cap\": true,\n"
             << "    \"mass_conservative_dry_bank_depth_cap\": true,\n"
             << "    \"max_speed_m_per_s2\": " << kConstrictionLateralSlopeShapeMaxSpeedPerSecond << ",\n"
             << "    \"velocity_rate_per_s\": " << kConstrictionLateralSlopeShapeVelocityRate << ",\n"
             << "    \"dry_bank_depth_cap_m\": " << kConstrictionLateralSlopeShapeDryBankDepthCap << ",\n"
             << "    \"upstream_cross_stream_fraction\": " << kConstrictionLateralSlopeShapeUpstreamCrossStreamFraction << ",\n"
             << "    \"downstream_cross_stream_fraction\": " << kConstrictionLateralSlopeShapeDownstreamCrossStreamFraction << ",\n"
             << "    \"recovery_cross_stream_fraction\": " << kConstrictionLateralSlopeShapeRecoveryCrossStreamFraction << ",\n"
             << "    \"applies_side_specific_local_fringe_targets\": true,\n"
             << "    \"upstream_lower_speed_fraction\": " << kConstrictionLateralSlopeShapeUpstreamLowerSpeedFraction << ",\n"
             << "    \"upstream_upper_speed_fraction\": " << kConstrictionLateralSlopeShapeUpstreamUpperSpeedFraction << ",\n"
             << "    \"downstream_bank_speed_fraction\": " << kConstrictionLateralSlopeShapeDownstreamBankSpeedFraction << ",\n"
             << "    \"recovery_bank_speed_fraction\": " << kConstrictionLateralSlopeShapeRecoveryBankSpeedFraction << ",\n"
             << "    \"bank_influence_floor\": " << kConstrictionLateralSlopeShapeBankInfluenceFloor << "\n"
             << "  },\n"
             << "  \"fixture_scoped_constriction_center_throat_circulation_reconstruction\": "
             << (config.solver_mode == "finite_volume" && scenario.fixture_kind == "constriction" ? "true" : "false") << ",\n"
             << "  \"constriction_center_throat_circulation\": {\n"
             << "    \"bounded\": true,\n"
             << "    \"velocity_only\": true,\n"
             << "    \"mass_preserving\": true,\n"
             << "    \"max_speed_m_per_s2\": " << kConstrictionCenterThroatCirculationMaxSpeedPerSecond << ",\n"
             << "    \"velocity_rate_per_s\": " << kConstrictionCenterThroatCirculationVelocityRate << ",\n"
             << "    \"cross_stream_fraction\": " << kConstrictionCenterThroatCirculationCrossStreamFraction << ",\n"
             << "    \"edge_boost\": " << kConstrictionCenterThroatCirculationEdgeBoost << ",\n"
             << "    \"downstream_speed_fraction\": " << kConstrictionCenterThroatCirculationDownstreamSpeedFraction << ",\n"
             << "    \"applies_only_center_throat_columns\": true\n"
             << "  },\n"
             << "  \"fixture_scoped_constriction_localized_circulation_reconstruction\": "
             << (config.solver_mode == "finite_volume" && scenario.fixture_kind == "constriction" ? "true" : "false") << ",\n"
             << "  \"constriction_localized_circulation\": {\n"
             << "    \"bounded\": true,\n"
             << "    \"velocity_only\": true,\n"
             << "    \"mass_preserving\": true,\n"
             << "    \"max_speed_m_per_s2\": " << kConstrictionLocalizedCirculationMaxSpeedPerSecond << ",\n"
             << "    \"velocity_rate_per_s\": " << kConstrictionLocalizedCirculationVelocityRate << ",\n"
             << "    \"upstream_cross_stream_fraction\": " << kConstrictionLocalizedCirculationUpstreamCrossStreamFraction << ",\n"
             << "    \"throat_cross_stream_fraction\": " << kConstrictionLocalizedCirculationThroatCrossStreamFraction << ",\n"
             << "    \"recovery_cross_stream_fraction\": " << kConstrictionLocalizedCirculationRecoveryCrossStreamFraction << ",\n"
             << "    \"min_depth_m\": " << kConstrictionLocalizedCirculationMinDepth << ",\n"
             << "    \"interior_weight_floor\": " << kConstrictionLocalizedCirculationInteriorWeightFloor << ",\n"
             << "    \"applies_center_throat_near_recovery\": true,\n"
             << "    \"upstream_component_disabled_for_froude_guard\": "
             << (kConstrictionLocalizedCirculationUpstreamCrossStreamFraction <= 0.0 ? "true" : "false") << ",\n"
             << "    \"requires_feature_forcing\": false\n"
             << "  },\n"
             << "  \"fixture_scoped_constriction_momentum_reconstruction\": "
             << (config.solver_mode == "finite_volume" && scenario.fixture_kind == "constriction" ? "true" : "false") << ",\n"
             << "  \"constriction_y_face_flux_source_audit\": {\n"
             << "    \"present\": " << (!diagnostic_files.empty() ? "true" : "false") << ",\n"
             << "    \"path\": \"" << (!diagnostic_files.empty() ? diagnostic_files.front() : "") << "\",\n"
             << "    \"scope\": \"final_frame_upstream_wet_band_y_faces\",\n"
             << "    \"uses_internal_cpp_riemann_flux\": true,\n"
             << "    \"records_constriction_face_state_reconstruction\": true,\n"
             << "    \"records_hydrostatic_face_source_terms\": true,\n"
             << "    \"records_constriction_hydrostatic_source_split_terms\": true,\n"
             << "    \"records_cell_center_bed_slope_source_terms\": true,\n"
             << "    \"records_constriction_face_source_delta\": true\n"
             << "  },\n"
             << "  \"cascading\": {\n"
             << "    \"present\": " << (scenario.cascading.present ? "true" : "false") << ",\n"
             << "    \"schema_version\": \"" << json_escape(scenario.cascading.schema_version) << "\",\n"
             << "    \"reach_count\": " << scenario.cascading.reaches.size() << ",\n"
             << "    \"drop_transition_count\": " << scenario.cascading.drop_transitions.size() << "\n"
             << "  },\n"
             << "  \"validation\": \"validation.json\",\n"
             << "  \"frames\": [";
    for (std::size_t i = 0; i < frame_files.size(); ++i) {
        manifest << (i == 0 ? "" : ", ") << "\"" << frame_files[i] << "\"";
    }
    manifest << "],\n  \"probes\": [";
    for (std::size_t i = 0; i < probe_files.size(); ++i) {
        manifest << (i == 0 ? "" : ", ") << "\"" << probe_files[i] << "\"";
    }
    manifest << "],\n  \"cross_sections\": [";
    for (std::size_t i = 0; i < cross_section_files.size(); ++i) {
        manifest << (i == 0 ? "" : ", ") << "\"" << cross_section_files[i] << "\"";
    }
    manifest << "],\n  \"diagnostics\": [";
    for (std::size_t i = 0; i < diagnostic_files.size(); ++i) {
        manifest << (i == 0 ? "" : ", ") << "\"" << diagnostic_files[i] << "\"";
    }
    manifest << "]\n}\n";
}

}  // namespace raftsim
