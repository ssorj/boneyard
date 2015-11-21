setenv DEVEL_HOME "$PWD"
set DEVEL_MODULES=(mint cumin basil parsley wooly)

# PYTHONPATH

if ($?PYTHONPATH) then
    if (! $?DEVEL_ORIGINAL_PYTHONPATH) then
        setenv DEVEL_ORIGINAL_PYTHONPATH "$PYTHONPATH"
    endif
else
    setenv DEVEL_ORIGINAL_PYTHONPATH
endif

set pypath="$DEVEL_HOME"/lib/python:"$HOME"/lib/python:"$DEVEL_ORIGINAL_PYTHONPATH"

foreach module ($DEVEL_MODULES)
    set pypath="$DEVEL_HOME"/"$module"/python:"$pypath"
end

setenv PYTHONPATH "$pypath"

# PATH

if (! $?DEVEL_ORIGINAL_PATH) then
    setenv DEVEL_ORIGINAL_PATH "$PATH"
endif

set path="$DEVEL_HOME"/bin:"$DEVEL_ORIGINAL_PATH"

foreach module ($DEVEL_MODULES)
    set path="$DEVEL_HOME"/"$module"/bin:"$path"
end

setenv PATH "$path"

# cumin test instance
setenv CUMIN_HOME "$DEVEL_HOME"/cumin-test-0

setenv INSTALL_PREFIX "$DEVEL_HOME"/install
