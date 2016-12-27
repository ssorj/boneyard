# Qpid project source reorganization

## Overview

This proof of concept represents an effort to achieve the source tree
layout proposed [here][1].  It allows the Qpid project to produce
independent releases of Qpid C++ and Python as well as other modules
that have heretofore been bundled into one large Qpid release.

[1]: https://cwiki.apache.org/confluence/display/qpid/Source+tree+layout+proposal

### End-goal top-level codebases and source artifacts

    New and will be migrated to Git

    qpid-cpp        qpid-cpp.git              qpid-cpp-VERSION.tar.gz
    qpid-python     qpid-python.git           qpid-python-VERSION.tar.gz

    Existing in Subversion

    qpid-java       qpid/java/trunk           qpid-java-VERSION.tar.gz
    qpid-maven      qpid/maven/trunk          [NA]
    qpid-site       qpid/site                 [NA]
    qpid-specs      qpid/specs                [NA]

    Existing in Git

    qpid-dispatch   qpid-dispatch.git         qpid-dispatch-VERSION.tar.gz
    qpid-jms        qpid-jms.git              apache-qpid-jms-VERSION.tar.gz
    qpid-proton     qpid-proton.git           qpid-proton-VERSION.tar.gz

### Dependencies

    qpid-cpp        depends on                qpid-proton for amqp 1.0 support
    qpid-cpp        depends on                qpid-python for its tests
    qpid-dispatch   depends on                qpid-proton
    qpid-java       depends on                qpid-python for its tests
    qpid-jms        depends on                qpid-proton
    qpid-python     optionally depends on     saslwrapper

## Changes in the Subversion tree

Note that the proof of concept does not in fact move the new top-level
codebases into the standard Subversion structure with trunk, branches,
and tags.  In order to minimize diffs, they instead remain in their
current locations, but updated to remove cross-tree source
dependencies.

After more discussion, we have decided to migrate the C++ and Python
trees to Git.  I will not move the code into the trunk-branches-tags
structure, but I will make the changes discussed below in Subversion
first, before the migration to Git.

A skeletal version of the existing Subversion layout will remain in
place for things such as AMQP spec files that are linked to
externally.
 
### Moves

