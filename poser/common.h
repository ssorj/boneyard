#define _POSIX_C_SOURCE 200809L

#include <proton/object.h>

#include <stdio.h>
#include <stdlib.h>
#include <time.h>

static inline void init_time(struct timespec *tv) {
    clock_gettime(CLOCK_MONOTONIC, tv);
}

static inline void mark_time(struct timespec *tv, char *label) {
    long long prev_time = (((long long) tv->tv_sec) * 1000) + (tv->tv_nsec / 1000000);

    clock_gettime(CLOCK_MONOTONIC, tv);

    long long curr_time = (((long long) tv->tv_sec) * 1000) + (tv->tv_nsec / 1000000);

    printf("%s: %ld\n", label, curr_time - prev_time);
}
