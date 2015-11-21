source "${PTOLEMY_HOME}/lib/bash/common.bash"

export QPID_BRANCH_URL="${PTOLEMY_BRANCH_URL}"
export QPID_BRANCH="${PTOLEMY_BRANCH}/qpid"
export QPID_BUILD="${PTOLEMY_CYCLE}/qpid"
export QPID_CPP_BROKER="${QPID_BUILD}/cpp/src/qpidd"

export STORE_BRANCH_URL="http://anonsvn.jboss.org/repos/rhmessaging/store/trunk/cpp"
export STORE_BRANCH="${PTOLEMY_BRANCH}/store"
export STORE_BUILD="${PTOLEMY_CYCLE}/store"

export CXXFLAGS="-O3"
export ANT_OPTS=-Xmx1024M

function start-broker {
    local datadir=$(mktemp -d)

    local command="${QPID_CPP_BROKER} --port 0 --data-dir ${datadir} --trace --auth no --daemon"

    echo "Starting broker using the following command:"
    echo -n "  "
    echo "$command" | sed "s/ --/\n    --/g"

    TEST_BROKER_PORT=$($command)
}

function stop-broker {
    test "$TEST_BROKER_PORT"

    echo "Stopping broker at port ${TEST_BROKER_PORT}"

    "$QPID_CPP_BROKER" --quit --port "$TEST_BROKER_PORT"
}

function broker-pids {
    pgrep -u "$USER" ".*qpidd.*"
}

function maybe-kill-brokers {
    return # XXX

    local pids=$(broker-pids)

    if [[ "$pids" ]]; then
        echo "Extra brokers hanging around; killing them (${pids})"
        kill -9 $pids
    fi
}

function java-test-with-cpp-broker {
    local profile="$1"
    local tmpdir=$(mktemp -d)
    local out="${tmpdir}/${profile}.out"

    maybe-kill-brokers

    # The extra build task call exists to handle an ant dependancy
    # problem
    # XXX maybe not anymore

    # ant build test \
    #     -Dbroker.executable="${INSTALL_PATH}/sbin/qpidd" \
    #     -Dmodule.dir="${INSTALL_PATH}/lib/qpid/daemon" \
    #     -Dstore.module.dir="${INSTALL_PATH}/lib/qpid/daemon" \
    #     -Dbroker.args="$args" \
    #     -Dbuild.data="$datadir" \
    #     -Dprofile="$profile" \
    #     2>&1 | tee "$out"

    ant test \
        -Dstore.module.dir="${STORE_BUILD}/lib/.libs" \
        -Dprofile="$profile" \
        </dev/null 2>&1 | tee "$out"

    local code="${PIPESTATUS[0]}"

    maybe-kill-brokers

    if [[ "$code" != 0 ]]; then
        echo "== profile '${profile}' =="

        java-print-failures "$out"
    fi

    ant clean-results

    rm -rf "$tmpdir"

    return "$code"
}

function java-print-failures {
    local out="$1"
    local failures=$(awk '/^\W*\[junit\] Test [^\W]+ FAILED$/ { print $3 }' "$out")

    for test in $failures; do
        for file in $(find "${QPID_BUILD}/java/build/results" -name "TEST-${test}.txt"); do
            cat "$file"
            echo "--"
        done
    done
}
