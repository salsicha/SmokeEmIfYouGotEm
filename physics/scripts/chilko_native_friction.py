"""Explicit adapter for the native solver's legacy `roughness` coefficient.

The C++ damping is 1-dt*roughness*speed/h**(4/3), without another g*n*n.
Keep this conversion scoped to new Chilko/Colorado full-corridor inputs; do not
retune installed legacy river cooks. Runtime's historically named `manning_n` field also carries this
coefficient verbatim, so its physical interpretation needs separate metadata.
"""
import math
import copy

GRAVITY = 9.81
POLICY = 'native_quadratic_drag_coefficient_g_n_squared_v1'


def friction_contract(manning_n):
    n = float(manning_n)
    if not math.isfinite(n) or not 0 < n <= .2:
        raise ValueError('Finite bounded Manning inference required')
    return dict(policy=POLICY, inferred_manning_n=n, gravity_mps2=GRAVITY,
                native_roughness_coefficient=GRAVITY*n*n,
                measured=False)


def validate_friction(scenario, inferred_manning_n):
    expected = friction_contract(inferred_manning_n)
    actual = scenario.get('metadata', {}).get('provenance', {}).get('friction')
    if actual != expected or scenario.get('roughness') != expected['native_roughness_coefficient']:
        raise ValueError('Native friction coefficient and Manning inference disagree')
    return expected


def with_manning_friction(scenario, inferred_manning_n):
    """Explicit fresh-input conversion; no change to bed, state or boundaries."""
    result = copy.deepcopy(scenario)
    contract = friction_contract(inferred_manning_n)
    result['roughness'] = contract['native_roughness_coefficient']
    result.setdefault('metadata', {}).setdefault('provenance', {})['friction'] = contract
    validate_friction(result, inferred_manning_n)
    return result


def runtime_friction_fields(scenario):
    """Preserve the engine's coefficient-valued fields; add unambiguous receipt."""
    coefficient = scenario['roughness']
    fields = dict(manning_n=coefficient, effective_manning_n=coefficient)
    contract = scenario.get('metadata', {}).get('provenance', {}).get('friction')
    if contract is not None:
        validate_friction(scenario, contract['inferred_manning_n'])
        fields.update(friction=contract, native_roughness_coefficient=coefficient,
                      legacy_manning_fields_semantics='native_quadratic_drag_coefficient_not_manning_n')
    return fields
