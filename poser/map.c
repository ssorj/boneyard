#include "common.h"

int main(size_t argc, char** argv) {
    int count = 1000 * 1000 * 10;

    pn_map_t *map = pn_map(PN_OBJECT, PN_OBJECT, 100, 0.75);
    pn_string_t *value = pn_string("value");
    pn_string_t *key1 = pn_string("abc");
    pn_string_t *key2 = pn_string("def");
    pn_string_t *key3 = pn_string("ghi");
    pn_string_t *key4 = pn_string("jkl");
    pn_string_t *key5 = pn_string("mno");
    pn_string_t *key6 = pn_string("pqr");
    pn_string_t *key7 = pn_string("stu");
    pn_string_t *key8 = pn_string("vwx");
    pn_string_t *key9 = pn_string("yz");

    struct timespec start;
    struct timespec interval;

    init_time(&start);
    init_time(&interval);

    for (int i = 0; i < count; i++) {
        pn_map_put(map, key1, value);
        pn_map_put(map, key2, value);
        pn_map_put(map, key3, value);
        pn_map_put(map, key4, value);
        pn_map_put(map, key5, value);
        pn_map_put(map, key6, value);
        pn_map_put(map, key7, value);
        pn_map_put(map, key8, value);
        pn_map_put(map, key9, value);
    }

    mark_time(&interval, "put");

    for (int i = 0; i < count; i++) {
        pn_map_size(map);
    }

    mark_time(&interval, "size");

    for (int i = 0; i < count; i++) {
        pn_map_get(map, key1);
        pn_map_get(map, key2);
        pn_map_get(map, key3);
        pn_map_get(map, key4);
        pn_map_get(map, key5);
        pn_map_get(map, key6);
        pn_map_get(map, key7);
        pn_map_get(map, key8);
        pn_map_get(map, key9);
    }

    mark_time(&interval, "get");

    for (int i = 0; i < count; i++) {
        pn_map_del(map, key1);
        pn_map_del(map, key2);
        pn_map_del(map, key3);
        pn_map_del(map, key4);
        pn_map_del(map, key5);
        pn_map_del(map, key6);
        pn_map_del(map, key7);
        pn_map_del(map, key8);
        pn_map_del(map, key9);
    }

    mark_time(&interval, "del");

    mark_time(&start, "total");
}

// PN_EXTERN pn_map_t *pn_map(const pn_class_t *key, const pn_class_t *value,
//                            size_t capacity, float load_factor);
// PN_EXTERN size_t pn_map_size(pn_map_t *map);
// PN_EXTERN int pn_map_put(pn_map_t *map, void *key, void *value);
// PN_EXTERN void *pn_map_get(pn_map_t *map, void *key);
// PN_EXTERN void pn_map_del(pn_map_t *map, void *key);
// PN_EXTERN pn_handle_t pn_map_head(pn_map_t *map);
// PN_EXTERN pn_handle_t pn_map_next(pn_map_t *map, pn_handle_t entry);
// PN_EXTERN void *pn_map_key(pn_map_t *map, pn_handle_t entry);
// PN_EXTERN void *pn_map_value(pn_map_t *map, pn_handle_t entry);
