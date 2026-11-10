# Antrag benchmark notes

## Repository and baseline

Repository: https://github.com/Make1205/antrag_opt (fork of mti/antrag_opt).
Baseline: `ccca2c6a627973827abc8479f1c32ebf6926b15f`.
Initial branch: `work`; initial working tree: clean.
The `bench` branch was created directly from this baseline. All changes are confined to `bench/`.

## Timing source

The four files `cpucycles.c`, `cpucycles.h`, `speed_print.c` and `speed_print.h`
are copied byte for byte from `ref/test/` in https://github.com/pq-crystals/dilithium
at `bba9534a3c5cbef66481cd6518d786e23ae601b5` (`bba9534`).
That revision has `ref/test/` and `avx2/test/`, rather than a root `test/` directory.
The reference implementation supplies the canonical files used here.
No edits were made to these four files.

SHA-256:

| File | SHA-256 |
|---|---|
| cpucycles.c | 31cc4c16b1e896b2cf7cc154aa21430329c0047cf9898a1865f9bfe9904f25e4 |
| cpucycles.h | 7f1e2b68cf3e3c76076364af3c5350de61442450c477aec809da8de10e131838 |
| speed_print.c | 533fc7bd12204078a5390cfb58c05d550b214850876609f8e98f7377b9d4f1b3 |
| speed_print.h | 3946b0226c63125664eb443a20d43563e6d1ba7fa3be5c1b952cd29d1477b2ef |

The default counter is RDTSC. `USE_RDPMC` will not be enabled.
`print_results` computes adjacent timestamp differences, subtracts measured counter
overhead and reports a median. In particular, 10001 input timestamps yield 10000
intervals. The driver passes 10002 timestamps for 10001 operations, so the unchanged printer
uses 10001 intervals. Timings are divided by 1000 for thousand-cycle output.

## Parameters and paper sizes

The ten active parameter sets were evaluated with the unchanged
`scripts/gen_headers.sage` and SageMath 10.6. Generated headers are stored in
`params/<set>/`; `params.sha256.json` verifies them before each run. No coefficients,
moduli or parameter values were edited. Commented-out candidates are excluded.

| Set | n | q | pk bytes | sk bytes | sig bytes |
|---|---:|---:|---:|---:|---:|
| 1f | 512 | 12289 | 896 | 59392 | 642 |
| 1s | 512 | 3583 | 768 | 59392 | 592 |
| 2f | 648 | 9721 | 1134 | 75168 | 812 |
| 2s | 648 | 3889 | 972 | 75168 | 768 |
| 3f | 768 | 18433 | 1440 | 89088 | 1002 |
| 3s | 768 | 3329 | 1152 | 89088 | 908 |
| 4f | 864 | 10369 | 1512 | 100224 | 1090 |
| 4s | 864 | 2593 | 1296 | 100224 | 1006 |
| 5f | 1024 | 12289 | 1792 | 118784 | 1282 |
| 5s | 1024 | 5119 | 1664 | 118784 | 1244 |

All successful signature encodings have the fixed size shown above.
`encode_sig` can reject a vector that does not fit. The driver follows the
repository codec test and repeats signing until encoding succeeds. Key material,
parameter values, sampling and RNG byte generation remain unchanged.

The user accepted the following discrepancies before benchmark implementation:

| Set | Repository n/q, pk/sig | Paper n/q, pk/sig |
|---|---|---|
| 1s | 512/3583, 768/592 | 512/3329, 768/591 |
| 3s | 768/3329, 1152/908 | 768/3329, 1152/883 |
| 5s | 1024/5119, 1664/1244 | 1024/3329, 1536/1176 |

Only 3s has q=3329. The q=12289 sets are 1f and 5f. All ten sets are measured.
The paper column uses the user's Table 2 / Table 3(b) numbers; other rows use `--`.
An earlier inventory-only SUMMARY is retained as a historical checkpoint.

## Build configurations

The original `falcon/config.h` enables `FALCON_AVX2=1`, `FALCON_FMA=1` and
`FALCON_KG_CHACHA20=1`. AVX2 uses that configuration unchanged. The external
`bench/config_ref.h` first includes the original configuration and then changes
only the AVX2 and FMA macros to zero. GCC preincludes this header for ref.
Header guards prevent later inclusion from overriding these selections.
Algorithm source files are byte-identical staged copies; no tracked files outside
`bench/` are edited. No source compatibility patches were necessary.

Both use system `/usr/bin/gcc -O3 -march=native -DNDEBUG -std=gnu11` and
link `-lm -lgmp`. `-DNDEBUG` matches the repository build. Ref adds
`-fno-tree-vectorize -fno-tree-slp-vectorize` to disable automatic vectorization
and compiles out the upstream SIMD intrinsics. Portable scalar C operations
still compile to the host's native scalar floating-point instructions.
Both use the repository's native `double` implementation and libm `sqrt`.
The commented software-emulation options do not provide a separate validated
Antrag backend. AVX2/FMA covers vector polynomial arithmetic and the PRNG.

