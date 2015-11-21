source "${PTOLEMY_HOME}/lib/bash/common.bash"

export PROJECT_BUILD="${PTOLEMY_CYCLE}/build"

if [[ "$PTOLEMY_DEBUG" != "" ]]; then
    set -x
fi
