"""Rebind an exact compiled function to explicit owned globals, never aliases.

The caller owns native resource allocation. This helper does not invent values
for absent globals, and rejects non-owned executable/resource substitutions.
"""
import dis
import hashlib
import marshal
import types


def immutable(value):
    return isinstance(value, (type(None), bool, int, float, str)) or (
        isinstance(value, tuple) and all(immutable(x) for x in value))


def global_names(function):
    if not isinstance(function, types.FunctionType) or function.__closure__:
        raise ValueError('Need a closure-free compiled function')
    return sorted({i.argval for i in dis.get_instructions(function)
                   if i.opname == 'LOAD_GLOBAL'})


def bind_owned(function, owned, native_calls, safe_builtins):
    """Allow only supplied resources/scalars and an explicit native-call table.

Native C functions are shared code, not engine solver instances. Unknown
globals that are absent in the original remain absent in the private function;
they are never populated to make an inactive native branch run successfully.
"""
    names = global_names(function)
    if not immutable(function.__defaults__) or function.__kwdefaults__:
        raise ValueError('Mutable or keyword defaults are not owned')
    if set(owned) & set(native_calls) or set(owned) & set(safe_builtins):
        raise ValueError('Ambiguous owned/native/builtin binding')
    if not all(isinstance(v, types.BuiltinFunctionType) for v in native_calls.values()):
        raise ValueError('Only native C callables may be shared')
    missing = [n for n in names if n in function.__globals__
               and n not in owned and n not in native_calls and n not in safe_builtins]
    if missing:
        raise ValueError('Unowned globals: '+', '.join(missing))
    for name, value in owned.items():
        if name in function.__globals__ and value is function.__globals__[name]:
            if not immutable(value):
                raise ValueError('Live mutable/resource alias: '+name)
    space = {n: owned[n] for n in names if n in owned}
    space.update({n: native_calls[n] for n in names if n in native_calls})
    space['__builtins__'] = dict(safe_builtins)
    bound = types.FunctionType(function.__code__, space, function.__name__, function.__defaults__)
    if bound.__code__ is not function.__code__ or bound.__globals__ is function.__globals__:
        raise ValueError('Compiled code or resource isolation changed')
    return bound, dict(global_names=names,
        absent_native_globals=[n for n in names if n not in function.__globals__ and n not in safe_builtins],
        exact_code_object=True, private_globals=True,
        code_sha256=hashlib.sha256(marshal.dumps(function.__code__)).hexdigest())
