"""Read-only inventory of the actual live South Fork water parent."""
import json
from pathlib import Path
import unreal

path = "/Game/RaftSim/Environment/SouthForkFullReach/Water/Materials/M_RaftSim_SouthForkRaftTransmissionWaterV4"
material = unreal.load_asset(path)
rows = []
expressions = unreal.MaterialEditingLibrary.get_material_expressions(material)
for expression in expressions:
    row = {"name": expression.get_name(), "class": expression.get_class().get_name()}
    for prop in ("parameter_name", "default_value", "code", "description", "desc", "texture", "coordinate_index", "u_tiling", "v_tiling", "sampler_source"):
        try:
            row[prop] = str(expression.get_editor_property(prop))
        except Exception:
            pass
    row["inputs"] = [e.get_name() for e in unreal.MaterialEditingLibrary.get_inputs_for_material_expression(material, expression) if e]
    rows.append(row)
origins = [row for row in rows if row.get("parameter_name") == "RaftSimWaterUVOrigin"]
chop = [row for row in rows if row.get("parameter_name") == "AnalyticChopStrength"]
assert len(chop) == 1 and float(chop[0]["default_value"]) == 0.0, "Legacy analytic normal waves must have a disabled amplitude gate"
assert any(chop[0]["name"] in row["inputs"] for row in rows), "Analytic normal gate must be wired into the graph"
assert len(origins) == 1, "Water needs exactly one shared full-precision river UV origin"
fluid = [row for row in rows if "float boilPhase" in row.get("code", "")]
assert len(fluid) == 1 and "WaveClock * 1.70 + 2.90 * boilNoiseB" in fluid[0]["code"], (
    "Saved water must use bounded boil phase offsets, not time-amplified advected noise"
)
coordinates = [row for row in rows if row["class"] == "MaterialExpressionTextureCoordinate" and row.get("coordinate_index") == "0"]
for coordinate in coordinates:
    consumers = [row for row in rows if coordinate["name"] in row["inputs"]]
    assert len(consumers) == 1 and consumers[0]["class"] == "MaterialExpressionAdd", (
        f"Unrebased river UV bypass: {coordinate['name']}: {consumers}"
    )
output = Path(unreal.Paths.project_saved_dir()) / "RaftSimValidation/troublemaker-water-material.json"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps({"path": path, "rebased_coordinates": len(coordinates), "expressions": rows}, indent=2), encoding="utf-8")
unreal.log(f"Water material audit: {output}")
