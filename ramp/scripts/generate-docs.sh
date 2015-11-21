#!/bin/bash -eu

if [[ $# != 3 ]]; then
    echo "generate-docs.sh QPID-DIR QPID-RELEASE OUTPUT-DIR"
    echo "generate-docs.sh ~/code/qpid-0.14 0.14 output/site"
    exit 1
fi

set -x

QPID_DIR=$1        # ~/code/qpid-0.14
QPID_RELEASE=$2    # 0.14
OUTPUT_DIR=$3      # output/site

BOOKS_OUTPUT_DIR=$OUTPUT_DIR/docs/books/$QPID_RELEASE
APIS_OUTPUT_DIR=$OUTPUT_DIR/docs/apis/$QPID_RELEASE

rm -rf $BOOKS_OUTPUT_DIR
rm -rf $APIS_OUTPUT_DIR

mkdir -p $BOOKS_OUTPUT_DIR
mkdir -p $APIS_OUTPUT_DIR/cpp
mkdir -p $APIS_OUTPUT_DIR/python

function build {
    (
        cd $QPID_DIR/doc/book
#        make clean all
        make clean
        make
        find build -name .svn -type d -print0 | xargs -0i rm -rf \{} # Eeggh
    )

    (cd $QPID_DIR/cpp; ./bootstrap; ./configure)
    (cd $QPID_DIR/cpp/docs/api; make clean html)
    (cd $QPID_DIR/python; ./setup.py build_doc)
}

function install {
    cp -a $QPID_DIR/doc/book/build/* $BOOKS_OUTPUT_DIR

    cp -a $QPID_DIR/cpp/docs/api/html $APIS_OUTPUT_DIR/cpp/html
    (cd $APIS_OUTPUT_DIR/cpp; tar -cvzf qpid-cpp-doxygen-$QPID_RELEASE.html.tar.gz html)

    cp -a $QPID_DIR/python/build/doc $APIS_OUTPUT_DIR/python/html
    (cd $APIS_OUTPUT_DIR/python; tar -cvzf qpid-python-epydoc-$QPID_RELEASE.html.tar.gz html)
}

build
install
