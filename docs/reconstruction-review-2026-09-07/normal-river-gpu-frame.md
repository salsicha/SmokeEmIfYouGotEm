# Accepted GPU frame connected to the shared presentation path — September 13

Previous goal turn was progress: bounded interval advancement was implemented
and verified, not merely polled. This turn bridges its completed state to the
existing material/raft-contact presentation queue. It does not enable the new
solver in the normal scenario or claim visible water/FPS acceptance.

## Implementation

`RaftSimResolveTotalDepthFrameGPU` derives offset, slopes and bounded foam
coverage from the same accepted total state and paired bed/carrier reference.
It emits a float4 Nx-by-(Ny+1) texture with the existing registration record
at metadata pixel0. Pixel1 carries accepted GPU time hi/lo, zero remaining
interval and schema marker2. All other metadata pixels retain registration.
This avoids estimating adaptive accepted time from CPU scheduled trial counts.

Before resolving the texture it checks finite/nonnegative state, momentum in
dry cells, finite wet velocity, finite reference and derived surface, completed
interval status, zero remaining time, finite clock and trial diagnostics.
Incomplete, failed or invalid candidates have invalid registration (w=0) and
must never be published. Their zero output pixels are not fallback water.
No state clipping, equation changes or tolerance changes were introduced.

The existing `FRaftSimDetailFrameReadback` now has an explicit GPU-clock option.
It reads the clock from the same padded texture payload before publishing the
immutable frame to `FRaftSimDetailFrameMailbox`. A GPU-clock frame's validation
checks that its simulation time still exactly matches its own metadata; a
finite but stale host time is invalid. Existing callers default to the old
fixed-step clock behavior, preserving normal-play compatibility. Readback
polling remains nonblocking; GPU waits exist only in the native test.

New files: `RaftSimTotalDepthFrameGPU.h/.cpp`, `RaftSimTotalDepthFrame.usf`,
and RaftSimRaft's `RaftSimTotalDepthFrameTest.cpp`. Existing presentation-frame
and readback headers contain the small production bridge changes.

## Verification scope

Build34346 succeeded77.81s; final sampler-parity assertion build85521 succeeded
14.15s. The new actual-D3D12 test starts with native bounded FV/pressure/RK
advancement, resolves its texture, uses the production readback/mailbox path,
then reuploads the immutable payload and invokes the actual material sampler.
It compares that sampler with CPU raft-contact sampling, including outside,
fractional and far-data-edge queries. The host time is deliberately77s while
the GPU time is1048576s plus its accepted increment.

Eleven cases cover completed movement, pending interval, fatal pressure input,
trial exhaustion, nonfinite reference, negative state, projection overflow,
finite state with overflowing velocity, nonzero remaining time, nonfinite
clock, and an already complete interval with no accepted steps. Invalid cases
must fail the production readback and leave the mailbox empty. Tampered finite
clock or remaining-time metadata must fail immutable-frame validation.
Independent CPU projection comparison retains2e-6 and material/contact parity
retains1e-6; neither is scene or physics-evolution acceptance.

Initial full native37342 CLOSED exit1 on an RDG ownership assertion: the
resolver attempted final texture access before the caller queued extraction.
The resolver now leaves the texture graph-local; the caller explicitly queues
extraction with SRVMask. Failed log retained. Corrected build53347 succeeds
14.78s. Single native30330 CLOSED1clean pass,0.215939403s:
`unreal/Saved/RaftSimValidation/south-fork-total-frame-gpu-v2-20260913/index.json`.
Both valid cases have286 reuploaded material/contact queries with EXACT zero
error, including far data edge and outside points. Derived surface maximum
error1.1920929e-7. All9 invalid/incomplete cases refused publication with the
expected diagnostic category. No state/physics/visual tolerance was changed.

Current shader SHA256:
`fc39055ebda7d433940876bddff2e4e6a9575e46a1b2d6f1784a84075d76c68a`.
Raft DLL SHA256:
`a72934ea456234030ee335019e4e6a8eb88d31e59310b2fff2d2ab23272ea6ec`.
Water-detail DLL SHA256:
`eb421c28b0eaee934db038cc4f7158ef3c61788f7448966d55c83077b9f74358`.

Final full native66112 CLOSED exit0:73clean passes, zero warnings/failures/unrun,
15.883719s. Report:
`unreal/Saved/RaftSimValidation/south-fork-total-frame-regressions-v2-20260913/index.json`.
The existing legacy completed-frame/contact test also passes with its original
host-clock behavior. Map/material/career-save hashes rechecked unchanged.
Tracked scoped diff whitespace checks pass; no whole-worktree LFS check or
release qualification is claimed. No commit made while the goal is unfinished.

## Still unfinished

The new total-state solver is not the normal game's state owner. Physical open
boundaries, authoritative bed/mean uploads outside diagnostics, conservative
mean/window exchange, breaking/froth generation/transport, and live interval
scheduling/ownership still need integration. Bounded-controller inactive slots
still schedule kernels; no whole-water-budget qualification or new FPS capture
is claimed. No CPU PDE changes or new long replay occurred this turn. The
prior17.017m/s hybrid replay peak remains physically unresolved. Latest normal
play21.571211FPS/p9552.6052ms still fails30FPS/33.333ms.

Cook96057/PID29104 remains live without restart. Both3700s/local34000 independent
state/artificial-bank audits pass:5,382,400 finite cells,86,720 exactly dry
artificial-face cells, volume2,908,523.140634853m3 and max step residual
1.649971937e-8m3. Outlet88.161592 versus inlet45.306955m3/s still indicates
settling; runtime600s is unchanged. Next3800/local36000 needs both audits after
the complete marker. Terrain/rapid evidence, normal scene motion, all later
rivers, crew, release and final commit remain open; the goal stays active.
Final live observation3723s/local34460; same cook handle retained.
