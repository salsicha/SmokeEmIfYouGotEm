"""Strict read-only Blender C01 cache clock and compiled snapshot inspection.

Layout checked against Blender fbe6228777e7 MANTA_main.cpp and DNA_fluid_types.h.
These are stored native timestamps, not a clock inferred from a playback solver
whose cache-loading initialization may leave timeTotal/frame at zero.
"""
import dis
import gzip
import io
import math
import struct

LAYOUT = struct.Struct('<4i2f9f3i3f16f9i3ff4s')


def decode_configuration(encoded):
    """Read only the exact little-endian, 204-byte version-C01 record.

The writer uses sizeof(int) for time_total's byte count, but DNA declares the
field float; its four bytes are decoded as float32, never reinterpreted as int.
dx is dimensionless 1/maxres, NOT a physical metre-valued cell size.
"""
    if not isinstance(encoded, bytes):
        raise ValueError('Need compressed immutable cache bytes')
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(encoded), mode='rb') as stream:
            data = stream.read(LAYOUT.size+1)
    except (OSError, EOFError) as exc:
        raise ValueError('Invalid gzip configuration') from exc
    if len(data) != LAYOUT.size:
        raise ValueError('Unsupported configuration length')
    fields = LAYOUT.unpack(data)
    if fields[-1] != b'C01\x00':
        raise ValueError('Unsupported Blender cache version')
    active, resolution = fields[0], tuple(fields[1:4])
    floats = (*fields[4:15], *fields[18:37], *fields[46:50])
    if (active < 0 or min(resolution) <= 0 or min(fields[37:40]) <= 0
            or not all(math.isfinite(x) for x in floats)
            or fields[4] <= 0 or fields[5] <= 0 or fields[49] < 0):
        raise ValueError('Invalid finite configuration dimensions/clock')
    return dict(version='C01', active_fields=active, resolution=list(resolution),
        dimensionless_dx=fields[4], last_timestep_native=fields[5],
        p0=list(fields[6:9]), p1=list(fields[9:12]), dp0=list(fields[12:15]),
        shift=list(fields[15:18]), object_shift=list(fields[18:21]),
        object_matrix=list(fields[21:37]), base_resolution=list(fields[37:40]),
        resolution_min=list(fields[40:43]), resolution_max=list(fields[43:46]),
        active_color=list(fields[46:49]), time_total_native=fields[49],
        payload_bytes=len(data), accepted=False)


def interval_clock(before, after, frame_span, fps, time_scale=1.):
    """Expose native and playback intervals; no field/time resampling or fitting."""
    if (isinstance(frame_span, bool) or not isinstance(frame_span, int) or frame_span <= 0
            or not all(math.isfinite(x) and x > 0 for x in (fps, time_scale))):
        raise ValueError('Need positive frame span, fps and domain time scale')
    delta = after['time_total_native']-before['time_total_native']
    if not math.isfinite(delta) or delta <= 0:
        raise ValueError('Non-increasing native cache clock')
    expected = .1*25*time_scale*frame_span/fps
    return dict(native_interval=delta, expected_native_interval=expected,
        native_interval_error=delta-expected, playback_interval_seconds=frame_span/fps,
        native_interval_in_physical_seconds=delta/2.5,
        domain_time_scale=time_scale, accepted=False)


def beginning_frame_snapshot(function, solver, phi, velocity, phi_previous, velocity_previous):
    """Prove the compiled copy block is skipped when timePerFrame is nonzero.

This narrow inspector rejects other code instead of guessing its semantics.
It never calls the function. Normalize method loads across Python 3.11..3.13;
the native audit separately pins the Blender build/Python interpreter.
"""
    instructions = list(dis.get_instructions(function))
    for index, instruction in enumerate(instructions):
        if instruction.opname in ('LOAD_ATTR', 'LOAD_METHOD') and instruction.argval == 'timePerFrame':
            if index == 0 or instructions[index-1].argval != solver:
                continue
            jump_index = index+1
            if instructions[jump_index].opname == 'TO_BOOL':
                jump_index += 1
            jump = instructions[jump_index]
            if jump.opname not in ('POP_JUMP_IF_TRUE', 'POP_JUMP_FORWARD_IF_TRUE'):
                continue
            block = [i for i in instructions[jump_index+1:] if i.offset < jump.argval]
            actual = [('LOAD_ATTR' if i.opname == 'LOAD_METHOD' else i.opname, i.argval)
                      for i in block if i.opname not in ('PRECALL', 'CACHE', 'EXTENDED_ARG')]
            expected = []
            for target, source in ((phi_previous, phi), (velocity_previous, velocity)):
                expected += [('LOAD_GLOBAL', target), ('LOAD_ATTR', 'copyFrom'),
                             ('LOAD_GLOBAL', source), ('CALL', 1), ('POP_TOP', None)]
            if actual != expected:
                raise ValueError('Unexpected beginning-frame snapshot body')
            return dict(condition='not solver.timePerFrame', copy_only_at_frame_beginning=True,
                phi_source=phi, velocity_source=velocity, phi_target=phi_previous,
                velocity_target=velocity_previous, condition_offset=instruction.offset,
                skip_target_offset=jump.argval, block_instructions=actual, accepted=False)
    raise ValueError('Supported compiled beginning-frame copy guard not found')
