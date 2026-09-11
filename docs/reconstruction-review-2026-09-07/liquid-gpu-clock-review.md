# Actual simulation time for live surface effects

September 9, bounded South Fork continuation. This completes the clock
prerequisite for current-surface foam; it does not implement that foam yet.

The live reconstruction callback can run while the simulation is frozen. The
earlier actual-GPU probe observed 750 reconstruction callbacks, only 709 with
Niagara's simulation-tick flag and 41 render-only callbacks. That boolean is
not elapsed simulation time, and buffer swaps count particle-writing stages,
not seconds. Advecting foam by 1/60 s on every callback would be incorrect.

## GPU-carried age

The transient foam system now writes its actual `Emitter.Age` into unused
SimRT B/A channels as whole and fractional seconds. The fraction is explicitly
rounded to a 1/2048 s binary grid before half-float storage. Both stored
components are then exactly representable in the bounded review interval;
decoded age error is at most 1/4096 s. This is bounded diagnostic metadata, not
an arbitrary-duration production clock. The inherited optical candidate always
derives normals from SDF.r, rather than these metadata channels.

Distance reconstruction now preserves G/B/A, not just G. Its actual-GPU test
has nonzero varying auxiliary channels and checks their half-float values
through all five plane/empty/full cases. The surface remains one SimRT/one
visible carrier; particle and solver state are unchanged.

`RaftSimRecordLiquidClockGPU` records age, delta from the preceding record,
reset indication and the diagnostic tick flag into a bounded persistent GPU
timeline. It reads the actual current surface, not game-thread wall time or an
assumed frame number. The timeline is read back only at stop. Negative age
changes are marked as reset, not treated as positive advection time. Actual
reset behavior still needs a dedicated fixture before foam history uses it.

## Retained failure

The first live run, `liquid-gpu-age-clock-12s`, completed without engine errors
but failed its predeclared 0.00025 s age-error gate: decoded final age was
11.9995117 s versus independently logged simulation age 11.999989 s, an error
of 0.0004773 s. The native typed UAV store truncated the arbitrary fraction.
The explicit binary-grid rounding fixes the encoding; the gate was not widened.

## Corrected actual-engine result

`liquid-gpu-age-quantized-12s/clock_audit.json` passes:

- 750 GPU records, with 709 positive time deltas and 41 render-only records.
- First decoded age 0.100097656 s; final age 12.0 s.
- Final independently logged age 11.999989 s: 0.000011 s difference.
- Summed deltas 11.899902344 s, exactly equal to final minus initial GPU age.
- Maximum delta 0.033203125 s, capturing elapsed time across batched updates.
- Last 32 callbacks have unchanged age and zero elapsed time.
- Every displayed surface sample carries the final clock exactly; no reset
  events or engine error lines in this run.

Separate live-particle and occupancy audits also pass: 71,045 particles,
maximum packing error 0.001488 mm, 30 distinct motion images, zero diagnostics,
exact independent boundary classification, zero new water in non-fluid cells,
zero displayed-distance sign mismatch and CPU support/phi error below 4.77e-7.
This is not photorealism or physical acceptance. The diagnostic surface still
looks cyan/plastic, weakly frothy and bounded by rectangular fixture edges.

85 numerical liquid tests pass. The expanded engine regression result is
recorded in the final checkpoint. Saved source system/map/project hashes remain
unchanged. No production promotion, commit or new river cook occurred.

## Next action

Implement persistent foam evolution against the current reconstructed SDF,
using the recorded GPU age difference for advection/decay, and resetting history
on actual time reset. Preserve history without evolution on zero-delta renders.
Sample current solver velocity and classify source regions on the same surface
that is rendered. Validate transport, surface placement, pause/reset behavior
and actual motion before comparing real-reference whitewater appearance again.
Do not repeat the completed callback-count probe or treat it as the clock.
