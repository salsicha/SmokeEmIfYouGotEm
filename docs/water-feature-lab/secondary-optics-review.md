# Secondary-phase modeling and optics

## Primary-method review

Read sections 4.3 and 4.7 of
[Kohl, Visual Enhancement of Liquid Simulations using Secondary Particles (2017)](https://ge.in.tum.de/download/2017-B.Sc_.-Thesis-kohl.pdf),
printed pages 17..19 and 25..26. The method generates samples per eligible
fluid cell and timestep using potential values and adjustable sampling rates.
It renders secondary material through density textures with volume scattering
and absorption, distinguishing spray from foam/bubbles. Its samples are not a
measured distribution of individual physical bubble radii. These statements
describe the thesis, not proof that the installed Blender implementation is
identical. PDF figure screenshot retrieval failed, so no figure comparison
or claimed reproduction of the paper's images was performed.

## Local observations and next implementation target

The current laboratory preview renders foam/bubbles as white sphere points
with assumed millimetre-scale radii; spray is dielectric water. Keeping those
radii fixed as simulation resolution increases greatly increases coverage.
The low-tailwater wave has 153,633 foam samples at resolution 80 and 793,010
at 120 at frame 192, alongside differing hydraulics. This is not a clean
optical-only convergence experiment, but is enough to reject the claim that
more particles automatically improve accuracy.

The next optics experiment should use a fixed cached flow and retain all
samples while comparing separate surface-foam, submerged-aeration and spray
representations. Any density reconstruction needs explicit units, kernel
normalization, integrated weights, phase bounds and an optical scale test.
An arbitrary opacity reduction is not air-volume calibration. Do not silently
reclassify solver samples, delete dense regions, paint moving water white, or
present a volume-rendered beauty result as resolved bubble physics.

The boil control has zero secondary particles before and through its small
piston pulse, demonstrating that the pipeline does not add whitewater merely
because a surface moves. Its white reflection strip is lighting, not foam.
