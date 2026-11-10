# Antrag inventory — parameter review required

Cloud workflow checkpoint; timings pending.

Baseline code: `ccca2c6a627973827abc8479f1c32ebf6926b15f`.

CPU: AMD EPYC 9V74 80-Core Processor

GCC: gcc (Debian 14.2.0-19) 14.2.0

Benchmark compilation flags: pending. No timing driver has been compiled.

Units for future timings: thousand cycles. `pending` means unmeasured.

| Parameter set | q | pk | sig | ref KeyGen/Sign/Verify | AVX2 KeyGen/Sign/Verify |
|---|---:|---:|---:|---|---|
| 1f (n=512) | 12289 | 896 | 642 | pending | pending |
| 1s (n=512) | 3583 | 768 | 592 | pending | pending |
| 2f (n=648) | 9721 | 1134 | 812 | pending | pending |
| 2s (n=648) | 3889 | 972 | 768 | pending | pending |
| 3f (n=768) | 18433 | 1440 | 1002 | pending | pending |
| 3s (n=768) | 3329 | 1152 | 908 | pending | pending |
| 4f (n=864) | 10369 | 1512 | 1090 | pending | pending |
| 4s (n=864) | 2593 | 1296 | 1006 | pending | pending |
| 5f (n=1024) | 12289 | 1792 | 1282 | pending | pending |
| 5s (n=1024) | 5119 | 1664 | 1244 | pending | pending |

Expanded-key Sign: pending.

Mismatch: q=3329 exists only for 3s (n=768), whose signature is 908 bytes, compared with 883 in the paper. No q=3329 sets exist for n=512 or n=1024. See ../../NOTES.md for the full comparison. User decision is required before further benchmark work.
