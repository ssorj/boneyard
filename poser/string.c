#include "common.h"

int main(size_t argc, char** argv) {
    int string_count = 1000 * 1000;

    pn_string_t *strings[string_count];

    struct timespec start;
    struct timespec interval;

    init_time(&start);
    init_time(&interval);

    for (int i = 0; i < string_count; i++) {
        strings[i] = pn_string("0123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789");
    }

    mark_time(&interval, "construct");

    for (int i = 0; i < string_count; i++) {
        pn_string_get(strings[i]);
    }

    mark_time(&interval, "get");

    for (int i = 0; i < string_count; i++) {
        pn_string_buffer(strings[i]);
    }

    mark_time(&interval, "buffer");

    for (int i = 0; i < string_count; i++) {
        pn_string_size(strings[i]);
    }

    mark_time(&interval, "size");

    for (int i = 0; i < string_count; i++) {
        pn_string_capacity(strings[i]);
    }

    mark_time(&interval, "capacity");

    for (int i = 0; i < string_count; i++) {
        pn_string_set(strings[i], "abcdefghijklmnopqrstuvwxyz");
    }

    mark_time(&interval, "set");

    for (int i = 0; i < string_count; i++) {
        pn_string_grow(strings[i], 100);
    }

    mark_time(&interval, "grow");

    for (int i = 0; i < string_count; i++) {
        pn_string_resize(strings[i], 200);
    }

    mark_time(&interval, "resize");

    pn_string_t *dst = pn_string("");

    for (int i = 0; i < string_count; i++) {
        pn_string_copy(dst, strings[i]);
    }

    mark_time(&interval, "copy");

    for (int i = 0; i < string_count; i++) {
        pn_string_clear(strings[i]);
    }

    mark_time(&interval, "clear");
    mark_time(&start, "total");
}

// PN_EXTERN pn_string_t *pn_string(const char *bytes);
// PN_EXTERN pn_string_t *pn_stringn(const char *bytes, size_t n);
// PN_EXTERN const char *pn_string_get(pn_string_t *string);
// PN_EXTERN size_t pn_string_size(pn_string_t *string);
// PN_EXTERN int pn_string_set(pn_string_t *string, const char *bytes);
// PN_EXTERN int pn_string_setn(pn_string_t *string, const char *bytes, size_t n);
// PN_EXTERN ssize_t pn_string_put(pn_string_t *string, char *dst);
// PN_EXTERN void pn_string_clear(pn_string_t *string);
// PN_EXTERN int pn_string_format(pn_string_t *string, const char *format, ...)
// #ifdef __GNUC__
//   __attribute__ ((format (printf, 2, 3)))
// #endif
//     ;
// PN_EXTERN int pn_string_vformat(pn_string_t *string, const char *format, va_list ap);
// PN_EXTERN int pn_string_addf(pn_string_t *string, const char *format, ...)
// #ifdef __GNUC__
//   __attribute__ ((format (printf, 2, 3)))
// #endif
//     ;
// PN_EXTERN int pn_string_vaddf(pn_string_t *string, const char *format, va_list ap);
// PN_EXTERN int pn_string_grow(pn_string_t *string, size_t capacity);
// PN_EXTERN char *pn_string_buffer(pn_string_t *string);
// PN_EXTERN size_t pn_string_capacity(pn_string_t *string);
// PN_EXTERN int pn_string_resize(pn_string_t *string, size_t size);
// PN_EXTERN int pn_string_copy(pn_string_t *string, pn_string_t *src);

// #include <time.h>
// #include <stdio.h>
// #include <string.h>

// int main(void)
// {
//     time_t mytime = time(NULL);
//     char * time_str = ctime(&mytime);
//     time_str[strlen(time_str)-1] = '\0';
//     printf("Current Time : %s\n", time_str);

//     return 0;
// }
