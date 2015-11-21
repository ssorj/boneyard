source ../common/qpid.bash

export ANT_OPTS=-Xmx1024M

function ant-test-interop {
    local tmpdir=$(mktemp -d)
    local out="${tmpdir}/default.out"

    ant test-interop 2>&1 | tee "$out" || :

    local code="${PIPESTATUS[0]}"

    if [[ "$code" != 0 ]]; then
        echo "== profile 'interop' =="

        print-failures "$out"

        save-results interop
    fi

    ant clean-results

    rm -rf "$tmpdir"

    return "$code"
}

function ant-test-external {
    test "$1" && local profile="$1" || exit 1
    test "$2" && local port="$2" || exit 1
    test "$3" && local args="$3" || :
    local tmpdir=$(mktemp -d)
    local command=$(broker-command "$port" "$tmpdir")
    local datadir="${tmpdir}/data"
    local out="${tmpdir}/${profile}.out"

    maybe-kill-brokers

    ant test \
        -Dbroker="${command} ${args}" \
        -Dbuild.data="$datadir" \
        -Dprofile="$profile" \
        2>&1 | tee "$out"

    local code="${PIPESTATUS[0]}"

    local bpids=$(broker-pids)

    if [[ "$bpids" ]]; then
        echo "Test brokers failed to exit (pids ${bpids})"
        ps -fwwu "$USER" --forest
        kill -9 $bpids
        code=1
    fi

    if [[ "$code" != 0 ]]; then
        echo "== profile '${profile}' =="

        print-failures "$out"

        save-results "$profile"
    fi

    ant clean-results

    rm -rf "$tmpdir"

    return "$code"
}

function save-results {
    test "$1" && local profile="$1" || exit 1

    if [[ "$CYCLE_PATH" ]]; then
        tar -czf "${CYCLE_PATH}/${profile}.tgz" --exclude \*.xml -C build results
    fi
}

function print-failures {
    set +x

    test "$1" && local out="$1" || exit 1

    local failures=$(awk '/^\W*\[junit\] Test [^\W]+ FAILED$/ { print $3 }' "$out")

    for test in $failures; do
        for file in $(find build/results -name "TEST-${test}.txt"); do
            cat "$file"
            echo "--"
        done
    done

    set -x
}