LTO and debug flags from the original Makefile are omitted; neither is required
for correctness. The explicit test links include all algorithm objects because,
without LTO, the original poly-test link misses references to the NTT helpers.
No source edits were needed for this link correction. Inherited conda compiler
search variables are removed for subprocesses, and inherited CFLAGS/LDFLAGS
are not used. Every exact command is retained in a build log.

## Timing boundaries

Messages contain 32 bytes. Each operation runs 10001 times. The timestamp at
the start of each operation and one final timestamp give 10001 intervals to
the unchanged Dilithium `print_results` function. Its overhead subtraction and
median implementation are used directly. No driver-specific cycle estimator
or timer replacement is used. Values are RDTSC ticks / 1000.
The loop dispatch and timestamp-loop overhead are included. Inputs are warm;
Verify repeatedly checks the same valid message/signature. No LTO is used,
so calls to the separately compiled algorithm cannot be eliminated by whole-program
optimization. Timing is pinned to one allowed logical CPU; no privileged
frequency or scheduler changes are attempted.

* KeyGen generates the key and encodes both sk and pk to bytes.
* Sign decodes the byte sk, signs and encodes the signature, including retries
  after encoding overflow.
* Verify decodes the byte pk and byte signature and verifies the signature.
* Expanded-key Sign uses the in-memory secret key and includes signature encoding
  and encoding retries; it excludes byte-sk decoding.

The byte sk already serializes four integer vectors and fourteen precomputed
double vectors. `decode_sk` restores expanded material; it does not recompute
key generation. This is the repository's byte-key API semantics. Encoding retries
are necessary because SUPERCOP's wrapper ignores encoding failure, whereas the
repository codec test handles it. The driver checks failures explicitly.

## Correctness

No upstream KAT runner or expected-output fixtures were found. Both configurations
run the existing NTT, polynomial/FFT and RNS test programs for every parameter set.
For each set/build, the driver initializes the existing global PRNG through
`inner_shake256_*` and `Zf(prng_init)` using an 8-byte seed: little-endian
32-bit domain followed by little-endian 32-bit case index. Domain 1 generates
100 distinct key/signature cases; messages are byte j = (case+j) mod 256.
The original randombytes/get64/get8 functions and PRNG implementations are used.
No RNG function is replaced, and the time-based `seed_rng` is not invoked.

Each generated signature is self-verified and then verified by the other build.
The receiver also signs with the sender's serialized sk and checks that signature,
and rejects the original signature with a changed message. Each build verifies
100 foreign signatures and 100 signatures from foreign serialized keys per set.
Python compares all 100 pk/sk/signature byte records and reports exact equality
counts. Correctness must finish for all sets before any timing begins.

FMA changes floating-point rounding, so serialized expanded keys and signatures
can differ for the same seed. Byte differences are recorded, rather than hidden.
Cross-verification is the required interoperability check in that case. The
original Falcon configuration itself documents this FMA rounding distinction.
Domains 2, 3 and 4 separate foreign-key tests, timings and length statistics.
Domain 3 seeds each timing process once; RNG state then advances normally.

## Unpadded length statistics

For each of 1s/3s/5s and each build, domain 4 generates one key followed by
10000 successfully encoded signatures on a 32-byte zero message. Every signature
is verified. Failed encodings are retried and counted separately; the mean is
conditional on successful encoding under the repository's fixed-size format.
The count of signing attempts and encoding rejections is retained in lengths.json.

The driver parses the actual emitted coefficient bitstream to find the bit after
the final unary terminator. It rounds that bit count up to bytes and adds SALT_BYTES.
It checks the result independently against the decoded coefficient formula
`sum(SIG_SMALL_BITS + 2 + (abs(centered_coefficient) >> SIG_SMALL_BITS))`.
Whole padding bytes are excluded; the final partial data byte and the salt are
included. Trailing zero data bytes are never stripped heuristically.
This is a length statistic, not a new accepted wire format. The mean is the same
for fixed-size encodings themselves: exactly ANTRAG_SIG_SIZE bytes.

Removing padding quantifies the fixed-buffer overhead. It does not reconcile
the different q values for 1s/5s, or establish the paper's exact sampling and
encoding conventions. Numerical means and residual differences are in each
completed run's SUMMARY.

## Running and evidence

`bash bench/run.sh` performs offline build, correctness and timing in that order.
Requirements: Linux x86-64 with AVX2/FMA, Bash, Python 3.8+, Git, system GCC,
and installed GMP headers/library. No sudo, network or Sage is used by run.sh.
All commands inherit LANG=C and LC_ALL=C. Full instructions are in README.md.

metadata.json records the code commit, initial worktree status, source and harness
SHA-256 values, CPU, compiler, affinity, flags and all parameter sizes. Worktree
status distinguishes runs made while preparing the benchmark. The underlying
algorithm source remains identical to baseline ccca2c6a627973827abc8479f1c32ebf6926b15f.
The ignored work directory stores binaries and cross-test vectors; logs, JSON,
CSV and SUMMARY are retained. No performance numbers from cloud execution should
be used in the paper.
