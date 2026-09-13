"""Remove only process-local wrapper addresses from graph audit values."""
import re


def canonical_graph(value):
    if not isinstance(value, dict):
        return value
    result = {}
    for key, item in value.items():
        if key in ('default_value', 'texture') and isinstance(item, str):
            item = re.sub(r' \(0x[0-9a-fA-F]+\)', '', item)
        result[key] = canonical_graph(item)
    return result
