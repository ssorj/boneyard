export SOURCE_DIR=$PWD
export BUILD_DIR=$SOURCE_DIR/build
export INSTALL_DIR=$SOURCE_DIR/install

export PLINY_CONFIG=$SOURCE_DIR/etc/pliny-devel-instance.conf
export PLINY_HOME=$INSTALL_DIR/share/pliny
export PLINY_DEBUG="hello, bugs"

export PYTHONPATH=$PLINY_HOME/python
export PATH=$INSTALL_DIR/bin:$SOURCE_DIR/bin:$PATH
