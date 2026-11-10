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
intervals. Benchmark-driver integration remains pending the parameter review below.

## Inventory and paper comparison

All ten active parameter sets were evaluated using the unchanged
`scripts/gen_headers.sage` with SageMath 10.6, in separate temporary directories.
The generated `ANTRAG_D`, `ANTRAG_Q`, `ANTRAG_PK_SIZE`, `ANTRAG_SK_SIZE` and
`ANTRAG_SIG_SIZE` values are recorded in `inventory.json`.
Commented-out candidate parameters are excluded.

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

Signatures use a fixed-size padded encoding, with `encode_sig` returning failure
when the compressed vector exceeds its allocated buffer. The successful serialized
size is the table value, so its average length is identical. `tests/codec_test.c`
retries signing until encoding succeeds; its subsequent 10000-signature loop
measures encoding rejection rate. A future byte-API timing driver must handle
encoding failure explicitly. SUPERCOP's wrapper currently ignores that return value.

The paper's 512 row has q=3329, pk=768 and sig=591. The repository's 1s
uses q=3583, pk=768 and sig=592. Its 1f uses q=12289, pk=896 and sig=642.
The paper's 768 row has q=3329, pk=1152 and sig=883. The repository's 3s
matches n, q and pk, but sig=908 (25 bytes longer).
The paper's 1024 row has q=3329, pk=1536 and sig=1176. The repository has
5s with q=5119, pk=1664 and sig=1244, and 5f with q=12289, pk=1792 and sig=1282.
No active 512 or 1024 parameter set uses q=3329.

This triggers the requested parameter/size review stop. No algorithm, modulus,
dimension, sampler, codec or RNG has been changed. Timing and the one-command
benchmark are deferred until the user resolves this discrepancy. No performance
numbers have been measured by the new benchmark.

## Implementation paths and API

`falcon/config.h` enables `FALCON_AVX2=1` and `FALCON_FMA=1` directly.
`falcon/fft.c` contains AVX2 vector arithmetic guarded by `FALCON_AVX2`.
`falcon/rng.c` also has an AVX2 PRNG path. FMA intrinsics are selected through
`FMADD` and `FMSUB` in `falcon/inner.h` when both macros are enabled.
These are repository paths, not new vector implementations.
The unconditional definitions in config.h mean command-line `-D...=0` alone
cannot reliably select ref. A build-time configuration solution is still pending;
none has been applied. Ref/AVX2 comparison has not been run.

`falcon/fpr.h` defines `fpr` as a struct containing a native C `double`.
The active square root uses `sqrt` from libm. On this x86-64 host this uses
hardware floating point. The configuration comments about `FALCON_FPEMU`
do not establish a working software-emulated Antrag implementation.

`decode_sk` restores four integer vectors and fourteen double vectors, including
precomputed key material. The byte secret key is already a serialized expanded
key. The in-memory `secret_key` is accepted by `sign`, so an additional
expanded-key timing can exclude `decode_sk`. Byte Sign must include decoding,
signing and successful signature encoding; byte Verify must include public key
and signature decoding and verification. Messages will have 32 bytes.

## Correctness and current scope

No KAT fixtures or KAT runner were found. Existing tests cover NTT, FFT,
polynomial arithmetic, RNS, key/signature codec round trips and signature verification.
The earlier cloud setup passed these tests for 1f and reported 200/200 correct
signatures in the main program. Those checks used the repository default SIMD
configuration and do not constitute ref/AVX2 cross-validation.
The fixed-seed 100-case cross-build test remains pending. `seed_rng` is time-based;
a test driver can initialize the existing global PRNG through its unchanged SHAKE
initialization API rather than replacing the algorithm's random-byte functions.

The four vendored timing utilities are present; the 10001-iteration driver,
offline run.sh, build variants and performance CSV are pending parameter review.
No compilation compatibility edits have been made.

Fresh 3s validation passed with system `/usr/bin/gcc` and `LANG=C`: NTT, FFT, polynomial, RNS and codec tests, including 10000 signing attempts. Exit status was zero. This used the default AVX2/FMA configuration.

The self-test command was `make clean`, `make gen3s`, then `make -j4 CC=/usr/bin/gcc test-ntt test-poly test-rns test-codec` after activating the existing Sage environment. This regenerated only ignored build outputs.

Actual self-test compilation command (inherited conda flags included; this is not the final benchmark flag policy):

```text
/usr/bin/gcc -march=nocona -mtune=haswell -ftree-vectorize -fPIC -fstack-protector-strong -fno-plt -O2 -ffunction-sections -pipe -isystem /workspace/.tools/sage/include -Wall -Wextra -Wshadow -Wundef -DNDEBUG -g -march=native -O3 -flto -MMD -c tests/ntt_test.c -o build/tests/ntt_test.o
```
