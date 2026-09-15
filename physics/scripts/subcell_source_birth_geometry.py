"""Exact one-sided source geometry at zero water, not a wet-front solver.

Polynomials hold only before the first positive ORIGINAL elevation knot.
The scaled jet is (height*divergence, velocity_x, velocity_y). Its limiting
Gram retains vertical inertia even when divergence grows as 1/height; setting
the dry Gram to zero before taking this limit would discard that contribution.
No dry inverse mass, epsilon water, inferred bed or topology repair is used.
"""
from fractions import Fraction as F

from subcell_exact_geometry import SourceRelativeStorage, area
from subcell_source_face_section import SourceFaceSection


def add(polynomial, power, coefficient):
    polynomial[power] = polynomial.get(power, F(0))+coefficient
    if polynomial[power] == 0:
        del polynomial[power]


def value(polynomial, height, derivative=False):
    return sum((coefficient*(power*height**(power-1) if derivative else height**power)
                for power, coefficient in polynomial.items() if not derivative or power), F(0))


class SourceBirthGeometry:
    def __init__(self, storage):
        if not isinstance(storage, SourceRelativeStorage):
            raise ValueError('Original exact-source storage required for birth geometry')
        self.fragments = storage.fragments
        self.datum = storage.source_datum
        self.source_ids = tuple(sorted(set(int(f.source_id) for f in storage.fragments)))
        levels = {v[2]-self.datum for fragment in storage.fragments for v in fragment.polygon}
        self.next_height = min((z for z in levels if z > 0), default=None)
        self.moment_polynomials = [dict() for _ in range(4)]
        self.gram_polynomials = [[dict() for _ in range(3)] for _ in range(3)]
        for fragment in storage.fragments:
            slope = fragment.gradient
            for triangle in fragment.triangles:
                a, b, c = sorted(v[2]-self.datum for v in triangle)
                if a > 0:
                    continue
                projected = area(triangle)
                for k in range(4):
                    if c == 0:
                        terms = {k: projected}
                    elif b == 0:
                        # Two minimum vertices: trapezoid, including its cubic
                        # storage correction, not just a leading monomial.
                        terms = {k+1: 2*projected/(c*(k+1)),
                                 k+2: -2*projected/(c*c*(k+1)*(k+2))}
                    else:
                        terms = {k+2: 2*projected/(b*c*(k+1)*(k+2))}
                    for power, coefficient in terms.items():
                        add(self.moment_polynomials[k], power, coefficient)
                        if k == 3:
                            add(self.gram_polynomials[0][0], power, coefficient)
                        elif k == 2:
                            for axis in range(2):
                                cross = -F(3, 2)*coefficient*slope[axis]
                                add(self.gram_polynomials[0][axis+1], power, cross)
                                add(self.gram_polynomials[axis+1][0], power, cross)
                        elif k == 1:
                            for i in range(2):
                                for j in range(2):
                                    add(self.gram_polynomials[i+1][j+1], power, 3*coefficient*slope[i]*slope[j])
        self.volume_power = min(self.moment_polynomials[1])
        self.volume_coefficient = self.moment_polynomials[1][self.volume_power]
        if self.volume_power not in (1, 2, 3) or self.volume_coefficient <= 0:
            raise ValueError('Positive original one-sided storage coefficient required')
        self.scaled_gram_limit = tuple(tuple(
            self.gram_polynomials[i][j].get(self.volume_power+(i == 0)+(j == 0), F(0))/self.volume_coefficient
            for j in range(3)) for i in range(3))

    def check_height(self, height):
        try:
            height = F(height)
        except (ValueError, OverflowError, TypeError) as exc:
            raise ValueError('Finite nonnegative exact birth height required') from exc
        if height < 0 or (self.next_height is not None and height >= self.next_height):
            raise ValueError('Birth height must precede the first original positive source knot')
        return height

    def moments(self, height):
        """Right-continuous moments: at zero, M0 includes newly wet flat area.

        Actual dry water still has zero volume and zero kinetic Gram. M0 here
        is the one-sided geometric limit, not a declaration of positive water.
        """
        height = self.check_height(height)
        return tuple(value(p, height) for p in self.moment_polynomials)

    def gram(self, height):
        height = self.check_height(height)
        return tuple(tuple(value(p, height) for p in row) for row in self.gram_polynomials)

    def stage_rates(self, height, height_rate):
        """Right derivative in stage coordinates, including the flat wet area.

        At exactly zero a negative stage direction is outside the birth cone.
        There is deliberately no division by the vanishing dV/dheight.
        """
        height = self.check_height(height)
        try:
            rate = F(height_rate)
        except (ValueError, OverflowError, TypeError) as exc:
            raise ValueError('Finite exact stage direction required') from exc
        if height == 0 and rate < 0:
            raise ValueError('Negative direction leaves the one-sided birth cone')
        return tuple(value(p, height, True)*rate for p in self.moment_polynomials)

    def face_area_polynomial(self, section):
        """Exact newborn column area before face_next_height(section).

        This is the NEW side's area, not a harmonic/common-wet pressure area.
        A positive minimum along the face means no initial contact there.
        """
        if not isinstance(section, SourceFaceSection):
            raise ValueError('Original exact source face required')
        polynomial = {}
        for first, second in section.source_segments:
            a, b = sorted((first[1]-self.datum, second[1]-self.datum))
            width = second[0]-first[0]
            if a < 0:
                raise ValueError('Face lies below original receiving storage')
            if a > 0:
                continue
            if b == 0:
                add(polynomial, 1, width)
            else:
                add(polynomial, 2, width/(2*b))
        return polynomial

    def face_next_height(self, section):
        """A shared-face subdivision may introduce an earlier FACE knot."""
        if not isinstance(section, SourceFaceSection):
            raise ValueError('Original exact source face required')
        positive = [v[1]-self.datum for segment in section.source_segments for v in segment if v[1] > self.datum]
        if self.next_height is not None:
            positive.append(self.next_height)
        return min(positive, default=None)

    def scaled_face_divergence_limit(self, section):
        """lim(height * NEW-side column_area / volume); no pressure closure."""
        polynomial = self.face_area_polynomial(section)
        if polynomial and min(polynomial)+1 < self.volume_power:
            raise ValueError('Face area grows outside the original source storage geometry')
        return polynomial.get(self.volume_power-1, F(0))/self.volume_coefficient

    def face_contact(self, section):
        """Original stored volume before the receiving stage reaches a face.

        Contact requires a STRICTLY greater stage. A higher incoming edge need
        not touch the first wet patch at the source polygon's lowest point.
        This is a geometric threshold, not a travel-time or flux prescription.
        """
        if not isinstance(section, SourceFaceSection):
            raise ValueError('Original exact source face required')
        height = min(v[1]-self.datum for segment in section.source_segments for v in segment)
        if height < 0:
            raise ValueError('Face lies below original receiving storage')
        volume = sum((f.depth_moments(self.datum+height)[1] for f in self.fragments), F(0))
        return dict(height_above_source_minimum=height, stored_volume_before_face_opens=volume,
                    contact_starts_at_birth=height == 0)

    def record(self):
        # Rational strings preserve tiny original coefficients and exact datums;
        # converting to float first could erase a source fragment entirely.
        return dict(source_triangle_indices=self.source_ids, source_datum=str(self.datum),
            next_positive_source_height=None if self.next_height is None else str(self.next_height),
            volume_leading_power=self.volume_power, volume_leading_coefficient=str(self.volume_coefficient),
            depth_moment_polynomials=[{str(k): str(v) for k, v in p.items()} for p in self.moment_polynomials],
            scaled_jet_gram_limit=[[str(v) for v in row] for row in self.scaled_gram_limit],
            stage_inverse_derivative_singular_at_birth=self.volume_power > 1,
            full_pressure_or_front_flux_or_time_or_gameplay_accepted=False)
