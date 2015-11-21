export DEVEL_HOME="$PWD"
export DEVEL_MODULES="mint cumin basil parsley wooly"

# PYTHONPATH

if [[ -z "$DEVEL_ORIGINAL_PYTHONPATH" ]] {
    export DEVEL_ORIGINAL_PYTHONPATH="$PYTHONPATH"
}

pypath="$DEVEL_HOME/lib/python:$HOME/lib/python:$DEVEL_ORIGINAL_PYTHONPATH"

foreach module in `echo $DEVEL_MODULES`
    pypath="$DEVEL_HOME/$module/python:$pypath"
end

export PYTHONPATH="$pypath"

# PATH

if [[ -z "$DEVEL_ORIGINAL_PATH" ]] {
    export DEVEL_ORIGINAL_PATH="$PATH"
}

path="$DEVEL_HOME/bin:$DEVEL_ORIGINAL_PATH"

foreach module in `echo $DEVEL_MODULES`
    path="$DEVEL_HOME/$module/bin:$path"
end

export PATH="$path"

# cumin test instance
export CUMIN_HOME="$DEVEL_HOME/cumin-test-0"
