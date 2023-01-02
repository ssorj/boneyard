#include "common.h"

int main(size_t argc, char** argv) {
    const int count = 1000 * 1000;
    void *objects[count];

    struct timespec start;
    struct timespec interval;

    init_time(&start);
    init_time(&interval);

    for (int i = 0; i < count; i++) {
        objects[i] = pn_class_new(PN_OBJECT, 0);
    }

    mark_time(&interval, "construct");

    for (int i = 0; i < count; i++) {
        pn_class_incref(PN_OBJECT, objects[i]);
    }

    mark_time(&interval, "incref");

    for (int i = 0; i < count; i++) {
        pn_class_refcount(PN_OBJECT, objects[i]);
    }

    mark_time(&interval, "refcount");

    for (int i = 0; i < count; i++) {
        pn_class_decref(PN_OBJECT, objects[i]);
    }

    mark_time(&interval, "decref");

    for (int i = 0; i < count; i++) {
        pn_class_free(PN_OBJECT, objects[i]);
    }

    mark_time(&interval, "free");

    mark_time(&start, "total");
}
