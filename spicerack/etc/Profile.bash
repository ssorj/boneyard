export DEVEL_HOME="$PWD"
export DEVEL_MODULES="mint cumin basil parsley wooly rosemary sage"

if [[ -z "$DEVEL_ORIGINAL_PATH" ]]; then
    export DEVEL_ORIGINAL_PATH="$PATH"
fi

export PATH="${DEVEL_HOME}/bin:${DEVEL_ORIGINAL_PATH}"

if [[ -z "$DEVEL_ORIGINAL_PYTHONPATH" ]]; then
    export DEVEL_ORIGINAL_PYTHONPATH="$PYTHONPATH"
fi

export PYTHONPATH="${DEVEL_HOME}/lib/python:${HOME}/lib/python:${DEVEL_ORIGINAL_PYTHONPATH}"

for module in $DEVEL_MODULES; do
    echo "Configuring module '${module}'"

    pushd "${DEVEL_HOME}/${module}" > /dev/null

    if [[ -f "etc/module.profile" ]]; then
        source "etc/module.profile"
    else
        source "../etc/module.profile"
    fi

    popd > /dev/null
done