Migrate qpid/trunk/qpid/tools python and ruby content to
qpid/trunk/qpid/cpp/management:

    tools/setup.py                 -> cpp/management/setup.py
    tools/MANIFEST.in              -> cpp/management/MANIFEST.in
    tools/*.txt                    -> cpp/management/python/*.txt
    tools/src/py/$libs             -> cpp/management/python/lib/$libs
    extras/qmf/src/py/qmf          -> cpp/management/python/lib/qmf
    tools/src/py/$tools            -> cpp/management/python/bin/$tools
    tools/src/ruby/qpid_management -> cpp/management/ruby/qpid_management

Migrate qpid/trunk/qpid/tests to qpid/trunk/qpid/python:

    tests/src/py/qpid_tests        -> python/qpid_tests

Migrate Windows packaging scripts to qpid/trunk/qpid/cpp:

    packaging/windows              -> cpp/packaging/windows

Migrate the remaining docbook content (some has already been moved to
qpid-java) to qpid/cpp:

    doc/book                       -> cpp/docs

### Deletions

Obsolete:

    QPID_VERSION.txt               # No longer makes sense
    LICENSE                        # No longer makes sense
    NOTICE                         # No longer makes sense
    extras/dispatch                # Obsolete stub
    doc/website                    # Obsolete stub

Apparently no longer in use:

    review                         # Not touched since 2009
    sandbox                        # Not touched since 2010
    bin                            # Not touched since 2012
    buildtools                     # Not touched since 2010
    doc/dev-readme                 # Not touched since 2010
    etc                            # Not touched since 2008
    wcf                            # Not touched since 2012

I'm judging "in use" by whether there have been any changes--not an
excellent metric.  If you are using any of these, please inform me so
that I preserve them.

## Sequence with respect to Git migration

I intend to migrate the C++ and Python subtrees to Git using the
following sequence:

 - Reorganize the C++ and Python subtrees inside the current
   Subversion structure
 - Migrate the isolated C++ and Python subtrees to their own Git repos
 - Reorganize the remaining Subversion tree to the target layout

## Qpid C++

### Changes in the C++ subtree

Relocate some docs:

    cpp/design_docs                -> cpp/docs/design
    cpp/docs/src/*                 -> cpp/docs/design
    cpp/DESIGN                     -> cpp/docs/design/overview.txt

    cpp/AMQP_1.0                   -> cpp/docs/amqp-1.0.txt
    cpp/SSL                        -> cpp/docs/ssl.txt
    cpp/README-HA.txt              -> cpp/docs/ha.txt

Collect winsdk stuff:

    cpp/bld-winsdk.ps1             -> cpp/packaging/winsdk/bld-winsdk.ps1
    cpp/README-winsdk.ps1          -> cpp/packaging/winsdk/README.txt

Clean up names and extensions:

    cpp/QPID_VERSION.txt           -> cpp/VERSION.txt  # Matching what Dispatch has
    cpp/NOTICE                     -> cpp/NOTICE.txt
    cpp/LICENSE                    -> cpp/LICENSE.txt  # Using .txt extension for these
    cpp/INSTALL                    -> cpp/INSTALL.txt  # is widespread practice now
    cpp/INSTALL-WINDOWS            -> cpp/INSTALL-WINDOWS.txt

### Improvements to the C++ tests

Changes:

 - Run scripts ("run_" scripts) organized by feature area
 - Run scripts are uniformly named
 - Run scripts produce temporary work dirs of the form run_script\_name_XXXX
   - They are removed on test success
 - All run scripts are runnable directly from src/tests build dir
 - Python test env and test broker tools - should be cross platform
   - Permits removal of many scripts that have both bash and
     powershell variants
   - Broker creation is more consistent
   - Broker termination and checking too
 - Modernized bash scripts

Test results after initial relocation:

    The following tests FAILED:
    	  1 - api_check_qpidtypes (Failed)
    	  2 - api_check_qpidmessaging (Failed)
    	 20 - interop_tests (Failed)
    	 21 - ha_tests (Failed)
    	 22 - qpidd_qmfv2_tests (Failed)
    	 23 - interlink_tests (Failed)
    	 24 - idle_timeout_tests (Failed)
    Errors while running CTest
    Makefile:149: recipe for target 'test' failed
    make: *** [test] Error 8

It was actually worse than this suggests.  Lots of the tests silently
pass (!) if the python testing tools are not available.

Current test results on Fedora 23:

    The following tests FAILED:
    	  4 - acl_tests (Failed)                   [valgrind error]
    	 12 - python_tests (Failed)                [0-10 management tests, test_connection_stats]
    	 13 - queue_redirect_tests (Failed)        [valgrind error]
    	 26 - linearstore_python_tests (Failed)    [valgrind error]
    Errors while running CTest

## Possibly impacted parties

 - Steve Huston - Windows packaging code (qpid/packaging/windows)
 - Java broker folks - Relocation of Python qpid_tests may affect Java
   broker testing

## How to setup the Qpid Python dependency

    cd qpid/python/trunk
    ./setup.py install --user
    export PYTHONPATH=$HOME/.local/lib/python2.7/site-packages
    export PATH=$HOME/.local/bin:$PATH

## Notes

 - Gah! Circular dependency.  Qpid Python (via qpid.testlib) depends
   on qpidtoollibs.  This should be removed: Qpid C++ depends on Qpid
   Python and not the reverse in any way.

 - The new test regime more uniformly runs brokers with valgrind, and
   this exposes new valgrind errors.

 - I removed the following test install utils from src/tests:
   qpid-build-rinstall, install_env.sh, etc.  If these are still
   important, I'd like to bring them back in a subdirectory or a
   different project altogether.  They are not central to the C++
   tests.

## Links

 - [Qpid jira](https://issues.apache.org/jira/browse/QPID-7207)

## Todo

 - Make C++ cmake find qpid-python by common prefix
 - Find a suitable spot in the Subversion tree to direct people to the
   new locations for things
 - Rewrite the index in qpid/README.txt - Update all the top-level
   info
 - Adjust the scope of windows testing to what we can ensure is
   working correctly from a test mechanics standpoint
