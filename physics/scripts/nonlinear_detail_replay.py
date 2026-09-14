"""2-D finite-amplitude candidate replay on actual captured detail/mean fields.

Research reference, NOT installed gameplay. Fixed mean and wet mask, unforced
replay: not an exact reproduction of the moving, source-driven engine run.
Retains its rational finite-depth linear pressure and adds hydrostatic nonlinear
pressure/momentum plus mean strain. This hybrid is not a fully nonlinear
Green-Naghdi or overturning model. Reject invalid steps; never clip cell mass.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from audit_detail_wave_regime import read_snapshot
from detail_nonlinear_flux import G
from finite_depth_pressure_reference import LENGTHS, WEIGHTS


def neighbor(a, offset, axis):
    return np.roll(a, -offset, axis=axis)


class ReplayExhausted(RuntimeError):
    """Failed replay with its last admissible state, not a successful restart."""
    def __init__(self, reason, state, statistics, diagnostics):
        super().__init__(f'{reason} at {statistics["elapsed_s"]:.9g}s; no time/mass repair')
        self.state = state.copy()
        self.statistics = statistics
        self.diagnostics = diagnostics


class Replay:
    def __init__(self, flow, cell_m, *, nonlinear=True, dispersive=True,
                 periodic=False, pressure_iterations=40, damping=.6):
        self.flow = np.asarray(flow, dtype=float)
        if (self.flow.ndim != 3 or self.flow.shape[-1] != 4
                or not np.all(np.isfinite(self.flow)) or np.any(self.flow[..., 0] < 0)
                or not np.isfinite(cell_m) or cell_m <= 0
                or not 1 <= pressure_iterations <= 128 or damping < 0):
            raise ValueError('Invalid replay mean field or settings')
        self.h0, self.u = self.flow[..., 0], self.flow[..., 1:3]
        self.wet = self.h0 > .01
        if not np.any(self.wet):
            raise ValueError('No wet cells')
        self.dx, self.nonlinear, self.dispersive = cell_m, nonlinear, dispersive
        self.iterations, self.damping = pressure_iterations, damping
        self.pairs = []
        self.gradients = []
        for axis in (1, 0):  # x then y
            pair = self.wet & neighbor(self.wet, 1, axis)
            if not periodic:
                if axis == 1:
                    pair[:, -1] = False
                else:
                    pair[-1, :] = False
            self.pairs.append(pair)
            left = neighbor(pair, -1, axis)
            both = left & pair
            gradient = np.zeros_like(self.u)
            forward = (neighbor(self.u, 1, axis) - self.u) / cell_m
            backward = (self.u - neighbor(self.u, -1, axis)) / cell_m
            gradient[both] = .5 * (forward[both] + backward[both])
            gradient[pair & ~left] = forward[pair & ~left]
            gradient[left & ~pair] = backward[left & ~pair]
            self.gradients.append(gradient)
        degree = np.zeros_like(self.h0)
        for axis, pair in zip((1, 0), self.pairs):
            degree += pair + neighbor(pair, -1, axis).astype(float)
        self.alpha = LENGTHS[:, None, None] * (self.h0 / cell_m)**2
        self.diagonal = 1 + self.alpha * degree
        self.c = 1 - 1 / (1 + 4 * LENGTHS * (self.h0.max() / cell_m)**2)

    def pressure(self, eta):
        if not self.dispersive:
            return eta
        rhs = np.where(self.wet, eta, 0)
        previous = np.broadcast_to(rhs, self.alpha.shape).copy()
        older, rho = previous.copy(), self.c.copy()
        for iteration in range(self.iterations):
            total = np.zeros_like(previous)
            for grid_axis, pair in zip((1, 0), self.pairs):
                axis = grid_axis + 1  # leading Helmholtz-term dimension
                total += pair * neighbor(previous, 1, axis)
                total += neighbor(pair, -1, grid_axis) * neighbor(previous, -1, axis)
            jacobi = (rhs + self.alpha * total) / self.diagonal
            relaxation, momentum = np.ones(2), np.zeros(2)
            if iteration:
                nxt = 1 / (2 / self.c - rho)
                relaxation, momentum, rho = 2*nxt/self.c, nxt*rho, nxt
            current = previous + relaxation[:, None, None]*(jacobi-previous)
            current += momentum[:, None, None]*(previous-older)
            older, previous = previous, current
        return eta/15 + np.sum(WEIGHTS[:, None, None]*previous, axis=0)

    def slope(self, value, axis, pair):
        a, b = value-neighbor(value, -1, axis), neighbor(value, 1, axis)-value
        result = .5*(np.sign(a)+np.sign(b))*np.minimum(.5*abs(a+b), 2*np.minimum(abs(a), abs(b)))
        valid = pair & neighbor(pair, -1, axis)
        return np.where(valid[..., None], result, 0) if value.ndim == 3 else np.where(valid, result, 0)

    def rate(self, state):
        if state.shape != (*self.h0.shape, 3) or not np.all(np.isfinite(state)):
            raise ValueError('Invalid wave state')
        if np.any(state[~self.wet] != 0):
            raise ValueError('Nonzero detail outside fixed authoritative wet domain')
        h = self.h0 + state[..., 0]
        if np.any(h[self.wet] <= 0):
            raise ValueError('Nonpositive total depth; do not repair captured mass')
        pressure = self.pressure(state[..., 0])
        rate = np.zeros_like(state)
        signals = np.zeros_like(self.h0)
        for component, (axis, pair) in enumerate(zip((1, 0), self.pairs)):
            slope = self.slope(state, axis, pair)
            if self.nonlinear:
                # Limit reconstructed POLYNOMIAL slopes, not conserved cells.
                # Each face depth stays positive while its cell average/mass
                # is unchanged. All momentum slopes use the same factor.
                theta = np.minimum(1., np.divide(1.98*h, abs(slope[..., 0]),
                    out=np.ones_like(h), where=abs(slope[..., 0]) > 0))
                slope *= theta[..., None]
            a, b = state+.5*slope, neighbor(state-.5*slope, 1, axis)
            hl, hr = self.h0+a[..., 0], neighbor(self.h0, 1, axis)+b[..., 0]
            if self.nonlinear and (np.any(hl[pair] <= 0) or np.any(hr[pair] <= 0)):
                raise ValueError('Nonpositive reconstructed face depth')
            hl_safe, hr_safe = np.where(pair, hl, 1), np.where(pair, hr, 1)
            depth = np.where(pair, np.minimum(self.h0, neighbor(self.h0, 1, axis)), 0)
            u = .5*(self.u[..., component]+neighbor(self.u[..., component], 1, axis))
            fa, fb = u[..., None]*a, u[..., None]*b
            fa[..., 0] += a[..., component+1]
            fb[..., 0] += b[..., component+1]
            ps = self.slope(pressure, axis, pair)
            pa, pb = pressure+.5*ps, neighbor(pressure-.5*ps, 1, axis)
            fa[..., component+1] += G*depth*pa
            fb[..., component+1] += G*depth*pb
            if self.nonlinear:
                fa[..., 1:] += a[..., component+1, None]*a[..., 1:]/hl_safe[..., None]
                fb[..., 1:] += b[..., component+1, None]*b[..., 1:]/hr_safe[..., None]
                fa[..., component+1] += .5*G*a[..., 0]**2
                fb[..., component+1] += .5*G*b[..., 0]**2
                speed = np.maximum(abs(u+a[..., component+1]/hl_safe)+np.sqrt(G*np.maximum(hl_safe, 0)),
                                   abs(u+b[..., component+1]/hr_safe)+np.sqrt(G*np.maximum(hr_safe, 0)))
            else:
                speed = abs(u)+np.sqrt(G*depth)
            flux = np.where(pair[..., None], .5*(fa+fb)-.5*speed[..., None]*(b-a), 0)
            rate -= (flux-neighbor(flux, -1, axis))/self.dx
            # Owning-cell hydrostatic balance, matching the fixed wet graph.
            balance = G*(depth-neighbor(depth, -1, axis))*pressure
            if self.nonlinear:
                balance += .5*G*(pair.astype(float)-neighbor(pair, -1, axis))*state[..., 0]**2
            rate[..., component+1] += balance/self.dx
            signals += np.maximum(np.where(pair, speed, 0), neighbor(np.where(pair, speed, 0), -1, axis))
        rate[..., 1:] -= state[..., 1, None]*self.gradients[0] + state[..., 2, None]*self.gradients[1]
        maximum = float(signals.max())
        cfl_step = .4*self.dx/maximum if maximum else np.inf
        draining = self.wet & (rate[..., 0] < 0)
        drain_step = float(np.min(.95*h[draining]/-rate[..., 0][draining])) if np.any(draining) else np.inf
        self.last_bounds = dict(cfl_step_s=cfl_step, draining_step_s=drain_step)
        return rate, min(cfl_step, drain_step)

    def diagnostics(self, state, rate, dt, bounds, last_rejection):
        h = self.h0 + state[..., 0]
        y, x = np.unravel_index(np.argmin(np.where(self.wet, h, np.inf)), h.shape)
        velocity = self.u + np.divide(state[..., 1:], h[..., None],
            out=np.zeros_like(self.u), where=self.wet[..., None])
        return dict(attempted_step_s=dt,
            bounds={key: value if np.isfinite(value) else None for key, value in bounds.items()},
            last_rejection=last_rejection,
            maximum_relative_momentum_m2ps=float(np.linalg.norm(state[..., 1:], axis=-1).max()),
            maximum_total_speed_mps=float(np.linalg.norm(velocity[self.wet], axis=-1).max()),
            shallowest_cell=dict(x=int(x), y=int(y), mean_depth_m=float(self.h0[y, x]),
                total_depth_m=float(h[y, x]), state=state[y, x].tolist(),
                mean_velocity_mps=self.u[y, x].tolist(), rate=rate[y, x].tolist()))

    def advance(self, state, seconds, max_step=1/120, max_trials=100000):
        state = np.asarray(state, dtype=float).copy()
        initial_volume = float(state[..., 0].sum()*self.dx**2)
        elapsed, accepted, rejected = 0., 0, 0
        smallest = max_step
        if (not np.isfinite(seconds) or seconds < 0 or not np.isfinite(max_step)
                or max_step <= 0 or max_trials < 1):
            raise ValueError('Invalid replay interval')
        def statistics():
            return dict(elapsed_s=elapsed, accepted_steps=accepted, rejected_trials=rejected,
                smallest_step_s=smallest, initial_signed_volume_m3=initial_volume,
                signed_volume_error_m3=float(state[..., 0].sum()*self.dx**2-initial_volume),
                minimum_total_depth_m=float(np.min((self.h0+state[..., 0])[self.wet])),
                maximum_abs_eta_m=float(np.max(abs(state[..., 0]))))
        while elapsed < seconds:
            first, bound = self.rate(state)
            bounds = self.last_bounds.copy()
            dt = min(max_step, seconds-elapsed, bound)
            last_rejection = None
            while True:
                if accepted+rejected >= max_trials or dt < 1.e-9:
                    reason = 'Trial budget exhausted' if accepted+rejected >= max_trials else 'Admissible timestep below 1e-9s'
                    raise ReplayExhausted(reason, state, statistics(),
                        self.diagnostics(state, first, dt, bounds, last_rejection))
                try:
                    stage = state+dt*first
                    second, stage_bound = self.rate(stage)
                    if dt > stage_bound*(1+1e-12):
                        raise ValueError('RK stage CFL/draining bound')
                    candidate = .5*(state+stage+dt*second)
                    if np.any((self.h0+candidate[..., 0])[self.wet] <= 0) or not np.all(np.isfinite(candidate)):
                        raise ValueError('Invalid candidate')
                    break
                except ValueError as error:
                    last_rejection = str(error)
                    dt *= .5
                    rejected += 1
            candidate[..., 1:] *= np.exp(-self.damping*dt)
            state, elapsed = candidate, elapsed+dt
            accepted += 1
            smallest = min(smallest, dt)
        return state, statistics()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshot', type=Path)
    parser.add_argument('--seconds', type=float, default=1.)
    parser.add_argument('--linear', action='store_true')
    parser.add_argument('--max-trials', type=int, default=2000,
                        help='Research compute bound; exhaustion is a failure, not accepted progress')
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    metadata, arrays, hashes = read_snapshot(args.snapshot)
    replay = Replay(arrays['flow'], metadata['cell_m'], nonlinear=not args.linear)
    initial = arrays['state'][..., :3]
    report = dict(schema='raftsim.nonlinear_fixed_mean_replay.v2', scene_accepted=False,
        integrated=False, source_hashes=hashes, nonlinear=not args.linear,
        scope=__doc__, requested_seconds=args.seconds)
    try:
        final, stats = replay.advance(initial, args.seconds, max_trials=args.max_trials)
        report.update(completed=True, statistics=stats)
        output = args.report.with_suffix('.state.npy')
        with output.open('xb') as stream:
            np.save(stream, final)
        report['final_state'] = str(output.resolve())
    except ReplayExhausted as error:
        report.update(completed=False, error=str(error), statistics=error.statistics,
                      failure_diagnostics=error.diagnostics)
        output = args.report.with_suffix('.failed-state.npy')
        with output.open('xb') as stream:
            np.save(stream, error.state)
        report['last_admissible_state_not_completed'] = str(output.resolve())
    except (ValueError, RuntimeError) as error:
        report.update(completed=False, error=str(error))
    with args.report.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
