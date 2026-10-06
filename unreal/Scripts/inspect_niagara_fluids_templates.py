"""Read-only inventory of UE 5.8 Niagara Fluids liquid templates.

Run with NiagaraFluids enabled on the command line. The script intentionally
does not save packages; it records the callable surface and exposed parameter
store needed to decide whether a solver-gated review component can reuse an
engine liquid template without modifying production content.
"""

import unreal


TEMPLATE_PATHS = (
    "/NiagaraFluids/Templates/Liquid/3D/Systems/Grid3D_Flip_Splash",
    "/NiagaraFluids/Templates/Liquid/3D/Systems/Grid3D_Flip_Hose",
    "/NiagaraFluids/Templates/Liquid/2D/Systems/Grid2D_FLIP_Splash",
    "/NiagaraFluids/Templates/Liquid/2D/Systems/ShallowWater/Grid2D_SW_Drop",
)


def _safe_property(obj, name):
    try:
        return obj.get_editor_property(name)
    except Exception as exc:  # Unreal reflection exposes version-specific fields.
        return f"<unavailable: {exc}>"


for asset_path in TEMPLATE_PATHS:
    system = unreal.load_asset(asset_path)
    print(f"RAFTSIM_NIAGARA_FLUID_TEMPLATE path={asset_path} loaded={system is not None}")
    if system is None:
        continue
    print(f"RAFTSIM_NIAGARA_FLUID_CLASS {system.get_class().get_path_name()}")
    callables = [
        name
        for name in dir(system)
        if "parameter" in name.lower() or "exposed" in name.lower()
    ]
    print(f"RAFTSIM_NIAGARA_FLUID_CALLABLES {callables}")
    exposed = _safe_property(system, "exposed_parameters")
    print(f"RAFTSIM_NIAGARA_FLUID_EXPOSED {exposed}")
    if not isinstance(exposed, str):
        exposed_callables = [
            name
            for name in dir(exposed)
            if "parameter" in name.lower() or "variable" in name.lower()
        ]
        print(f"RAFTSIM_NIAGARA_FLUID_STORE_CALLABLES {exposed_callables}")
