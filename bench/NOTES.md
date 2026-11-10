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
