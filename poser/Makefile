TARGETS := string map hash object list
CFLAGS  := -g -O2 -std=c99 -fno-omit-frame-pointer

%: %.c
	gcc $< -o $@ ${CFLAGS} -lqpid-proton -lqpid-proton-proactor

.PHONY:
build: clean ${TARGETS}

.PHONY:
clean:
	rm -f ${TARGETS}
