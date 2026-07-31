"""Read-only structural audit for reviewed and regenerated river-water materials.

Run through Unreal Editor with ``-ExecutePythonScript``.  The script never
modifies or saves an asset.  It records expression classes, stable authored
properties, and input-class relationships for the reviewed production material
and the isolated preview generated from the current C++ recipe.
"""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path

import unreal


MATERIAL_PATHS = {
    "production": "/Game/RaftSim/Materials/M_RaftSim_PhotorealRiverWater",
    "preview": "/Game/RaftSim/Experiments/M_RaftSim_PhotorealRiverWater_Preview",
}

AUDITED_PROPERTIES = (
    "parameter_name",
    "default_value",
    "constant",
    "scale",
    "quality",
    "levels",
    "output_min",
    "output_max",
    "noise_function",
    "turbulence",
    "speed_x",
    "speed_y",
    "u_tiling",
    "v_tiling",
    "sampler_type",
    "texture",
)


def _stable_value(value: object) -> object:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if all(hasattr(value, channel) for channel in ("r", "g", "b", "a")):
        return {
            channel: round(float(getattr(value, channel)), 8)
            for channel in ("r", "g", "b", "a")
        }
    if all(hasattr(value, channel) for channel in ("x", "y", "z")):
        channels = ("x", "y", "z", "w") if hasattr(value, "w") else ("x", "y", "z")
        return {
            channel: round(float(getattr(value, channel)), 8)
            for channel in channels
        }
    get_path_name = getattr(value, "get_path_name", None)
    if callable(get_path_name):
        return get_path_name()
    return str(value)


def _audit_material(asset_path: str) -> dict[str, object]:
    material = unreal.EditorAssetLibrary.load_asset(asset_path)
    if material is None:
        raise RuntimeError(f"missing material: {asset_path}")

    expressions = unreal.MaterialEditingLibrary.get_material_expressions(material)
    rows: list[dict[str, object]] = []
    for expression in expressions:
        class_name = expression.get_class().get_name()
        properties: dict[str, object] = {}
        for property_name in AUDITED_PROPERTIES:
            try:
                value = expression.get_editor_property(property_name)
            except Exception:
                continue
            properties[property_name] = _stable_value(value)
        inputs = [
            {
                "object_name": input_expression.get_name(),
                "class": input_expression.get_class().get_name(),
            }
            for input_expression in unreal.MaterialEditingLibrary.get_inputs_for_material_expression(
                material, expression
            )
            if input_expression is not None
        ]
        rows.append(
            {
                "object_name": expression.get_name(),
                "class": class_name,
                "properties": properties,
                "inputs": inputs,
            }
        )

    rows_by_name = {row["object_name"]: row for row in rows}
    canonical_cache: dict[str, str] = {}

    def canonical_expression(object_name: str, active: frozenset[str]) -> str:
        if object_name in canonical_cache:
            return canonical_cache[object_name]
        if object_name in active:
            raise RuntimeError(f"material expression cycle at {object_name}")
        row = rows_by_name[object_name]
        payload = {
            "class": row["class"],
            "properties": row["properties"],
            "inputs": [
                canonical_expression(
                    input_row["object_name"], active | {object_name}
                )
                for input_row in row["inputs"]
            ],
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        canonical_cache[object_name] = canonical
        return canonical

    canonical_hashes = sorted(
        hashlib.sha256(
            canonical_expression(row["object_name"], frozenset()).encode("utf-8")
        ).hexdigest()
        for row in rows
    )
    material_properties: dict[str, object] = {}
    for property_name in (
        "blend_mode",
        "two_sided",
        "tangent_space_normal",
        "dithered_lod_transition",
    ):
        try:
            value = material.get_editor_property(property_name)
        except Exception:
            continue
        material_properties[property_name] = _stable_value(value)

    rows.sort(
        key=lambda row: (
            row["class"],
            row["object_name"],
            json.dumps(row["properties"], sort_keys=True),
            json.dumps(row["inputs"]),
        )
    )
    return {
        "asset_path": asset_path,
        "expression_count": len(rows),
        "expression_class_counts": dict(
            sorted(Counter(row["class"] for row in rows).items())
        ),
        "material_properties": material_properties,
        "canonical_expression_sha256": canonical_hashes,
        "expressions": rows,
    }


report = {
    "schema": "raftsim.m9.water_material_parity_audit.v1",
    "read_only": True,
    "materials": {
        label: _audit_material(asset_path)
        for label, asset_path in MATERIAL_PATHS.items()
    },
}
production = report["materials"]["production"]
preview = report["materials"]["preview"]
report["structurally_equal"] = all(
    production[key] == preview[key]
    for key in (
        "expression_count",
        "expression_class_counts",
        "material_properties",
        "canonical_expression_sha256",
    )
)

output_path = (
    Path(unreal.Paths.project_saved_dir())
    / "Diagnostics"
    / "m9_water_material_parity_audit.json"
)
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log(f"audit_water_material_parity: wrote {output_path}")
unreal.log(
    "audit_water_material_parity: structurally_equal="
    f"{report['structurally_equal']}"
)
