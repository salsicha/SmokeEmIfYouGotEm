# ruff: noqa: F401

import json
import hashlib
from pathlib import Path

import pytest
from PIL import Image, ImageStat

from raftsim.editor_source_layout import EditorImplementationSourceSet, read_raftsim_editor_source
from raftsim.photoreal_capture_quality import (
    CAPTURE_QUALITY_REVIEW_RELATIVE_PATH,
    FLOW_VARIANT_CAPTURE_QUALITY_REVIEW_RELATIVE_PATH,
    FLOW_VARIANT_ENVIRONMENT_PERFORMANCE_REVIEW_RELATIVE_PATH,
    FLOW_VARIANT_CAPTURE_PLAN_RELATIVE_PATH,
    FLOW_VARIANT_HUMAN_LIFELIKE_REVIEW_HANDOFF_RELATIVE_PATH,
    HUMAN_LIFELIKE_REVIEW_HANDOFF_RELATIVE_PATH,
    HUMAN_LIFELIKE_REVIEW_PACKET_RELATIVE_PATH,
    HUMAN_LIFELIKE_REVIEW_RESULTS_TEMPLATE_RELATIVE_PATH,
    PHOTOREAL_ENVIRONMENT_PERFORMANCE_REVIEW_RELATIVE_PATH,
    build_capture_quality_review,
    build_flow_variant_capture_quality_review,
    build_flow_variant_environment_performance_review,
    build_flow_variant_human_lifelike_review_handoff,
    build_photoreal_flow_variant_capture_plan,
    build_human_lifelike_review_handoff,
    build_human_lifelike_review_packet_markdown,
    build_human_lifelike_review_results_template,
    build_photoreal_environment_performance_review,
)
from raftsim.procedural_material_swatches import (
    SWATCH_MANIFEST_RELATIVE_PATH,
    TEXTURE_ATLAS_MANIFEST_RELATIVE_PATH,
)
from raftsim.production_detail_textures import (
    MANIFEST_RELATIVE_PATH as PRODUCTION_DETAIL_TEXTURE_MANIFEST_RELATIVE_PATH,
    TEXTURE_ASSET_ROOT_RELATIVE_PATH as PRODUCTION_DETAIL_TEXTURE_ASSET_ROOT_RELATIVE_PATH,
)
from raftsim.futaleufu_native_canopy_assets import (
    MANIFEST_RELATIVE_PATH as FUTALEUFU_NATIVE_CANOPY_TEXTURE_MANIFEST_RELATIVE_PATH,
)
from raftsim.futaleufu_cordillera_cypress_assets import (
    TEXTURE_MANIFEST_RELATIVE_PATH as FUTALEUFU_CORDILLERA_CYPRESS_TEXTURE_MANIFEST_RELATIVE_PATH,
)
from raftsim.futaleufu_cordillera_cypress_review import (
    REPORT_RELATIVE_PATH as FUTALEUFU_CORDILLERA_CYPRESS_REPORT_RELATIVE_PATH,
    REVIEW_RELATIVE_PATH as FUTALEUFU_CORDILLERA_CYPRESS_REVIEW_RELATIVE_PATH,
    V2_REPORT_RELATIVE_PATH as FUTALEUFU_CORDILLERA_CYPRESS_V2_REPORT_RELATIVE_PATH,
    V2_REVIEW_RELATIVE_PATH as FUTALEUFU_CORDILLERA_CYPRESS_V2_REVIEW_RELATIVE_PATH,
    V3_REPORT_RELATIVE_PATH as FUTALEUFU_CORDILLERA_CYPRESS_V3_REPORT_RELATIVE_PATH,
    V3_REVIEW_RELATIVE_PATH as FUTALEUFU_CORDILLERA_CYPRESS_V3_REVIEW_RELATIVE_PATH,
    V4_REPORT_RELATIVE_PATH as FUTALEUFU_CORDILLERA_CYPRESS_V4_REPORT_RELATIVE_PATH,
    V4_REVIEW_RELATIVE_PATH as FUTALEUFU_CORDILLERA_CYPRESS_V4_REVIEW_RELATIVE_PATH,
    V5_REPORT_RELATIVE_PATH as FUTALEUFU_CORDILLERA_CYPRESS_V5_REPORT_RELATIVE_PATH,
    V5_REVIEW_RELATIVE_PATH as FUTALEUFU_CORDILLERA_CYPRESS_V5_REVIEW_RELATIVE_PATH,
    V6_REPORT_RELATIVE_PATH as FUTALEUFU_CORDILLERA_CYPRESS_V6_REPORT_RELATIVE_PATH,
    V6_REVIEW_RELATIVE_PATH as FUTALEUFU_CORDILLERA_CYPRESS_V6_REVIEW_RELATIVE_PATH,
    V7_REPORT_RELATIVE_PATH as FUTALEUFU_CORDILLERA_CYPRESS_V7_REPORT_RELATIVE_PATH,
    V7_REVIEW_RELATIVE_PATH as FUTALEUFU_CORDILLERA_CYPRESS_V7_REVIEW_RELATIVE_PATH,
    V8_REPORT_RELATIVE_PATH as FUTALEUFU_CORDILLERA_CYPRESS_V8_REPORT_RELATIVE_PATH,
    V8_REVIEW_RELATIVE_PATH as FUTALEUFU_CORDILLERA_CYPRESS_V8_REVIEW_RELATIVE_PATH,
    V9_REPORT_RELATIVE_PATH as FUTALEUFU_CORDILLERA_CYPRESS_V9_REPORT_RELATIVE_PATH,
    V9_REVIEW_RELATIVE_PATH as FUTALEUFU_CORDILLERA_CYPRESS_V9_REVIEW_RELATIVE_PATH,
    V10_REPORT_RELATIVE_PATH as FUTALEUFU_CORDILLERA_CYPRESS_V10_REPORT_RELATIVE_PATH,
    V10_REVIEW_RELATIVE_PATH as FUTALEUFU_CORDILLERA_CYPRESS_V10_REVIEW_RELATIVE_PATH,
    V11_REPORT_RELATIVE_PATH as FUTALEUFU_CORDILLERA_CYPRESS_V11_REPORT_RELATIVE_PATH,
    V11_REVIEW_RELATIVE_PATH as FUTALEUFU_CORDILLERA_CYPRESS_V11_REVIEW_RELATIVE_PATH,
    V12_REPORT_RELATIVE_PATH as FUTALEUFU_CORDILLERA_CYPRESS_V12_REPORT_RELATIVE_PATH,
    V12_REVIEW_RELATIVE_PATH as FUTALEUFU_CORDILLERA_CYPRESS_V12_REVIEW_RELATIVE_PATH,
    V13_REPORT_RELATIVE_PATH as FUTALEUFU_CORDILLERA_CYPRESS_V13_REPORT_RELATIVE_PATH,
    V13_REVIEW_RELATIVE_PATH as FUTALEUFU_CORDILLERA_CYPRESS_V13_REVIEW_RELATIVE_PATH,
    V14_REPORT_RELATIVE_PATH as FUTALEUFU_CORDILLERA_CYPRESS_V14_REPORT_RELATIVE_PATH,
    V14_REVIEW_RELATIVE_PATH as FUTALEUFU_CORDILLERA_CYPRESS_V14_REVIEW_RELATIVE_PATH,
    V15_REPORT_RELATIVE_PATH as FUTALEUFU_CORDILLERA_CYPRESS_V15_REPORT_RELATIVE_PATH,
    V15_REVIEW_RELATIVE_PATH as FUTALEUFU_CORDILLERA_CYPRESS_V15_REVIEW_RELATIVE_PATH,
)
from raftsim.zambezi_batoka_basalt_review import (
    V1_REPORT_RELATIVE_PATH as ZAMBEZI_BATOKA_BASALT_V1_REPORT_RELATIVE_PATH,
    V1_REVIEW_RELATIVE_PATH as ZAMBEZI_BATOKA_BASALT_V1_REVIEW_RELATIVE_PATH,
    V2_REPORT_RELATIVE_PATH as ZAMBEZI_BATOKA_BASALT_V2_REPORT_RELATIVE_PATH,
    V2_REVIEW_RELATIVE_PATH as ZAMBEZI_BATOKA_BASALT_V2_REVIEW_RELATIVE_PATH,
    V3_REPORT_RELATIVE_PATH as ZAMBEZI_BATOKA_BASALT_V3_REPORT_RELATIVE_PATH,
    V3_REVIEW_RELATIVE_PATH as ZAMBEZI_BATOKA_BASALT_V3_REVIEW_RELATIVE_PATH,
    V4_REPORT_RELATIVE_PATH as ZAMBEZI_BATOKA_BASALT_V4_REPORT_RELATIVE_PATH,
    V4_REVIEW_RELATIVE_PATH as ZAMBEZI_BATOKA_BASALT_V4_REVIEW_RELATIVE_PATH,
    V5_REPORT_RELATIVE_PATH as ZAMBEZI_BATOKA_BASALT_V5_REPORT_RELATIVE_PATH,
    V5_REVIEW_RELATIVE_PATH as ZAMBEZI_BATOKA_BASALT_V5_REVIEW_RELATIVE_PATH,
    V6_REPORT_RELATIVE_PATH as ZAMBEZI_BATOKA_BASALT_V6_REPORT_RELATIVE_PATH,
    V6_REVIEW_RELATIVE_PATH as ZAMBEZI_BATOKA_BASALT_V6_REVIEW_RELATIVE_PATH,
    V7_REPORT_RELATIVE_PATH as ZAMBEZI_BATOKA_BASALT_V7_REPORT_RELATIVE_PATH,
    V7_REVIEW_RELATIVE_PATH as ZAMBEZI_BATOKA_BASALT_V7_REVIEW_RELATIVE_PATH,
    V8_REPORT_RELATIVE_PATH as ZAMBEZI_BATOKA_BASALT_V8_REPORT_RELATIVE_PATH,
    V8_REVIEW_RELATIVE_PATH as ZAMBEZI_BATOKA_BASALT_V8_REVIEW_RELATIVE_PATH,
    V9_REPORT_RELATIVE_PATH as ZAMBEZI_BATOKA_BASALT_V9_REPORT_RELATIVE_PATH,
    V9_REVIEW_RELATIVE_PATH as ZAMBEZI_BATOKA_BASALT_V9_REVIEW_RELATIVE_PATH,
    V10_REPORT_RELATIVE_PATH as ZAMBEZI_BATOKA_BASALT_V10_REPORT_RELATIVE_PATH,
    V10_REVIEW_RELATIVE_PATH as ZAMBEZI_BATOKA_BASALT_V10_REVIEW_RELATIVE_PATH,
    C1_CORRIDOR_REPORT_RELATIVE_PATH as ZAMBEZI_BATOKA_BASALT_C1_CORRIDOR_REPORT_RELATIVE_PATH,
    C1_CORRIDOR_REVIEW_RELATIVE_PATH as ZAMBEZI_BATOKA_BASALT_C1_CORRIDOR_REVIEW_RELATIVE_PATH,
    C2_CORRIDOR_REPORT_RELATIVE_PATH as ZAMBEZI_BATOKA_BASALT_C2_CORRIDOR_REPORT_RELATIVE_PATH,
    C2_CORRIDOR_REVIEW_RELATIVE_PATH as ZAMBEZI_BATOKA_BASALT_C2_CORRIDOR_REVIEW_RELATIVE_PATH,
    C3_TERRAIN_REPORT_RELATIVE_PATH as ZAMBEZI_BATOKA_C3_TERRAIN_REPORT_RELATIVE_PATH,
    C3_TERRAIN_REVIEW_RELATIVE_PATH as ZAMBEZI_BATOKA_C3_TERRAIN_REVIEW_RELATIVE_PATH,
    C4_WORLD_ALIGNED_REPORT_RELATIVE_PATH as ZAMBEZI_BATOKA_C4_WORLD_ALIGNED_REPORT_RELATIVE_PATH,
    C4_WORLD_ALIGNED_REVIEW_RELATIVE_PATH as ZAMBEZI_BATOKA_C4_WORLD_ALIGNED_REVIEW_RELATIVE_PATH,
    C5_VISUAL_MORPHOLOGY_REPORT_RELATIVE_PATH as ZAMBEZI_BATOKA_C5_VISUAL_MORPHOLOGY_REPORT_RELATIVE_PATH,
    C5_VISUAL_MORPHOLOGY_REVIEW_RELATIVE_PATH as ZAMBEZI_BATOKA_C5_VISUAL_MORPHOLOGY_REVIEW_RELATIVE_PATH,
    build_zambezi_batoka_basalt_v1_visual_review,
    build_zambezi_batoka_basalt_v2_visual_review,
    build_zambezi_batoka_basalt_v3_visual_review,
    build_zambezi_batoka_basalt_v4_visual_review,
    build_zambezi_batoka_basalt_v5_visual_review,
    build_zambezi_batoka_basalt_v6_visual_review,
    build_zambezi_batoka_basalt_v7_visual_review,
    build_zambezi_batoka_basalt_v8_visual_review,
    build_zambezi_batoka_basalt_v9_visual_review,
    build_zambezi_batoka_basalt_v10_visual_review,
    build_zambezi_batoka_basalt_c1_corridor_visual_review,
    build_zambezi_batoka_basalt_c2_corridor_visual_review,
    build_zambezi_batoka_v11_terrain_integrated_visual_review,
    build_zambezi_batoka_v12_world_aligned_visual_review,
    build_zambezi_batoka_v13_visual_morphology_review,
)
from raftsim.source_conditioned_material_maps import (
    SOURCE_CONDITIONED_MATERIAL_MAP_MANIFEST_RELATIVE_PATH,
    SOURCE_CONDITIONED_MATERIAL_TEXTURE_ASSET_ROOT_RELATIVE_PATH,
    SOURCE_CONDITIONED_MATERIAL_TEXTURE_ASSET_STATUS,
)
from raftsim.solver_visualization_fields import (
    MANIFEST_RELATIVE_PATH as SOLVER_VISUALIZATION_FIELD_MANIFEST_RELATIVE_PATH,
    NORMAL_TEXTURE_RELATIVE_PATH as SOLVER_VISUALIZATION_NORMAL_RELATIVE_PATH,
    PACKED_TEXTURE_RELATIVE_PATH as SOLVER_VISUALIZATION_PACKED_RELATIVE_PATH,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ASSET_PLAN_PATH = (
    REPO_ROOT
    / "unreal/Content/RaftSim/Rendering/first_party_procedural_environment_assets.json"
)
MATERIAL_RECIPE_PATH = (
    REPO_ROOT
    / "unreal/Content/RaftSim/Rendering/first_party_procedural_material_recipes.json"
)
MATERIAL_SWATCH_MANIFEST_PATH = REPO_ROOT / SWATCH_MANIFEST_RELATIVE_PATH
MATERIAL_TEXTURE_ATLAS_MANIFEST_PATH = REPO_ROOT / TEXTURE_ATLAS_MANIFEST_RELATIVE_PATH
FLOW_VISUAL_BAND_MANIFEST_PATH = (
    REPO_ROOT / "unreal/Content/RaftSim/Rendering/river_flow_visual_bands.json"
)
SOURCE_CONDITIONED_MATERIAL_MAP_MANIFEST_PATH = (
    REPO_ROOT / SOURCE_CONDITIONED_MATERIAL_MAP_MANIFEST_RELATIVE_PATH
)
MATERIAL_INSTANCE_CANDIDATE_MANIFEST_PATH = (
    REPO_ROOT
    / "unreal/Content/RaftSim/Rendering/first_party_material_instance_candidates.json"
)
PRODUCTION_DETAIL_TEXTURE_MANIFEST_PATH = (
    REPO_ROOT / PRODUCTION_DETAIL_TEXTURE_MANIFEST_RELATIVE_PATH
)
SOURCE_PLAN_PATH = (
    REPO_ROOT
    / "unreal/Content/RaftSim/Rendering/photoreal_river_environment_sources.json"
)
GAP_REGISTER_PATH = (
    REPO_ROOT / "physics/data/real_world/production_environment_gap_register.json"
)
GEOSPATIAL_ATTACHMENT_LEDGER_PATH = (
    REPO_ROOT / "physics/data/real_world/production_geospatial_attachment_ledger.json"
)
GEOSPATIAL_ATTACHMENT_AUDIT_PATH = (
    REPO_ROOT
    / "physics/data/real_world/production_geospatial_source_attachment_audit.json"
)
ADDITIONAL_SOURCE_LEADS_REVIEW_PATH = (
    REPO_ROOT / "physics/data/real_world/production_additional_source_leads_review.json"
)
PRODUCTION_FLOW_VARIANT_INTAKE_PATH = (
    REPO_ROOT / "physics/data/real_world/production_flow_variant_intake.json"
)
PRODUCTION_VISUAL_SOURCE_ACQUISITION_QUEUE_PATH = (
    REPO_ROOT
    / "physics/data/real_world/production_visual_source_acquisition_queue.json"
)
PRODUCTION_VISUAL_SOURCE_ITEM_INTAKE_PATH = (
    REPO_ROOT / "physics/data/real_world/production_visual_source_item_intake.json"
)
ART_SOURCE_RESEARCH_PATH = (
    REPO_ROOT / "unreal/Content/RaftSim/Rendering/art_asset_source_research.json"
)
CAPTURE_MANIFEST_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/environment_capture_manifest.json"
)
CAPTURE_QUALITY_REVIEW_PATH = REPO_ROOT / CAPTURE_QUALITY_REVIEW_RELATIVE_PATH
FLOW_VARIANT_CAPTURE_PLAN_PATH = REPO_ROOT / FLOW_VARIANT_CAPTURE_PLAN_RELATIVE_PATH
FLOW_VARIANT_CAPTURE_MANIFEST_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/flow_variant_capture_manifest.json"
)
FLOW_VARIANT_CAPTURE_QUALITY_REVIEW_PATH = (
    REPO_ROOT / FLOW_VARIANT_CAPTURE_QUALITY_REVIEW_RELATIVE_PATH
)
FLOW_VARIANT_HUMAN_LIFELIKE_REVIEW_HANDOFF_PATH = (
    REPO_ROOT / FLOW_VARIANT_HUMAN_LIFELIKE_REVIEW_HANDOFF_RELATIVE_PATH
)
FLOW_VARIANT_ENVIRONMENT_PERFORMANCE_REVIEW_PATH = (
    REPO_ROOT / FLOW_VARIANT_ENVIRONMENT_PERFORMANCE_REVIEW_RELATIVE_PATH
)
HUMAN_LIFELIKE_REVIEW_HANDOFF_PATH = (
    REPO_ROOT / HUMAN_LIFELIKE_REVIEW_HANDOFF_RELATIVE_PATH
)
HUMAN_LIFELIKE_REVIEW_PACKET_PATH = (
    REPO_ROOT / HUMAN_LIFELIKE_REVIEW_PACKET_RELATIVE_PATH
)
HUMAN_LIFELIKE_REVIEW_RESULTS_TEMPLATE_PATH = (
    REPO_ROOT / HUMAN_LIFELIKE_REVIEW_RESULTS_TEMPLATE_RELATIVE_PATH
)
PHOTOREAL_ENVIRONMENT_PERFORMANCE_REVIEW_PATH = (
    REPO_ROOT / PHOTOREAL_ENVIRONMENT_PERFORMANCE_REVIEW_RELATIVE_PATH
)
AUTOMATION_RUN_REPORT_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/unreal_environment_automation_run_2026-07-06_material_recipe_gate.json"
)
EDITOR_MODULE_PATH = EditorImplementationSourceSet(REPO_ROOT)
EDITOR_MODULE_HEADER_PATH = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Public/RaftSimEditorModule.h"
)
EDITOR_BUILD_RULES_PATH = (
    REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/RaftSimEditor.Build.cs"
)
RAFTSIM_PLUGIN_PATH = REPO_ROOT / "unreal/Plugins/RaftSim/RaftSim.uplugin"
UNREAL_PROJECT_PATH = REPO_ROOT / "unreal/SmokeEmIfYouGotEm.uproject"
UNREAL_ENGINE_CONFIG_PATH = REPO_ROOT / "unreal/Config/DefaultEngine.ini"
LANDSCAPE_CANDIDATE_MANIFEST_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/landscape_candidate_manifest.json"
)
REVIEWED_BIOME_IMPORT_SCRIPT_PATH = (
    REPO_ROOT / "unreal/Scripts/import_reviewed_biome_asset.py"
)
REVIEWED_FIR_SOURCE_MANIFEST_PATH = (
    REPO_ROOT
    / "unreal/Content/RaftSim/Environment/ExternalReview/PolyHaven/FirTree01_1K/"
    "polyhaven_fir_tree_01_source_manifest.json"
)
REVIEWED_FIR_IMPORT_REPORT_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/polyhaven_fir_tree_01_import_report.json"
)
REVIEWED_FIR_VISUAL_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "polyhaven_fir_tree_01_visual_comparison_review.json"
)
REVIEWED_BROADLEAF_IMPORT_SCRIPT_PATH = (
    REPO_ROOT / "unreal/Scripts/import_reviewed_broadleaf_asset.py"
)
REVIEWED_BROADLEAF_SOURCE_MANIFEST_PATH = (
    REPO_ROOT
    / "unreal/Content/RaftSim/Environment/ExternalReview/PolyHaven/TreeSmall02_1K/"
    "polyhaven_tree_small_02_source_manifest.json"
)
REVIEWED_BROADLEAF_IMPORT_REPORT_PATH = (
    REPO_ROOT / "docs/environment-captures/photoreal_river_previews/"
    "polyhaven_tree_small_02_import_report.json"
)
REVIEWED_BROADLEAF_VISUAL_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "polyhaven_tree_small_02_visual_comparison_review.json"
)
REVIEWED_ROCK_IMPORT_SCRIPT_PATH = (
    REPO_ROOT / "unreal/Scripts/import_reviewed_rock_asset.py"
)
REVIEWED_ROCK_SOURCE_MANIFEST_PATH = (
    REPO_ROOT
    / "unreal/Content/RaftSim/Environment/ExternalReview/PolyHaven/RockMossSet01_1K/"
    "polyhaven_rock_moss_set_01_source_manifest.json"
)
REVIEWED_ROCK_IMPORT_REPORT_PATH = (
    REPO_ROOT / "docs/environment-captures/photoreal_river_previews/"
    "polyhaven_rock_moss_set_01_import_report.json"
)
REVIEWED_JACARANDA_IMPORT_SCRIPT_PATH = (
    REPO_ROOT / "unreal/Scripts/import_reviewed_jacaranda_asset.py"
)
REVIEWED_JACARANDA_SOURCE_MANIFEST_PATH = (
    REPO_ROOT
    / "unreal/Content/RaftSim/Environment/ExternalReview/PolyHaven/JacarandaTree_1K/"
    "polyhaven_jacaranda_tree_source_manifest.json"
)
REVIEWED_JACARANDA_IMPORT_REPORT_PATH = (
    REPO_ROOT / "docs/environment-captures/photoreal_river_previews/"
    "polyhaven_jacaranda_tree_import_report.json"
)
REVIEWED_JACARANDA_VISUAL_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "polyhaven_jacaranda_tree_visual_comparison_review.json"
)
REVIEWED_FUTALEUFU_FOREST_IMPORT_SCRIPT_PATH = (
    REPO_ROOT / "unreal/Scripts/import_reviewed_futaleufu_forest_set.py"
)
REVIEWED_FUTALEUFU_FOREST_SOURCE_MANIFEST_PATH = (
    REPO_ROOT / "unreal/Content/RaftSim/Environment/ExternalReview/PolyHaven/"
    "FutaleufuTemperateForestSet_1K/"
    "polyhaven_futaleufu_temperate_forest_set_source_manifest.json"
)
REVIEWED_FUTALEUFU_FOREST_IMPORT_REPORT_PATH = (
    REPO_ROOT / "docs/environment-captures/photoreal_river_previews/"
    "polyhaven_futaleufu_temperate_forest_set_import_report.json"
)
REVIEWED_FUTALEUFU_FOREST_VISUAL_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "polyhaven_futaleufu_temperate_forest_set_visual_comparison_review.json"
)
REVIEWED_FUTALEUFU_ISLAND_TREE_IMPORT_SCRIPT_PATH = (
    REPO_ROOT / "unreal/Scripts/import_reviewed_futaleufu_island_tree_set.py"
)
REVIEWED_FUTALEUFU_ISLAND_TREE_SOURCE_MANIFEST_PATH = (
    REPO_ROOT / "unreal/Content/RaftSim/Environment/ExternalReview/PolyHaven/"
    "FutaleufuIslandTreeSet_1K/"
    "polyhaven_futaleufu_island_tree_set_source_manifest.json"
)
REVIEWED_FUTALEUFU_ISLAND_TREE_IMPORT_REPORT_PATH = (
    REPO_ROOT / "docs/environment-captures/photoreal_river_previews/"
    "polyhaven_futaleufu_island_tree_set_import_report.json"
)
REVIEWED_FUTALEUFU_ISLAND_TREE_VISUAL_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "polyhaven_futaleufu_island_tree_set_visual_comparison_review.json"
)
PVE_FUTALEUFU_BEECH_SOURCE_MANIFEST_PATH = (
    REPO_ROOT / "unreal/Content/RaftSim/Environment/ProceduralVegetation/"
    "FutaleufuEuropeanBeechCandidate/"
    "pve_futaleufu_european_beech_source_manifest.json"
)
PVE_FUTALEUFU_BEECH_REPORT_PATHS = tuple(
    REPO_ROOT / "docs/environment-captures/photoreal_river_previews/"
    f"pve_futaleufu_european_beech_beech_{index:02d}_structural_report.json"
    for index in range(1, 5)
)
PVE_FUTALEUFU_BEECH_VISUAL_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "ue_pve_futaleufu_european_beech_visual_review.json"
)
FUTALEUFU_NATIVE_CANOPY_AUTHORING_SPEC_PATH = (
    REPO_ROOT
    / "unreal/Content/RaftSim/Environment/ProceduralVegetation/FutaleufuNativeCanopy/"
    "futaleufu_native_canopy_authoring_spec.json"
)
FUTALEUFU_CORDILLERA_CYPRESS_AUTHORING_MANIFEST_PATH = (
    REPO_ROOT
    / "unreal/Content/RaftSim/Environment/ProceduralVegetation/FutaleufuNativeCanopy/"
    "CordilleraCypress/futaleufu_cordillera_cypress_authoring_manifest.json"
)
FUTALEUFU_CORDILLERA_CYPRESS_TEXTURE_MANIFEST_PATH = (
    REPO_ROOT / FUTALEUFU_CORDILLERA_CYPRESS_TEXTURE_MANIFEST_RELATIVE_PATH
)
FUTALEUFU_CORDILLERA_CYPRESS_REPORT_PATH = (
    REPO_ROOT / FUTALEUFU_CORDILLERA_CYPRESS_REPORT_RELATIVE_PATH
)
FUTALEUFU_CORDILLERA_CYPRESS_REVIEW_PATH = (
    REPO_ROOT / FUTALEUFU_CORDILLERA_CYPRESS_REVIEW_RELATIVE_PATH
)
FUTALEUFU_CORDILLERA_CYPRESS_V2_REPORT_PATH = (
    REPO_ROOT / FUTALEUFU_CORDILLERA_CYPRESS_V2_REPORT_RELATIVE_PATH
)
FUTALEUFU_CORDILLERA_CYPRESS_V2_REVIEW_PATH = (
    REPO_ROOT / FUTALEUFU_CORDILLERA_CYPRESS_V2_REVIEW_RELATIVE_PATH
)
FUTALEUFU_CORDILLERA_CYPRESS_V3_REPORT_PATH = (
    REPO_ROOT / FUTALEUFU_CORDILLERA_CYPRESS_V3_REPORT_RELATIVE_PATH
)
FUTALEUFU_CORDILLERA_CYPRESS_V3_REVIEW_PATH = (
    REPO_ROOT / FUTALEUFU_CORDILLERA_CYPRESS_V3_REVIEW_RELATIVE_PATH
)
FUTALEUFU_CORDILLERA_CYPRESS_V4_REPORT_PATH = (
    REPO_ROOT / FUTALEUFU_CORDILLERA_CYPRESS_V4_REPORT_RELATIVE_PATH
)
FUTALEUFU_CORDILLERA_CYPRESS_V4_REVIEW_PATH = (
    REPO_ROOT / FUTALEUFU_CORDILLERA_CYPRESS_V4_REVIEW_RELATIVE_PATH
)
FUTALEUFU_CORDILLERA_CYPRESS_V5_REPORT_PATH = (
    REPO_ROOT / FUTALEUFU_CORDILLERA_CYPRESS_V5_REPORT_RELATIVE_PATH
)
FUTALEUFU_CORDILLERA_CYPRESS_V5_REVIEW_PATH = (
    REPO_ROOT / FUTALEUFU_CORDILLERA_CYPRESS_V5_REVIEW_RELATIVE_PATH
)
FUTALEUFU_CORDILLERA_CYPRESS_V6_REPORT_PATH = (
    REPO_ROOT / FUTALEUFU_CORDILLERA_CYPRESS_V6_REPORT_RELATIVE_PATH
)
FUTALEUFU_CORDILLERA_CYPRESS_V6_REVIEW_PATH = (
    REPO_ROOT / FUTALEUFU_CORDILLERA_CYPRESS_V6_REVIEW_RELATIVE_PATH
)
FUTALEUFU_CORDILLERA_CYPRESS_V7_REPORT_PATH = (
    REPO_ROOT / FUTALEUFU_CORDILLERA_CYPRESS_V7_REPORT_RELATIVE_PATH
)
FUTALEUFU_CORDILLERA_CYPRESS_V7_REVIEW_PATH = (
    REPO_ROOT / FUTALEUFU_CORDILLERA_CYPRESS_V7_REVIEW_RELATIVE_PATH
)
FUTALEUFU_CORDILLERA_CYPRESS_V8_REPORT_PATH = (
    REPO_ROOT / FUTALEUFU_CORDILLERA_CYPRESS_V8_REPORT_RELATIVE_PATH
)
FUTALEUFU_CORDILLERA_CYPRESS_V8_REVIEW_PATH = (
    REPO_ROOT / FUTALEUFU_CORDILLERA_CYPRESS_V8_REVIEW_RELATIVE_PATH
)
FUTALEUFU_CORDILLERA_CYPRESS_V9_REPORT_PATH = (
    REPO_ROOT / FUTALEUFU_CORDILLERA_CYPRESS_V9_REPORT_RELATIVE_PATH
)
FUTALEUFU_CORDILLERA_CYPRESS_V9_REVIEW_PATH = (
    REPO_ROOT / FUTALEUFU_CORDILLERA_CYPRESS_V9_REVIEW_RELATIVE_PATH
)
FUTALEUFU_CORDILLERA_CYPRESS_V10_REPORT_PATH = (
    REPO_ROOT / FUTALEUFU_CORDILLERA_CYPRESS_V10_REPORT_RELATIVE_PATH
)
FUTALEUFU_CORDILLERA_CYPRESS_V10_REVIEW_PATH = (
    REPO_ROOT / FUTALEUFU_CORDILLERA_CYPRESS_V10_REVIEW_RELATIVE_PATH
)
FUTALEUFU_CORDILLERA_CYPRESS_V10_TEXTURE_MANIFEST_PATH = (
    REPO_ROOT
    / "unreal/Content/RaftSim/Environment/ProceduralVegetation/"
    "FutaleufuNativeCanopy/CordilleraCypress/"
    "futaleufu_cordillera_cypress_v10_texture_manifest.json"
)
FUTALEUFU_CORDILLERA_CYPRESS_V11_REPORT_PATH = (
    REPO_ROOT / FUTALEUFU_CORDILLERA_CYPRESS_V11_REPORT_RELATIVE_PATH
)
FUTALEUFU_CORDILLERA_CYPRESS_V11_REVIEW_PATH = (
    REPO_ROOT / FUTALEUFU_CORDILLERA_CYPRESS_V11_REVIEW_RELATIVE_PATH
)
FUTALEUFU_CORDILLERA_CYPRESS_V12_REPORT_PATH = (
    REPO_ROOT / FUTALEUFU_CORDILLERA_CYPRESS_V12_REPORT_RELATIVE_PATH
)
FUTALEUFU_CORDILLERA_CYPRESS_V12_REVIEW_PATH = (
    REPO_ROOT / FUTALEUFU_CORDILLERA_CYPRESS_V12_REVIEW_RELATIVE_PATH
)
FUTALEUFU_CORDILLERA_CYPRESS_V13_REPORT_PATH = (
    REPO_ROOT / FUTALEUFU_CORDILLERA_CYPRESS_V13_REPORT_RELATIVE_PATH
)
FUTALEUFU_CORDILLERA_CYPRESS_V13_REVIEW_PATH = (
    REPO_ROOT / FUTALEUFU_CORDILLERA_CYPRESS_V13_REVIEW_RELATIVE_PATH
)
FUTALEUFU_CORDILLERA_CYPRESS_V14_REPORT_PATH = (
    REPO_ROOT / FUTALEUFU_CORDILLERA_CYPRESS_V14_REPORT_RELATIVE_PATH
)
FUTALEUFU_CORDILLERA_CYPRESS_V14_REVIEW_PATH = (
    REPO_ROOT / FUTALEUFU_CORDILLERA_CYPRESS_V14_REVIEW_RELATIVE_PATH
)
FUTALEUFU_CORDILLERA_CYPRESS_V15_REPORT_PATH = (
    REPO_ROOT / FUTALEUFU_CORDILLERA_CYPRESS_V15_REPORT_RELATIVE_PATH
)
FUTALEUFU_CORDILLERA_CYPRESS_V15_REVIEW_PATH = (
    REPO_ROOT / FUTALEUFU_CORDILLERA_CYPRESS_V15_REVIEW_RELATIVE_PATH
)
FUTALEUFU_CORDILLERA_CYPRESS_V16_REPORT_PATHS = tuple(
    sorted(
        (
            REPO_ROOT
            / "docs/environment-captures/photoreal_river_previews/landscape_candidates"
        ).glob("futaleufu_cordillera_cypress_v16_pve_*_report.json")
    )
)
FUTALEUFU_CORDILLERA_CYPRESS_V16_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v16_pve_visual_review.json"
)
FUTALEUFU_CORDILLERA_CYPRESS_V17_OPEN_REPORT_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v17_pve_open_grown_conical_report.json"
)
FUTALEUFU_CORDILLERA_CYPRESS_V21_REPORT_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v21_pve_open_grown_conical_"
    "compound_branchlet_atlas_report.json"
)
FUTALEUFU_CORDILLERA_CYPRESS_V21_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v21_compound_branchlet_visual_review.json"
)
FUTALEUFU_CORDILLERA_CYPRESS_V22_REPORT_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v22_pve_open_grown_conical_"
    "detiered_compound_branchlet_atlas_report.json"
)
FUTALEUFU_CORDILLERA_CYPRESS_V22_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v22_detiered_crown_visual_review.json"
)
FUTALEUFU_CORDILLERA_CYPRESS_V23_REPORT_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v23_pve_open_grown_conical_"
    "async_secondary_compound_branchlet_atlas_report.json"
)
FUTALEUFU_CORDILLERA_CYPRESS_V23_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v23_async_secondary_crown_visual_review.json"
)
FUTALEUFU_CORDILLERA_CYPRESS_V24_REPORT_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v24_pve_open_grown_conical_"
    "irregular_crown_mass_compound_branchlet_atlas_report.json"
)
FUTALEUFU_CORDILLERA_CYPRESS_V24_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v24_irregular_crown_mass_visual_review.json"
)
FUTALEUFU_CORDILLERA_CYPRESS_V25_REPORT_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v25_pve_open_grown_conical_"
    "hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas_report.json"
)
FUTALEUFU_CORDILLERA_CYPRESS_V25_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v25_hlod_handoff_visual_review.json"
)
FUTALEUFU_CORDILLERA_CYPRESS_V26_REPORT_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v26_pve_open_grown_conical_"
    "high_detail_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas_"
    "report.json"
)
FUTALEUFU_CORDILLERA_CYPRESS_V26_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v26_high_detail_hlod_visual_review.json"
)
FUTALEUFU_CORDILLERA_CYPRESS_V27_REPORT_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v27_pve_open_grown_conical_frozen_wpo_"
    "hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas_report.json"
)
FUTALEUFU_CORDILLERA_CYPRESS_V27_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v27_frozen_wpo_repeatability_review.json"
)
FUTALEUFU_CORDILLERA_CYPRESS_V28_REPORT_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v28_pve_open_grown_conical_frozen_wpo_"
    "high_detail_hlod_calibrated_irregular_crown_mass_compound_branchlet_atlas_"
    "report.json"
)
FUTALEUFU_CORDILLERA_CYPRESS_V28_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v28_frozen_wpo_resolution_review.json"
)
FUTALEUFU_CORDILLERA_CYPRESS_V29_REPORT_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v29_pve_open_grown_conical_frozen_wpo_"
    "azimuth_registered_hlod_calibrated_irregular_crown_mass_compound_"
    "branchlet_atlas_report.json"
)
FUTALEUFU_CORDILLERA_CYPRESS_V29_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v29_azimuth_registration_review.json"
)
FUTALEUFU_CORDILLERA_CYPRESS_V30_REPORT_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v30_pve_open_grown_conical_frozen_wpo_"
    "azimuth_registered_perspective_hlod_calibrated_irregular_crown_mass_"
    "compound_branchlet_atlas_report.json"
)
FUTALEUFU_CORDILLERA_CYPRESS_V30_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v30_perspective_projection_review.json"
)
FUTALEUFU_CORDILLERA_CYPRESS_V31_REPORT_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v31_pve_open_grown_conical_frozen_wpo_"
    "azimuth_registered_perspective_depth_hlod_calibrated_irregular_crown_"
    "mass_compound_branchlet_atlas_report.json"
)
FUTALEUFU_CORDILLERA_CYPRESS_V31_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v31_depth_proxy_review.json"
)
FUTALEUFU_CORDILLERA_CYPRESS_V32_REPORT_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v32_pve_open_grown_conical_frozen_wpo_"
    "azimuth_registered_perspective_complementary_transition_hlod_calibrated_"
    "irregular_crown_mass_compound_branchlet_atlas_report.json"
)
FUTALEUFU_CORDILLERA_CYPRESS_V32_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v32_complementary_transition_review.json"
)
FUTALEUFU_CORDILLERA_CYPRESS_V33_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v33_temporal_transition_path_review.json"
)
FUTALEUFU_CORDILLERA_CYPRESS_V34_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v34_persistent_motion_review.json"
)
FUTALEUFU_CORDILLERA_CYPRESS_V35_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v35_fine_transition_review.json"
)
FUTALEUFU_CORDILLERA_CYPRESS_V36_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v36_lit_river_view_review.json"
)
FUTALEUFU_CORDILLERA_CYPRESS_V36_CONTACT_SHEET_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v36_lit_river_view_contact_sheet.png"
)
FUTALEUFU_CORDILLERA_CYPRESS_V37_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v37_temporal_lit_handoff_review.json"
)
FUTALEUFU_CORDILLERA_CYPRESS_V37_CONTACT_SHEET_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v37_temporal_lit_handoff_contact_sheet.png"
)
FUTALEUFU_CORDILLERA_CYPRESS_V38_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v38_hlod_frame_search_review.json"
)
FUTALEUFU_CORDILLERA_CYPRESS_V38_CONTACT_SHEET_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v38_hlod_frame_search_contact_sheet.png"
)
FUTALEUFU_CORDILLERA_CYPRESS_V39_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v39_split_shading_review.json"
)
FUTALEUFU_CORDILLERA_CYPRESS_V39_CONTACT_SHEET_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v39_split_shading_contact_sheet.png"
)
FUTALEUFU_CORDILLERA_CYPRESS_V40_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v40_dual_layer_review.json"
)
FUTALEUFU_CORDILLERA_CYPRESS_V40_CONTACT_SHEET_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v40_dual_layer_contact_sheet.png"
)
FUTALEUFU_CORDILLERA_CYPRESS_V41_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v41_transmission_light_bracket_review.json"
)
FUTALEUFU_CORDILLERA_CYPRESS_V41_CONTACT_SHEET_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v41_transmission_light_bracket_contact_sheet.png"
)
FUTALEUFU_CORDILLERA_CYPRESS_V42_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v42_merged_geometry_shape_bracket_review.json"
)
FUTALEUFU_CORDILLERA_CYPRESS_V42_CONTACT_SHEET_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_cordillera_cypress_v42_merged_geometry_shape_bracket_contact_sheet.png"
)
FUTALEUFU_CORDILLERA_CYPRESS_V43_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates"
    / "futaleufu_cordillera_cypress_v43_merged_component_parity_review.json"
)
FUTALEUFU_CORDILLERA_CYPRESS_V43_CONTACT_SHEET_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates"
    / "futaleufu_cordillera_cypress_v43_merged_component_parity_contact_sheet.png"
)
FUTALEUFU_NATIVE_CANOPY_TEXTURE_MANIFEST_PATH = (
    REPO_ROOT / FUTALEUFU_NATIVE_CANOPY_TEXTURE_MANIFEST_RELATIVE_PATH
)
FUTALEUFU_NATIVE_CANOPY_PROTOTYPE_REPORT_PATH = (
    REPO_ROOT / "docs/environment-captures/photoreal_river_previews/"
    "futaleufu_native_canopy_coigue_prototype_report.json"
)
FUTALEUFU_NATIVE_CANOPY_VISUAL_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_native_canopy_coigue_visual_review.json"
)
FUTALEUFU_NATIVE_CANOPY_V2_VISUAL_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_native_canopy_coigue_v2_visual_review.json"
)
FUTALEUFU_NATIVE_CANOPY_V3_VISUAL_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_native_canopy_coigue_v3_visual_review.json"
)
FUTALEUFU_NATIVE_CANOPY_V4_VISUAL_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_native_canopy_coigue_v4_visual_review.json"
)
FUTALEUFU_NATIVE_CANOPY_V5_VISUAL_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_native_canopy_coigue_v5_visual_review.json"
)
FUTALEUFU_NATIVE_CANOPY_V6_VISUAL_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_native_canopy_coigue_v6_visual_review.json"
)
FUTALEUFU_NATIVE_CANOPY_V7_VISUAL_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_native_canopy_coigue_v7_visual_review.json"
)
FUTALEUFU_NATIVE_CANOPY_V8_VISUAL_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_native_canopy_coigue_v8_visual_review.json"
)
FUTALEUFU_NATIVE_CANOPY_V9_VISUAL_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_native_canopy_coigue_v9_visual_review.json"
)
FUTALEUFU_NATIVE_CANOPY_V10_VISUAL_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_native_canopy_coigue_v10_visual_review.json"
)
FUTALEUFU_NATIVE_CANOPY_V11_PERFORMANCE_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_native_canopy_coigue_v11_performance_review.json"
)
FUTALEUFU_NATIVE_CANOPY_V12_RUNTIME_LOD_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_native_canopy_coigue_v12_runtime_lod_review.json"
)
FUTALEUFU_NATIVE_CANOPY_V13_CORRIDOR_COMPARISON_REPORT_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_native_canopy_coigue_v13_corridor_comparison_report.json"
)
FUTALEUFU_NATIVE_CANOPY_V13_CORRIDOR_VISUAL_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_native_canopy_coigue_v13_corridor_visual_review.json"
)
FUTALEUFU_NATIVE_CANOPY_V14_INSTANCED_MATERIAL_COMPARISON_REPORT_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_native_canopy_coigue_v14_instanced_material_comparison_report.json"
)
FUTALEUFU_NATIVE_CANOPY_V14_INSTANCED_MATERIAL_VISUAL_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_native_canopy_coigue_v14_instanced_material_visual_review.json"
)
FUTALEUFU_NATIVE_CANOPY_V15_RENDER_DIAGNOSTIC_REPORT_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_native_canopy_coigue_v15_leaf_shadow_opacity_diagnostic_report.json"
)
FUTALEUFU_NATIVE_CANOPY_V15_RENDER_DIAGNOSTIC_VISUAL_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_native_canopy_coigue_v15_leaf_shadow_opacity_visual_review.json"
)
FUTALEUFU_NATIVE_CANOPY_V16_OPACITY_DIAGNOSTIC_REPORT_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_native_canopy_coigue_v16_same_shader_opacity_diagnostic_report.json"
)
FUTALEUFU_NATIVE_CANOPY_V16_OPACITY_DIAGNOSTIC_VISUAL_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_native_canopy_coigue_v16_same_shader_opacity_visual_review.json"
)
FUTALEUFU_NATIVE_CANOPY_V17_LIGHTING_DIAGNOSTIC_REPORT_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_native_canopy_coigue_v17_lighting_diagnostic_report.json"
)
FUTALEUFU_NATIVE_CANOPY_V17_LIGHTING_DIAGNOSTIC_VISUAL_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_native_canopy_coigue_v17_lighting_visual_review.json"
)
FUTALEUFU_NATIVE_CANOPY_V18_LIGHT_RIG_DIAGNOSTIC_REPORT_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_native_canopy_coigue_v18_corridor_light_rig_diagnostic_report.json"
)
FUTALEUFU_NATIVE_CANOPY_V18_LIGHT_RIG_DIAGNOSTIC_VISUAL_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_native_canopy_coigue_v18_corridor_light_rig_visual_review.json"
)
FUTALEUFU_NATIVE_CANOPY_V19_REFLECTANCE_DIAGNOSTIC_REPORT_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_native_canopy_coigue_v19_reflectance_diagnostic_report.json"
)
FUTALEUFU_NATIVE_CANOPY_V19_REFLECTANCE_DIAGNOSTIC_VISUAL_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_native_canopy_coigue_v19_reflectance_visual_review.json"
)
FUTALEUFU_NATIVE_CANOPY_V20_SHADING_MODEL_DIAGNOSTIC_REPORT_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_native_canopy_coigue_v20_shading_model_diagnostic_report.json"
)
FUTALEUFU_NATIVE_CANOPY_V20_SHADING_MODEL_DIAGNOSTIC_VISUAL_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_native_canopy_coigue_v20_shading_model_visual_review.json"
)
FUTALEUFU_NATIVE_CANOPY_V21_MIP_PADDING_DIAGNOSTIC_REPORT_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_native_canopy_coigue_v21_mip_padding_diagnostic_report.json"
)
FUTALEUFU_NATIVE_CANOPY_V21_MIP_PADDING_DIAGNOSTIC_VISUAL_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_native_canopy_coigue_v21_mip_padding_visual_review.json"
)
FUTALEUFU_NATIVE_CANOPY_V22_OPACITY_SELECTION_DIAGNOSTIC_REPORT_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_native_canopy_coigue_v22_opacity_selection_diagnostic_report.json"
)
FUTALEUFU_NATIVE_CANOPY_V22_OPACITY_SELECTION_DIAGNOSTIC_VISUAL_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_native_canopy_coigue_v22_opacity_selection_visual_review.json"
)
FUTALEUFU_NATIVE_CANOPY_V23_BOUNDED_SHADOW_DIAGNOSTIC_REPORT_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_native_canopy_coigue_v23_bounded_shadow_diagnostic_report.json"
)
FUTALEUFU_NATIVE_CANOPY_V23_BOUNDED_SHADOW_DIAGNOSTIC_VISUAL_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_native_canopy_coigue_v23_bounded_shadow_visual_review.json"
)
FUTALEUFU_NATIVE_CANOPY_V24_DENSE_COMPARISON_REPORT_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_native_canopy_coigue_v24_dense_canopy_comparison_report.json"
)
FUTALEUFU_NATIVE_CANOPY_V24_DENSE_VISUAL_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_native_canopy_coigue_v24_dense_canopy_visual_review.json"
)
FUTALEUFU_NATIVE_CANOPY_V25_AREA_SAMPLED_COMPARISON_REPORT_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_native_canopy_coigue_v25_area_sampled_comparison_report.json"
)
FUTALEUFU_NATIVE_CANOPY_V25_AREA_SAMPLED_VISUAL_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_native_canopy_coigue_v25_area_sampled_visual_review.json"
)
FUTALEUFU_NATIVE_CANOPY_V26_WORLD_STABLE_COMPARISON_REPORT_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_native_canopy_coigue_v26_world_stable_comparison_report.json"
)
FUTALEUFU_NATIVE_CANOPY_V26_WORLD_STABLE_VISUAL_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "futaleufu_native_canopy_coigue_v26_world_stable_visual_review.json"
)
REVIEWED_PINE_IMPORT_SCRIPT_PATH = (
    REPO_ROOT / "unreal/Scripts/import_reviewed_pine_asset.py"
)
REVIEWED_PINE_SOURCE_MANIFEST_PATH = (
    REPO_ROOT
    / "unreal/Content/RaftSim/Environment/ExternalReview/PolyHaven/PineTree01_1K/"
    "polyhaven_pine_tree_01_source_manifest.json"
)
REVIEWED_PINE_IMPORT_REPORT_PATH = (
    REPO_ROOT / "docs/environment-captures/photoreal_river_previews/"
    "polyhaven_pine_tree_01_import_report.json"
)
REVIEWED_TERRAIN_DETAIL_IMPORT_SCRIPT_PATH = (
    REPO_ROOT / "unreal/Scripts/import_reviewed_terrain_detail_asset.py"
)
REVIEWED_TERRAIN_DETAIL_SOURCE_MANIFEST_PATH = (
    REPO_ROOT
    / "unreal/Content/RaftSim/Environment/ExternalReview/PolyHaven/ForestGround03_4K/"
    "polyhaven_forest_ground_03_source_manifest.json"
)
REVIEWED_TERRAIN_DETAIL_IMPORT_REPORT_PATH = (
    REPO_ROOT / "docs/environment-captures/photoreal_river_previews/"
    "polyhaven_forest_ground_03_import_report.json"
)
REVIEWED_ROCK_GROUND_IMPORT_SCRIPT_PATH = (
    REPO_ROOT / "unreal/Scripts/import_reviewed_rock_ground_detail_asset.py"
)
REVIEWED_ROCK_GROUND_SOURCE_MANIFEST_PATH = (
    REPO_ROOT
    / "unreal/Content/RaftSim/Environment/ExternalReview/PolyHaven/RockGround_4K/"
    "polyhaven_rock_ground_source_manifest.json"
)
REVIEWED_ROCK_GROUND_IMPORT_REPORT_PATH = (
    REPO_ROOT / "docs/environment-captures/photoreal_river_previews/"
    "polyhaven_rock_ground_import_report.json"
)
REVIEWED_ZAMBEZI_CLIFF_IMPORT_SCRIPT_PATH = (
    REPO_ROOT / "unreal/Scripts/import_reviewed_zambezi_cliff_asset.py"
)
REVIEWED_ZAMBEZI_CLIFF_SOURCE_MANIFEST_PATH = (
    REPO_ROOT / "unreal/Content/RaftSim/Environment/ExternalReview/PolyHaven/"
    "NamaqualandCliff02_2K/polyhaven_namaqualand_cliff_02_source_manifest.json"
)
REVIEWED_ZAMBEZI_CLIFF_IMPORT_REPORT_PATH = (
    REPO_ROOT / "docs/environment-captures/photoreal_river_previews/"
    "polyhaven_namaqualand_cliff_02_import_report.json"
)
REVIEWED_ZAMBEZI_CLIFF_COMPARISON_REPORT_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "polyhaven_namaqualand_cliff_02_corridor_comparison_report.json"
)
REVIEWED_ZAMBEZI_CLIFF_VISUAL_REVIEW_PATH = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "polyhaven_namaqualand_cliff_02_corridor_visual_review.json"
)
ZAMBEZI_BATOKA_BASALT_AUTHORING_MANIFEST_PATH = (
    REPO_ROOT
    / "unreal/Content/RaftSim/Environment/ProceduralGeology/ZambeziBatokaBasalt/"
    "zambezi_batoka_basalt_authoring_manifest.json"
)
REVIEWED_BATOKA_DETAIL_IMPORT_SCRIPT_PATH = (
    REPO_ROOT / "unreal/Scripts/import_reviewed_batoka_basalt_surface.py"
)
REVIEWED_BATOKA_DETAIL_SOURCE_MANIFEST_PATH = (
    REPO_ROOT
    / "unreal/Content/RaftSim/Environment/ExternalReview/AmbientCG/Rock037_2K/"
    "ambientcg_rock037_source_manifest.json"
)
REVIEWED_BATOKA_DETAIL_IMPORT_REPORT_PATH = (
    REPO_ROOT / "docs/environment-captures/photoreal_river_previews/"
    "ambientcg_rock037_batoka_surface_import_report.json"
)
REVIEWED_BATOKA_MACRO_IMPORT_SCRIPT_PATH = (
    REPO_ROOT / "unreal/Scripts/import_reviewed_batoka_macro_surface.py"
)
REVIEWED_BATOKA_MACRO_SOURCE_MANIFEST_PATH = (
    REPO_ROOT / "unreal/Content/RaftSim/Environment/ExternalReview/PolyHaven/"
    "AerialRocks02_4K/polyhaven_aerial_rocks_02_source_manifest.json"
)
REVIEWED_BATOKA_MACRO_IMPORT_REPORT_PATH = (
    REPO_ROOT / "docs/environment-captures/photoreal_river_previews/"
    "polyhaven_aerial_rocks_02_batoka_macro_import_report.json"
)
WATER_MATERIAL_REVIEW_PATH = (
    REPO_ROOT / "unreal/Content/RaftSim/Rendering/water_material_candidate_review.json"
)
SOLVER_VISUALIZATION_FIELD_MANIFEST_PATH = (
    REPO_ROOT / SOLVER_VISUALIZATION_FIELD_MANIFEST_RELATIVE_PATH
)
EXPECTED_CAPTURE_QUALITY_STATUS = (
    "captures_reviewed_preview_only_not_lifelike_quality_blockers_recorded"
)
EXPECTED_FLOW_VARIANT_CAPTURE_QUALITY_STATUS = (
    "flow_variant_captures_reviewed_preview_only_not_lifelike_quality_blockers_recorded"
)
EXPECTED_CAPTURE_STATUS = "preview_only_not_lifelike_quality_blockers"
EXPECTED_CAPTURE_BLOCKER_ID = "low_color_texture_entropy"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


__all__ = [name for name in globals() if not name.startswith("__")]
