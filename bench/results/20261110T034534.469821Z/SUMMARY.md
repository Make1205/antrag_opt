# Antrag cloud benchmark

Cloud numbers validate the workflow only; exclude them from paper results.

Code commit: `fbae8a799528fa593e3635a837c59f5fe59b2847`.

CPU: AMD EPYC 9V74 80-Core Processor; pinned logical CPU 0.

GCC: gcc (Debian 14.2.0-19) 14.2.0.

ref flags: `-O3 -march=native -DNDEBUG -std=gnu11 -include bench/config_ref.h -fno-tree-vectorize -fno-tree-slp-vectorize`; link: `-lm -lgmp`.

avx2 flags: `-O3 -march=native -DNDEBUG -std=gnu11`; link: `-lm -lgmp`.

Native hardware double/libm in both builds. Ref disables explicit SIMD and compiler loop/SLP vectorization. AVX2 enables upstream AVX2/FMA.

Each operation executes 10001 times, yielding 10002 RDTSC timestamps and 10001 adjacent intervals. The unchanged Dilithium printer subtracts counter overhead and takes the median. Units: thousand cycles (TSC ticks). Message: 32 bytes.

| Parameter set | q | pk | sig (fixed) | 论文尺寸 (pk/sig) | ref KeyGen/Sign/Verify | AVX2 KeyGen/Sign/Verify |
|---|---:|---:|---:|---|---|---|
| 1f (n=512) | 12289 | 896 | 642 | -- | 11354.433/386.099/58.343 | 12350.181/220.947/50.777 |
| 1s (n=512) | 3583 | 768 | 592 | n=512, q=3329; 768/591 | 10331.255/383.863/106.547 | 11293.879/221.857/100.177 |
| 2f (n=648) | 9721 | 1134 | 812 | -- | 16820.751/511.549/112.891 | 18271.343/301.287/102.881 |
| 2s (n=648) | 3889 | 972 | 768 | -- | 15432.585/512.277/115.075 | 16666.311/301.027/103.037 |
| 3f (n=768) | 18433 | 1440 | 1002 | -- | 21358.843/598.675/103.245 | 23402.183/348.165/91.155 |
| 3s (n=768) | 3329 | 1152 | 908 | n=768, q=3329; 1152/883 | 17365.815/597.011/190.189 | 19241.637/346.163/179.737 |
| 4f (n=864) | 10369 | 1512 | 1090 | -- | 24454.559/680.211/135.121 | 26503.853/398.761/124.071 |
| 4s (n=864) | 2593 | 1296 | 1006 | -- | 20724.937/679.665/137.539 | 22725.871/397.851/131.585 |
| 5f (n=1024) | 12289 | 1792 | 1282 | -- | 32210.151/776.801/122.303 | 34415.055/451.333/108.237 |
| 5s (n=1024) | 5119 | 1664 | 1244 | n=1024, q=3329; 1536/1176 | 28374.345/774.773/226.121 | 31017.375/451.021/219.231 |

Expanded-key Sign includes signature encoding and encoding retries, excluding byte-secret-key decoding.

| Set | ref | AVX2 |
|---|---:|---:|
| 1f | 354.431 | 206.881 |
| 1s | 353.755 | 207.245 |
| 2f | 475.929 | 282.879 |
| 2s | 476.137 | 282.957 |
| 3f | 555.697 | 326.871 |
| 3s | 553.955 | 325.259 |
| 4f | 631.799 | 373.983 |
| 4s | 631.487 | 373.801 |
| 5f | 719.731 | 422.109 |
| 5s | 718.925 | 421.953 |

Unpadded lengths include the salt and final partial data byte, excluding whole padding bytes. Each mean uses 10000 successfully encoded, verified signatures. One fixed-seed key per build/set; rejected encodings are counted separately.

| Set | Build | Mean bytes | Min/max | Encoding rejects |
|---|---|---:|---|---:|
| 1s | ref | 586.8078 | 577/592 | 136 |
| 1s | avx2 | 586.8078 | 577/592 | 136 |
| 3s | ref | 899.4041 | 885/908 | 159 |
| 3s | avx2 | 899.4041 | 885/908 | 159 |
| 5s | ref | 1238.4003 | 1230/1244 | 31 |
| 5s | avx2 | 1238.4003 | 1230/1244 | 31 |

Padding and remaining difference from the paper, in bytes:

| Set | Build | Fixed minus mean (padding) | Mean minus paper sig |
|---|---|---:|---:|
| 1s | ref | 5.1922 | -4.1922 |
| 1s | avx2 | 5.1922 | -4.1922 |
| 3s | ref | 8.5959 | +16.4041 |
| 3s | avx2 | 8.5959 | +16.4041 |
| 5s | ref | 5.5997 | +62.4003 |
| 5s | avx2 | 5.5997 | +62.4003 |

Correctness: existing NTT/poly/RNS unit tests passed for all 20 builds. No upstream KAT exists. Fixed-seed vectors and cross-verification results:

| Set | Equal pk/sk/sig (of 100) | Cross Verify ref←AVX2 / AVX2←ref |
|---|---|---|
| 1f | 100/0/100 | 100/100 |
| 1s | 100/0/100 | 100/100 |
| 2f | 100/0/100 | 100/100 |
| 2s | 100/0/100 | 100/100 |
| 3f | 100/0/100 | 100/100 |
| 3s | 100/0/100 | 100/100 |
| 4f | 100/0/100 | 100/100 |
| 4s | 100/0/100 | 100/100 |
| 5f | 100/0/100 | 100/100 |
| 5s | 100/0/100 | 100/100 |

FMA can change floating-point expanded-key material and signatures. Byte differences are retained in correctness.json; every foreign signature and foreign serialized secret key was verified, and changed messages were rejected.

The latest shorthand for 3s (768/883) is interpreted as n=768 and sig=883; paper pk=1152 follows the earlier complete table supplied by the user.

Paper comparisons are user-supplied Table 2 / Table 3(b) values. 1s and 5s also differ in q. Removing padding changes length only; it does not make their parameters match the paper.

KeyGen includes pk/sk encoding. Sign includes byte-sk decoding, signing, signature encoding and retry after encoding overflow. Verify includes byte-pk and signature decoding. The repository byte-sk already serializes expanded material; decode_sk restores that material. Algorithm source is unchanged; configuration and driver are external. See metadata.json for source hashes and worktree status.

Execution harness commit: `98d61a19c3e22feed31f58915e400a7647395f92`. Report layout was completed after measurement using unchanged JSON values.
