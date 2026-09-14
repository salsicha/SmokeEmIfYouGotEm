"""Exact last-wet-interval drain event for fixed outgoing donor velocities.

An isolated cell with NO incoming water and frozen nonnegative face weights.
Not a pressure update, a coupled solver, or permission to delete thin water.
This oracle distinguishes finite geometric extinction from asymptotic drainage.
"""
import numpy as np


class LowestWetDrain:
    def __init__(self, storage, weighted_sections):
        self.datum = float(storage.levels.min())
        levels = storage.levels-self.datum
        self.wet_coefficients = np.zeros(3)
        self.outflow_coefficients = np.zeros(2)
        knots = list(levels[levels > 0])
        for (low, middle, high), area in zip(levels, storage.areas):
            if low != 0:
                continue
            if high == 0:
                self.wet_coefficients[0] += area
            elif middle == 0:
                self.wet_coefficients[1] += 2*area/high
                self.wet_coefficients[2] -= area/(high*high)
            else:
                self.wet_coefficients[2] += area/(middle*high)
        for weight, section in weighted_sections:
            if not np.isfinite(weight) or weight < 0:
                raise ValueError('Finite nonnegative outgoing coefficient required')
            if weight == 0:
                continue
            heights = section.levels-self.datum
            if (heights < 0).any():
                raise ValueError('Face below the original cell minimum')
            knots.extend(heights[heights > 0])
            for (low, high), length in zip(heights, section.lengths):
                if low != 0:
                    continue
                if high == 0:
                    self.outflow_coefficients[0] += weight*length
                else:
                    self.outflow_coefficients[1] += weight*length/(2*high)
        self.ceiling = float(min(knots)) if knots else np.inf

    def moments(self, depth_above_minimum):
        d = float(depth_above_minimum)
        if not np.isfinite(d) or d < 0 or d > self.ceiling:
            raise ValueError('Stage outside the exact lowest wet interval')
        w0, w1, w2 = self.wet_coefficients
        a, b = self.outflow_coefficients
        return d*(w0+d*(w1/2+d*w2/3)), w0+d*(w1+d*w2), d*(a+d*b)

    def extinction_time(self, depth_above_minimum):
        """Integral_0^depth wet_area(x)/outflow(x) dx, seconds; may be infinite."""
        _, _, _ = self.moments(depth_above_minimum)
        d = float(depth_above_minimum)
        if d == 0:
            return 0.
        w0, w1, w2 = self.wet_coefficients
        a, b = self.outflow_coefficients
        if w0 > 0 or (a == 0 and (b == 0 or w1 > 0)):
            return np.inf
        if a == 0:
            return w2*d/b
        if b == 0:
            return d*(w1+w2*d/2)/a
        t = b*d/a
        # Positive-interval rational integral. Avoid t-log1p(t) cancellation.
        if t < 1e-3:
            l = sum((-t)**n/(n+1) for n in range(12))
            r = sum((-t)**n/(n+2) for n in range(12))
        else:
            l = np.log1p(t)/t
            r = (t-np.log1p(t))/(t*t)
        return d/a*(w1*l+w2*d*r)

    def drain(self, depth_above_minimum, duration):
        """Exact isolated finite-event outflow; return remaining/drained volume.

        No depth threshold. Infinite-time drainage is rejected, not truncated.
        Incoming flux, evolving weights, pressure and momentum are NOT modeled.
        """
        if not np.isfinite(duration) or duration < 0:
            raise ValueError('Finite nonnegative duration required')
        original = self.moments(depth_above_minimum)[0]
        if duration == 0:
            return original, 0.
        time = self.extinction_time(depth_above_minimum)
        if not np.isfinite(time):
            raise ValueError('No finite isolated extinction event')
        if duration >= time:
            return 0., original
        low, high, target = 0., float(depth_above_minimum), time-duration
        for _ in range(128):
            middle = (low+high)/2
            if middle == low or middle == high:
                break
            if self.extinction_time(middle) < target:
                low = middle
            else:
                high = middle
        remaining = self.moments((low+high)/2)[0]
        return remaining, original-remaining
