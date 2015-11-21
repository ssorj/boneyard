export PTOLEMY_DEBUG=${PTOLEMY_DEBUG:=}

export CPU_CORES=$(cat /proc/cpuinfo | awk '/^processor\W+:/ { count++ } END { print count }')

export SVN="svn --non-interactive --trust-server-cert"
export GIT="git --no-pager"

function script-init {
    date

    test -d "$PTOLEMY_PROJECT"
    test -d "$PTOLEMY_CYCLE"

    printenv | sort

    ulimit -S -c unlimited &> /dev/null

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
    local pattern="$1"
    local replacement="$2"
    local file="$3"

    tmpfile="${file}.tmp.${RANDOM}"

    sed "s/${pattern}/${replacement}/g" "$file" > "$tmpfile"
    mv "$tmpfile" "$file"
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
    local path="$1"

    (
        cd "$path"

        $SVN cleanup
        $SVN revert --recursive .

        chmod --recursive ug+w .

        $SVN status --no-ignore | awk '/^[I?]/ {print $2}' | xargs --no-run-if-empty rm -r
    )
}

function svn-revision {
    local path="$1"

    (
        cd "$path"

        $SVN info | awk '/^Last Changed Rev:/ {print $4}'
    )
}

function git-revision {
    local path="$1"

    (
        cd "$path"

        $GIT log --max-count=1 --pretty=format:'%h'
    )
}

# Assumes url follows the form repo-url?branch-id
function git-checkout {
    local url="$1"
    local path="$2"

    repo="${url%\?*}"
    branch="${url#*\?}"

    $GIT clone "$repo" "$path"

    (
        cd "$path"

        $GIT checkout "$branch"
    )
}

function git-clean {
    local path="$1"

    (
        cd "$path"

        $GIT reset --hard
        $GIT clean --force -x
    )
}

function print-process-stacks {
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
