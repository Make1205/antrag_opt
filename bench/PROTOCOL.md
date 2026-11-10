# Benchmark protocol

GCC -O3 -march=native with required backend flags; byte-form sk/pk inputs,
32-byte messages, unchanged Dilithium bba9534 timing files and median ticks/1000.
No extra ref auto-vectorization suppression unless required by upstream.
Cloud uses QUICK=1 only; FULL is local.


## Floating-point contraction rule (2026-11-10)

All builds that execute floating-point arithmetic, ref and AVX2 alike, must add
`-ffp-contract=off` to system GCC `-O3 -march=native` and required backend options.
This prevents compiler-generated fused multiply/add and preserves separate
binary64 rounding. It does not disable or rewrite explicit upstream FMA
intrinsics. Those are retained, named and counted separately; never remove
algorithm intrinsics just to obtain a zero count. FALCON_FMA is not changed by
this compiler policy. Integer-only paths do not need a contraction flag.

Every run checks benchmark-owned object files and the linked driver with
objdump (apt package binutils), saves per-build fma-audit JSON and reports counts
in SUMMARY. Expected count is zero unless a named original source object uses
explicit FMA intrinsics. Shared-library internals are outside this audit. Any
unexplained FMA causes the run to fail before timing. HAWK KeyGen/Sign are
integer/fixed-point, and LITHIUM's selected default exp path is integer; neither
is silently changed into another algorithm variant by this policy.

The local c-fn-dsa case 3462 (zero-based index 3461) established FP contraction
as the reason for the old mismatch, not an implementation defect: both signatures
cross-verified; disabling contraction removed 15 compiler-generated FMA
instructions and restored equality with ref for that case. c-fn-dsa now requires
ref/AVX2 byte equality and also retains all cross-verification checks. c-fn-dsa
is the paper's primary Falcon-family measurement; VecFalcon is the backup.
