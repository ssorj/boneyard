#include "common.h"

int main(size_t argc, char** argv) {
    int count = 1000 * 1000 * 10;

    pn_list_t *list = pn_list(PN_OBJECT, 100);
    pn_string_t *value = pn_string("value");

    struct timespec start;
    struct timespec interval;

    init_time(&start);
    init_time(&interval);

    for (int i = 0; i < count; i++) {
        pn_list_add(list, value);
    }

    mark_time(&interval, "add");

    for (int i = 0; i < count; i++) {
        pn_list_size(list);
    }

    mark_time(&interval, "size");

    for (int i = 0; i < count; i++) {
        pn_list_del(list, pn_list_size(list) - 1, 1);
    }

    mark_time(&interval, "del");

    for (int i = 0; i < count; i++) {
        pn_list_add(list, value);
    }

    mark_time(&interval, "add");

    for (int i = 0; i < count; i++) {
        pn_list_pop(list);
    }

    mark_time(&interval, "pop");

    mark_time(&start, "total");
}

// PN_EXTERN pn_list_t *pn_list(const pn_class_t *clazz, size_t capacity);
// PN_EXTERN size_t pn_list_size(pn_list_t *list);
// PN_EXTERN void *pn_list_get(pn_list_t *list, int index);
// PN_EXTERN void pn_list_set(pn_list_t *list, int index, void *value);
// PN_EXTERN int pn_list_add(pn_list_t *list, void *value);
// PN_EXTERN void *pn_list_pop(pn_list_t *list);
// PN_EXTERN ssize_t pn_list_index(pn_list_t *list, void *value);
// PN_EXTERN bool pn_list_remove(pn_list_t *list, void *value);
// PN_EXTERN void pn_list_del(pn_list_t *list, int index, int n);
// PN_EXTERN void pn_list_clear(pn_list_t *list);
// PN_EXTERN void pn_list_iterator(pn_list_t *list, pn_iterator_t *iter);
// PN_EXTERN void pn_list_minpush(pn_list_t *list, void *value);
// PN_EXTERN void *pn_list_minpop(pn_list_t *list);
