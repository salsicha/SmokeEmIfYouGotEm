"""Focused plain-function checks for environments without pytest; not a full-suite runner."""
import json
from pathlib import Path
import runpy
import traceback

root = Path(__file__).resolve().parents[2]
modules = (
    "test_futaleufu_current_water_presentation",
    "test_pacuare_current_water_presentation",
    "test_colorado_current_water_presentation",
    "test_south_fork_water_performance_and_banding",
    "test_full_reach_water_presentation",
    "test_photoreal_futaleufu_terminator_water",
)
results = []
for module in modules:
    namespace = runpy.run_path(str(root / "physics/tests" / (module + ".py")))
    for name, function in namespace.items():
        if not name.startswith("test_") or not callable(function):
            continue
        result = {"module": module, "test": name, "passed": False}
        try:
            function()
            result["passed"] = True
        except Exception:
            result["error"] = traceback.format_exc()
        results.append(result)
        print("PASS" if result["passed"] else "FAIL", module, name)
output = root / "unreal/Saved/RaftSimValidation/futaleufu-water-tests.json"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(results, indent=2), encoding="utf-8")
print(f"{sum(r['passed'] for r in results)}/{len(results)} passed; details: {output}")
raise SystemExit(0 if all(r["passed"] for r in results) else 1)
