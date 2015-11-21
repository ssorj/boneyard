#!/bin/bash -efx

VERSION="$1"
VERSION_SHORT="$2"

if [[ ! -d test ]]; then
    mkdir test
fi

function expand-tarball {
    local source_dir="$1"
    local target_dir="$2"

    if [[ -z "$target_dir" ]]; then
        local target_dir="$source_dir"
    fi

    if [[ -d "test/${target_dir}" ]]; then
        return
    fi

    (cd test; tar -xvzf "../artifacts/${source_dir}.tar.gz")
}

expand-tarball "qpid-cpp-${VERSION}" "qpidc-${VERSION_SHORT}"
expand-tarball "qpid-${VERSION}"

(cd "test/qpidc-${VERSION_SHORT}"; ./configure; make check)
(cd "test/qpid-${VERSION}/java"; ant test)
