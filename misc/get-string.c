#include <errno.h>
#include <stdio.h>
#include <string.h>

const char *src = "abc\0";

// Returns ERANGE if dst plus the null byte cannot hold the value.
// Adds a null byte even if src lacks one.
int get(char *dst, const size_t len) {
    if (strlen(src) + 1 > len) {
        return ERANGE;
    }

    if (len > 0) {
        (void) strncpy(dst, src, len - 1);
        dst[len - 1] = '\0';
    }

    return 0;
}

int main() {
    int err;

    size_t len1 = 2;
    char result1[len1];

    err = get(result1, len1);

    printf("2 \"%s\" (%d)\n", result1, err);

    size_t len2 = 4;
    char result2[len2];

    err = get(result2, len2);

    printf("4 \"%s\" (%d)\n", result2, err);

    size_t len3 = 4;
    char result3[len3];

    err = get(result3, len3);

    printf("8 \"%s\" (%d)\n", result3, err);

    return 0;
}

// 2 "" (34)
// 4 "abc" (0)
// 8 "abc" (0)
