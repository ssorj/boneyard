CCFLAGS := -Os -std=c++11 -lstdc++ -g
SOURCES := $(shell find . -name \*.cpp)
TARGETS := ${SOURCES:./%.cpp=build/%}

.PHONY: run
run: build
	build/main

.PHONY: build
build: ${TARGETS}

.PHONY: clean
clean:
	rm -rf build

build/%: %.cpp
	@mkdir -p ${@D}
	${CXX} $< -o $@ ${CCFLAGS}
