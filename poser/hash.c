#include "common.h"

int main(size_t argc, char** argv) {
    int count = 1000 * 1000 * 10;

    pn_hash_t *map = pn_hash(PN_OBJECT, 100, 0.75);
    pn_string_t *key = pn_string("key");
    pn_string_t *value = pn_string("value");

    struct timespec start;
    struct timespec interval;

    init_time(&start);
    init_time(&interval);

    for (int i = 0; i < count; i++) {
        pn_hash_put(map, (uintptr_t) key, value);
    }

    mark_time(&interval, "put");

    for (int i = 0; i < count; i++) {
        pn_hash_size(map);
    }

    mark_time(&interval, "size");

    for (int i = 0; i < count; i++) {
        pn_hash_get(map, (uintptr_t) key);
    }

    mark_time(&interval, "get");

    for (int i = 0; i < count; i++) {
        pn_hash_del(map, (uintptr_t) key);
    }

    mark_time(&interval, "del");

    mark_time(&start, "total");
}

// PN_EXTERN pn_hash_t *pn_hash(const pn_class_t *clazz, size_t capacity, float load_factor);
// PN_EXTERN size_t pn_hash_size(pn_hash_t *hash);
// PN_EXTERN int pn_hash_put(pn_hash_t *hash, uintptr_t key, void *value);
// PN_EXTERN void *pn_hash_get(pn_hash_t *hash, uintptr_t key);
// PN_EXTERN void pn_hash_del(pn_hash_t *hash, uintptr_t key);
// PN_EXTERN pn_handle_t pn_hash_head(pn_hash_t *hash);
// PN_EXTERN pn_handle_t pn_hash_next(pn_hash_t *hash, pn_handle_t entry);
// PN_EXTERN uintptr_t pn_hash_key(pn_hash_t *hash, pn_handle_t entry);
// PN_EXTERN void *pn_hash_value(pn_hash_t *hash, pn_handle_t entry);
