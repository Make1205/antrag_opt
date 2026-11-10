/* Build configuration only: keep every upstream option except SIMD. */
#include "../falcon/config.h"
#undef FALCON_AVX2
#undef FALCON_FMA
#define FALCON_AVX2 0
#define FALCON_FMA 0
