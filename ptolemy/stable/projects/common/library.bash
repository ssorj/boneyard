function script-init {
    date

    printenv | sort

    ulimit -S -c unlimited &> /dev/null

    test -d "$PROJECT_PATH" || return 1
    test -d "$INSTALL_PATH" || return 1
    test -d "$CYCLE_PATH" || return 1

    trap "ps -fu $USER -Hww" SIGUSR1
    trap handle-exit EXIT
}

function handle-exit {
    if (( $? != 0 )); then
        handle-abnormal-exit
    fi
}

function handle-abnormal-exit {
    :
}

function replace {
    set +x

    test "$1" && local pattern="$1"
    test "$2" && local replacement="$2"
    test "$3" && local file="$3"

    tmpfile="${file}.tmp.${RANDOM}"

    sed "s/${pattern}/${replacement}/g" "$file" > "$tmpfile"
    mv "$tmpfile" "$file"

    set -x
}

function core-count {
    set +x

    cat /proc/cpuinfo | awk '/^processor\W+:/ { count++ } END { print count }'

    set -x
}

function disable {
    exit 64
}

function distro {
    local distro=unknown
    local id=$(lsb_release -i | awk '{print $3}')

    expr match "$id" '^RedHatEnterprise' > /dev/null && distro=rhel
    expr match "$id" '^Fedora' > /dev/null && distro=fedora

    echo -n "$distro"
}

function release {
    echo -n $(lsb_release -r | awk '{print $2}')
}

function svn-clean {
    test "$1" && local path="$1"

    pushd "$path"

    chmod --recursive ug+w .

    svn status --no-ignore | awk '/^[I?]/ {print $2}' | \
        xargs --no-run-if-empty rm -r

    popd
}

function svn-update {
    test "$1" && local url="$1"
    test "$2" && local dir="$2"

    if svn info "$dir" &>/dev/null; then
        svn cleanup "$dir"
        svn revert --recursive "$dir"
        svn-clean "$dir"
        svn update --non-interactive "$dir"
    else
        svn checkout "$url" "$dir"
    fi
}

function svn-revision {
    test "$1" && local path="$1"

    (cd "$path" && svn info | awk '/^Last Changed Rev:/ {print $4}')
}

function svn-save-revision {
    test "$CYCLE_PATH" || return 0
    test "$1" && local path="$1"

    svn-revision "$path" > "${CYCLE_PATH}/revision"
}

function svn-save-changes {
    test "$CYCLE_PATH" || return 0
    test "$LAST_REVISION" || return 0
    test "$1" && local path="$1"

    local rev=$(svn-revision "$path")

    test "$rev" = "$LAST_REVISION" || {
        pushd "$path"

        svn log -r "${rev}:${LAST_REVISION}" | awk '/^r[0-9]+/ {print $1 " " $3}' \
            >> "${CYCLE_PATH}/changes"

        popd
    }
}

function print-process-stacks {
    set +x

    while read line; do
        pid=${line%% *}
        command=${line#* }
        executable=${command%% *}

        echo "--- ${pid}, ${command} ---"

        case "$executable" in
            (*/bash|bash|*/sh|sh|*/tee|tee|*/make|make|*/python|python)
            ;;
            (*/java|java)
            jstack "$pid" || :
            ;;
            (*)
            pstack "$pid" || :
            ;;
        esac
    done < <(ps -u "$USER" --no-headers -o pid,command)

    ps -fu "$USER" -Hww

    set -x
}

function python-path {
    python <<EOF
import os
from distutils.sysconfig import get_python_lib

prefix = os.environ["INSTALL_PATH"]

dirs = list()
dirs.append(get_python_lib(prefix=prefix))
#dirs.append("%s/lib/python" % prefix)

print ":".join(dirs)
EOF
}
