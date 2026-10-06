"""Rigid presentation registration; never modify liquid/source coordinates."""
import math
import struct


def review_frame(manifest, geometry, geographic=False):
    source_yaw = float(manifest['local_to_engine_yaw_degrees'])
    origin = tuple(float(v) for v in manifest['local_origin_engine_cm'])
    if len(origin) != 3 or not all(math.isfinite(v) for v in (*origin, source_yaw)):
        raise ValueError('Finite liquid origin and yaw required')
    # The Unreal Python Rotator constructor takes a float input. Use the same
    # representable angle for camera/source diagnostics, retaining the source
    # value separately. This avoids comparing float-input engine poses to an
    # unrepresentable double angle (1.14 micrometres over this test window).
    yaw = struct.unpack('f',struct.pack('f',source_yaw))[0]
    if geographic:
        if not geometry.get('coordinate_rebase_only'):
            raise ValueError('Geographic review requires the documented source rebase')
        offset = tuple(float(v) for v in geometry['parent_frame_offset_east_north_m'])
        if len(offset) != 2 or not all(math.isfinite(v) for v in offset):
            raise ValueError('Finite parent-frame offset required')
        # Reflect AFTER restoring the parent source frame. A yaw alone cannot
        # represent this orientation: the lateral axis also changes handedness.
        return dict(origin_cm=(origin[0]+100*offset[0], -(origin[1]+100*offset[1]), origin[2]),
                    yaw_degrees=-yaw, source_yaw_degrees=source_yaw,
                    scale=(1.0, -1.0, 1.0), world_y_sign=-1)
    return dict(origin_cm=origin, yaw_degrees=yaw, source_yaw_degrees=source_yaw,
                scale=(1.0, 1.0, 1.0), world_y_sign=1)


def world_point_cm(frame, point_m):
    if len(point_m) != 3 or not all(math.isfinite(float(p)) for p in point_m):
        raise ValueError('Finite XYZ point required')
    x, y, z = (100*float(p)*s for p, s in zip(point_m, frame['scale']))
    a = math.radians(frame['yaw_degrees'])
    ox, oy, oz = frame['origin_cm']
    return (ox+math.cos(a)*x-math.sin(a)*y,
            oy+math.sin(a)*x+math.cos(a)*y, oz+z)
