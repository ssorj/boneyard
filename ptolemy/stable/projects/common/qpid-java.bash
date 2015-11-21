source ../common/qpid.bash

export ANT_OPTS=-Xmx1024M

function ant-test-external {
    test "$1" && local profile="$1" || exit 1
    test "$2" && local args="$2" || :
    local tmpdir=$(mktemp -d)
    local datadir="${tmpdir}/data"
    local out="${tmpdir}/${profile}.out"

    maybe-kill-brokers

    # The extra build task call exists to handle an ant dependancy
    # problem

    ant build test \
        -Dbroker.executable="${INSTALL_PATH}/sbin/qpidd" \
        -Dmodule.dir="${INSTALL_PATH}/lib/qpid/daemon" \
        -Dstore.module.dir="${INSTALL_PATH}/lib/qpid/daemon" \
        -Dbroker.args="$args" \
        -Dbuild.data="$datadir" \
        -Dmodules="common client systests" \
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
    tar -czf "${CYCLE_PATH}/results.tgz" --exclude \*.xml -C build results
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
