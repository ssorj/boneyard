path=$(python3 - <<EOF
import distutils.sysconfig as config
import os

install_dir = os.path.abspath("install")
plat_path = config.get_python_lib(plat_specific=True, prefix=install_dir)
path = config.get_python_lib(prefix=install_dir)

print("{}:{}".format(plat_path, path))
EOF
)

PYTHONPATH=$path:$PYTHONPATH

export PYTHONPATH
