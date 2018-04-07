CCFLAGS := -Os -std=c++11 -lstdc++
TARGETS := connect

.PHONY: build
build: ${TARGETS}

.PHONY: clean
clean:
	rm -f ${TARGETS}

.PHONY: test
test: build
	PN_TRACE_FRM=1 KRB5_TRACE=/dev/stdout ./connect 127.0.0.1

%: %.cpp
	${CXX} $< -o $@ ${CCFLAGS} -lqpid-proton -lqpid-proton-cpp
