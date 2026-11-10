# Antrag offline benchmark

Run on a Linux x86-64 host with AVX2/FMA, system GCC at `/usr/bin/gcc`,
GMP development headers/library, Git, Bash and Python 3.8+:

```bash
git fetch origin
git checkout bench
git pull --ff-only origin bench
bash bench/run.sh
```

The script uses no network or sudo and does not require SageMath.
All commands use `LANG=C` and `LC_ALL=C`.
It builds all ten parameter sets in both configurations, runs the existing
NTT/poly/RNS tests and 100-case deterministic cross-build checks, then measures
10001 KeyGen, Sign, Verify and expanded-key Sign operations per configuration.
It also measures unpadded sizes for 10000 successful signatures per build for
1s, 3s and 5s. Source and parameter files remain unchanged.

Results are written under `bench/results/<UTC timestamp>/`.
`SUMMARY.md`, `bench.csv`, JSON metadata and individual logs are retained.
The ignored `work/` directory contains staged source copies, binaries and test
vectors. It can be removed after the run when no benchmark process is using it.
Any build, verification or parameter-check failure stops the script with a
nonzero exit code. A failed/incomplete run has no final SUMMARY or CSV.

Timing is pinned to the first CPU allowed by the task's CPU affinity mask.
To choose another allowed logical CPU, use `BENCH_CPU=3 bash bench/run.sh`.
Run on an otherwise idle machine for paper measurements. Cloud results are
workflow checks only. Reported cycles are RDTSC ticks, not frequency-adjusted
core-clock cycles.

See `NOTES.md` for timing boundaries, seeds, encoded-length interpretation,
parameter discrepancies and configuration choices. The paper comparison column
uses the values provided by the user from Table 2 and Table 3(b).
