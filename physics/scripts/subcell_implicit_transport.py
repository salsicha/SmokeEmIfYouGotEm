"""Frozen-donor coupled transport research control on exact cell/face geometry.

Backward Euler transports volume and momentum through the SAME face generator.
No depth clipping, post-solve rescale or tiny-cell deletion. Hydrostatic pressure
and bed force remain explicit and therefore UNQUALIFIED for large timesteps.
This dissipative first-order base is not the full two-pole river solver.
Dense matrices are a small-patch reference, never a native performance claim.
"""
import numpy as np


def frozen_system(patch, volumes, momenta, gravity=9.81):
    volume, momentum = np.asarray(volumes, float), np.asarray(momenta, float)
    if (volume.shape != patch.shape or momentum.shape != (*patch.shape, 2)
            or not np.isfinite(volume).all() or not np.isfinite(momentum).all()
            or (volume < 0).any() or np.any(momentum[volume == 0] != 0)
            or not np.isfinite(gravity) or gravity <= 0):
        raise ValueError('Finite physical state and positive gravity required')
    volume, momentum = volume.ravel(), momentum.reshape(-1, 2)
    count = len(volume)
    stages = np.array([cell.relative_stage_for_volume(v) if patch.relative_stages else cell.stage_for_volume(v)
                       for cell, v in zip(patch.cells, volume)])
    datums = np.array([cell.datum if patch.relative_stages else 0. for cell in patch.cells])
    velocity = np.divide(momentum, volume[:, None], out=np.zeros_like(momentum), where=volume[:, None] > 0)
    generator = np.zeros((count, count))
    wall_loss = np.zeros((count, 2))
    pressure = np.array([cell.hydrostatic_bed_force(eta, gravity, patch.relative_stages)
                         for cell, eta in zip(patch.cells, stages)])
    maximum_speed = 0.
    for left, right, axis, section in patch.faces:
        li = right if left < 0 else left
        ri = left if right < 0 else right
        ul, ur = velocity[li].copy(), velocity[ri].copy()
        if left < 0: ul[axis] *= -1
        if right < 0: ur[axis] *= -1
        al, i2l, _ = section.moments(stages[li], datums[li])
        ar, i2r, _ = section.moments(stages[ri], datums[ri])
        _, speed = section.flux(stages[li], ul, stages[ri], ur, axis, gravity, datums[li], datums[ri])
        maximum_speed = max(maximum_speed, speed)
        outgoing_left = .5*(speed+ul[axis])*al
        outgoing_right = .5*(speed-ur[axis])*ar
        force = .25*gravity*(i2l+i2r)
        if left >= 0: pressure[left, axis] -= force
        if right >= 0: pressure[right, axis] += force
        if left >= 0 and right >= 0:
            for owner, other, outgoing in ((left, right, outgoing_left), (right, left, outgoing_right)):
                if volume[owner] == 0:
                    if outgoing != 0:
                        raise ValueError('Exactly dry cell cannot donate')
                    continue
                rate = outgoing/volume[owner]
                generator[owner, owner] -= rate
                generator[other, owner] += rate
        else:
            owner = li
            outgoing = outgoing_right if left < 0 else outgoing_left
            if volume[owner] > 0:
                # Reflecting ghost returns all mass and tangential momentum;
                # its normal momentum is reversed, giving a factor of two.
                wall_loss[owner, axis] += 2*outgoing/volume[owner]
    wave_limit = .5*float(patch.spacing.min())/maximum_speed if maximum_speed > 0 else np.inf
    return generator, wall_loss, pressure, wave_limit


def advance(patch, volumes, momenta, duration, gravity=9.81):
    if not np.isfinite(duration) or duration <= 0:
        raise ValueError('Positive finite duration required')
    generator, wall_loss, pressure, limit = frozen_system(patch, volumes, momenta, gravity)
    if duration > limit:
        raise ValueError('Duration exceeds grid wave bound; pressure remains explicit')
    matrix = np.eye(generator.shape[0])-duration*generator
    before_v, before_p = np.asarray(volumes).ravel(), np.asarray(momenta).reshape(-1, 2)
    volume = np.linalg.solve(matrix, before_v)
    momentum = np.empty_like(before_p)
    for axis in (0, 1):
        operator = matrix+np.diag(duration*wall_loss[:, axis])
        momentum[:, axis] = np.linalg.solve(operator, before_p[:, axis]+duration*pressure[:, axis])
    if (not np.isfinite(volume).all() or not np.isfinite(momentum).all() or (volume < 0).any()
            or np.any(momentum[volume == 0] != 0)):
        raise ValueError('Implicit update rejected; no state repair: '
            f'minimum_volume={float(volume.min()):.17g}, negative_cells={int((volume < 0).sum())}, '
            f'nonfinite_volumes={int((~np.isfinite(volume)).sum())}, '
            f'nonfinite_momenta={int((~np.isfinite(momentum)).sum())}, '
            f'nonzero_dry_momenta={int((momentum[volume == 0] != 0).sum())}')
    if abs(float(volume.sum()-before_v.sum())) > 1e-10:
        raise ValueError('Implicit volume conservation failed; no rescale')
    return volume.reshape(patch.shape), momentum.reshape((*patch.shape, 2))
