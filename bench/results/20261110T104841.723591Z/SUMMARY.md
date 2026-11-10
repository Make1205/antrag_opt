# Antrag benchmark — QUICK

Run context: local.

Cloud numbers validate the workflow only; exclude them from paper results.

Code commit: `b5cf110479875ad3b6cf55c475c177d9b070f47f`.

CPU: AMD EPYC 9V74 80-Core Processor; pinned logical CPU 0.

GCC: gcc (Debian 14.2.0-19) 14.2.0.

ref flags: `-O3 -march=native -DNDEBUG -std=gnu11 -ffp-contract=off -DRUNS=11 -DLENGTH_SAMPLES=100 -include bench/config_ref.h`; link: `-lm -lgmp`.

avx2 flags: `-O3 -march=native -DNDEBUG -std=gnu11 -ffp-contract=off -DRUNS=11 -DLENGTH_SAMPLES=100`; link: `-lm -lgmp`.

Native hardware double/libm in both builds. Ref disables upstream explicit SIMD/FMA without extra compiler auto-vectorization suppression. Both builds disable compiler contraction; AVX2 preserves upstream explicit FMA intrinsics in falcon/fft.c.

Each operation executes 11 measured calls after 20 warmup rounds; fresh byte-key triples for KeyGen/Sign/Verify. The unchanged Dilithium printer subtracts counter overhead and takes the median. Units: thousand cycles (TSC ticks). Message: 32 bytes.

| Parameter set | q | pk | sig (fixed) | 论文尺寸 (pk/sig) | ref KeyGen/Sign/Verify | AVX2 KeyGen/Sign/Verify |
|---|---:|---:|---:|---|---|---|
| 1f (n=512) | 12289 | 896 | 642 | -- | 12446.043/372.345/62.841 | 12333.801/234.233/63.075 |
| 1s (n=512) | 3583 | 768 | 592 | n=512, q=3329; 768/591 | 11297.337/373.515/109.641 | 11352.587/235.897/111.045 |
| 2f (n=648) | 9721 | 1134 | 812 | -- | 19198.139/500.265/119.365 | 18929.247/326.975/118.689 |
| 2s (n=648) | 3889 | 972 | 768 | -- | 17438.745/491.971/119.469 | 17243.745/319.279/119.105 |
| 3f (n=768) | 18433 | 1440 | 1002 | -- | 24086.373/620.931/113.229 | 24858.547/377.051/113.151 |
| 3s (n=768) | 3329 | 1152 | 908 | n=768, q=3329; 1152/883 | 18918.639/574.521/194.661 | 20342.529/365.533/194.687 |
| 4f (n=864) | 10369 | 1512 | 1090 | -- | 27490.969/665.677/151.319 | 28753.087/431.313/145.599 |
| 4s (n=864) | 2593 | 1296 | 1006 | -- | 24267.827/671.943/144.845 | 25731.185/441.375/145.495 |
| 5f (n=1024) | 12289 | 1792 | 1282 | -- | 35852.751/752.777/132.131 | 37298.741/481.623/132.677 |
| 5s (n=1024) | 5119 | 1664 | 1244 | n=1024, q=3329; 1536/1176 | 33804.159/763.905/241.617 | 32573.735/505.594/238.184 |

Expanded-key Sign includes signature encoding and encoding retries, excluding byte-secret-key decoding.

| Set | ref | AVX2 |
|---|---:|---:|
| 1f | 348.269 | 207.245 |
| 1s | 341.119 | 207.531 |
| 2f | 454.687 | 282.489 |
| 2s | 459.081 | 281.527 |
| 3f | 532.791 | 327.079 |
| 3s | 533.181 | 324.089 |
| 4f | 632.215 | 377.831 |
| 4s | 608.893 | 378.741 |
| 5f | 701.583 | 428.141 |
| 5s | 698.385 | 529.333 |

Unpadded lengths include the salt and final partial data byte, excluding whole padding bytes. Each mean uses 100 successfully encoded, verified signatures. One fixed-seed key per build/set; rejected encodings are counted separately.

| Set | Build | Mean bytes | Min/max | Encoding rejects |
|---|---|---:|---|---:|
| 1s | ref | 586.6000 | 581/592 | 1 |
| 1s | avx2 | 586.6000 | 581/592 | 1 |
| 3s | ref | 898.6800 | 888/908 | 0 |
| 3s | avx2 | 898.6800 | 888/908 | 0 |
| 5s | ref | 1238.2800 | 1233/1244 | 0 |
| 5s | avx2 | 1238.2800 | 1233/1244 | 0 |

Padding and remaining difference from the paper, in bytes:

| Set | Build | Fixed minus mean (padding) | Mean minus paper sig |
|---|---|---:|---:|
| 1s | ref | 5.4000 | -4.4000 |
| 1s | avx2 | 5.4000 | -4.4000 |
| 3s | ref | 9.3200 | +15.6800 |
| 3s | avx2 | 9.3200 | +15.6800 |
| 5s | ref | 5.7200 | +62.2800 |
| 5s | avx2 | 5.7200 | +62.2800 |

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

FMA audit (linked driver; only explicit upstream FFT intrinsics may remain):

| Set | ref count | AVX2 explicit FMA count |
|---|---:|---:|
| 1f | 0 | 8 |
| 1s | 0 | 8 |
| 2f | 0 | 8 |
| 2s | 0 | 8 |
| 3f | 0 | 8 |
| 3s | 0 | 8 |
| 4f | 0 | 8 |
| 4s | 0 | 8 |
| 5f | 0 | 8 |
| 5s | 0 | 8 |

FMA can change floating-point expanded-key material and signatures. Byte differences are retained in correctness.json; every foreign signature and foreign serialized secret key was verified, and changed messages were rejected.

The latest shorthand for 3s (768/883) is interpreted as n=768 and sig=883; paper pk=1152 follows the earlier complete table supplied by the user.

Paper comparisons are user-supplied Table 2 / Table 3(b) values. 1s and 5s also differ in q. Removing padding changes length only; it does not make their parameters match the paper.

KeyGen includes pk/sk encoding. Sign includes byte-sk decoding, signing, signature encoding and retry after encoding overflow. Verify includes byte-pk and signature decoding. The repository byte-sk already serializes expanded material; decode_sk restores that material. Algorithm source is unchanged; configuration and driver are external. See metadata.json for source hashes and worktree status.
