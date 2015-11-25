#include <fcntl.h>
#include <inttypes.h>
#include <jni.h>
#include <linux/dvb/dmx.h>
#include <linux/dvb/frontend.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>

#include "Driver.h"

// XXX make this do qam too
// XXX throw exceptions in order to get better error info back; the -1
// fd is too opaque
int tune(const char * frontend, const int freq) {
    int err = 0;
    int fd;
    struct dvb_frontend_parameters p;

    fd = open(frontend, O_RDWR | O_NONBLOCK);

    if (fd == -1) {
        perror("open");
        err = 1;
        goto out;
    }

    memset(&p, 0, sizeof(p));

    p.frequency = (uint32_t) freq;
    p.u.vsb.modulation = VSB_8;

    if (ioctl(fd, FE_SET_FRONTEND, &p) == -1) {
        /* perror("FE_SET_FRONTEND"); */
        err = 1;
        goto out;
    }

    out:

    if (err && fd != -1) {
        close(fd);
        fd = -1;
    }

    return fd;
}

int add_filter(const char * demux,
               const dmx_pes_type_t type,
               const int pid) {
    int err = 0;
    int fd;
    struct dmx_pes_filter_params p;

    fd = open(demux, O_RDWR | O_NONBLOCK);

    if (fd == -1) {
        perror("open");
        err = 1;
        goto out;
    }

    memset(&p, 0, sizeof(p));

    p.pid = (uint16_t) pid;
    p.input = DMX_IN_FRONTEND;
    p.output = DMX_OUT_TS_TAP;
    p.pes_type = type;
    p.flags = DMX_IMMEDIATE_START;

    if (ioctl(fd, DMX_SET_PES_FILTER, &p) == -1) {
        perror("DMX_SET_PES_FILTER");
        err = 1;
        goto out;
    }

    out:

    if (err && fd != -1) {
        close(fd);
        fd = -1;
    }

    return fd;
}

JNIEXPORT jint JNICALL Java_tuba_dvb_Driver_tune
        (JNIEnv * env, jclass class, jstring frontend, jint freq) {
    const char * str;
    int fd;

    str = (*env)->GetStringUTFChars(env, frontend, NULL);

    fd = tune(str, freq);

    (*env)->ReleaseStringUTFChars(env, frontend, str);

    return fd;
}

JNIEXPORT jint JNICALL Java_tuba_dvb_Driver_add_1video_1filter
        (JNIEnv * env, jclass class, jstring demux, jint pid) {
    const char * str;
    int fd;

    str = (*env)->GetStringUTFChars(env, demux, NULL);

    fd = add_filter(str, DMX_PES_VIDEO, pid);

    (*env)->ReleaseStringUTFChars(env, demux, str);

    return fd;
}

JNIEXPORT jint JNICALL Java_tuba_dvb_Driver_add_1audio_1filter
        (JNIEnv * env, jclass class, jstring demux, jint pid) {
    const char * str;
    int fd;

    str = (*env)->GetStringUTFChars(env, demux, NULL);

    fd = add_filter(str, DMX_PES_AUDIO, pid);

    (*env)->ReleaseStringUTFChars(env, demux, str);

    return fd;
}

JNIEXPORT jint JNICALL Java_tuba_dvb_Driver_close
        (JNIEnv * env, jclass class, jint fd) {
    int ret;

    ret = close(fd);

    if (ret == -1) {
        perror("close");
    }

    return ret;
}
