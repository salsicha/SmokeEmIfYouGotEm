"""Permit only exact successful-data state transitions in a mesh preflight."""


def validate_completed_data_settings(prepared, loaded, end_frame):
    expected = dict(prepared)
    transitions = {'cache_frame_pause_data': (0, end_frame),
                   'has_cache_baked_data': (False, True),
                   'has_cache_baked_any': (False, True)}
    for key, (before, after) in transitions.items():
        if key not in prepared or prepared[key] != before:
            raise ValueError('Pristine prepared data state required: '+key)
        expected[key] = after
    if expected != loaded:
        differences = [(key, expected.get(key), loaded.get(key))
                       for key in set(expected) | set(loaded)
                       if expected.get(key) != loaded.get(key)]
        raise ValueError('Unexpected prepared-settings change: '+repr(differences))
    return {key: dict(before=before, after=after) for key, (before, after) in transitions.items()}
