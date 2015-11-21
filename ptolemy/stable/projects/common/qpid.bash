export CXXFLAGS="-O3"

# XXX On its way out
function broker-command {
    set +x

    test "$1" && local port="$1" || local port=0
    test "$2" && local datadir="$2" || local datadir=$(mktemp -d)

    local executable="${INSTALL_PATH}/sbin/qpidd"
    local args="--port ${port} --data-dir ${datadir} --trace --auth no"

    echo -n "${executable} ${args}"

    set -x
}

function start-broker {
    set +x

    local executable="${INSTALL_PATH}/sbin/qpidd"
    local port=0
    local datadir=$(mktemp -d)

    test -x "$executable"

    local command="${executable} --port ${port} --data-dir ${datadir} --trace --auth no --daemon $@"

    echo "Starting broker using the following command:"
    echo -n "  "
    echo "$command" | sed "s/ --/\n    --/g"

    TEST_BROKER_PORT=$($command)

    set -x
}

function stop-broker {
    set +x

    test "$TEST_BROKER_PORT" && port="$TEST_BROKER_PORT" || return 1

    echo "Stopping broker at port ${port}"

    "${INSTALL_PATH}/sbin/qpidd" --quit --port "$port"

    set -x
}

function maybe-build-cpp {
    set +x

    if [[ ! -d "${SOURCE_PATH}/cpp" ]]; then
        echo "Qpid cpp dir not found at ${SOURCE_PATH}/cpp"
        return 1
    fi

    if [[ -e "${SOURCE_PATH}/cpp/src/qpidd" ]]; then
        echo "Qpid cpp is already built"
        return
    fi

    set -x

    pushd "${SOURCE_PATH}/cpp"

    if [[ "$(distro)" == "rhel" && "$(release)" == "4" ]]; then
        (cd boost-1.32-support && make apply)
    fi

    ./bootstrap
    ./configure
    make -j$(core-count)

    popd
}

function broker-pids {
    set +x
    pgrep -u "$USER" ".*qpidd.*"
    set -x
}

function maybe-kill-brokers {
    local pids=$(broker-pids)

    if [[ "$pids" ]]; then
        echo "Extra brokers hanging around; killing them (${pids})"
        kill -9 $pids
    fi
}
