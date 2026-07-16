#include "solver_internal.hpp"

namespace raftsim::solver_detail {

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

}  // namespace raftsim::solver_detail
