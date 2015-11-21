dnl # Copyright (C) 2007, 2008 Red Hat Inc.
dnl #
dnl # This file is part of Red Hat Messaging.
dnl #
dnl # Red Hat Messaging is free software; you can redistribute it and/or
dnl # modify it under the terms of the GNU Lesser General Public
dnl # License as published by the Free Software Foundation; either
dnl # version 2.1 of the License, or (at your option) any later version.
dnl #
dnl # This library is distributed in the hope that it will be useful,
dnl # but WITHOUT ANY WARRANTY; without even the implied warranty of
dnl # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
dnl # Lesser General Public License for more details.
dnl #
dnl # You should have received a copy of the GNU Lesser General Public
dnl # License along with this library; if not, write to the Free Software
dnl # Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
dnl # USA
dnl #
dnl # The GNU Lesser General Public License is available in the file COPYING.
dnl 
dnl Process this file with autoconf to produce a configure script.

AC_INIT([mace], [0.1], [rhemrg-users-list@redhat.com])
AC_CONFIG_AUX_DIR([build-aux])
AM_INIT_AUTOMAKE([dist-bzip2 subdir-objects])

# Minimum Autoconf version required.
AC_PREREQ(2.59)

AC_CONFIG_HEADERS([src/config.h])
AC_CONFIG_SRCDIR([src/GridSim.cpp])

AC_PROG_CC_STDC
AM_PROG_CC_C_O
AC_PROG_CXX
AC_USE_SYSTEM_EXTENSIONS
AC_LANG([C++])	

AC_ARG_ENABLE(warnings,
[  --enable-warnings   turn on lots of compiler warnings (recommended)],
[case "${enableval}" in
   yes|no) ;;
   *)      AC_MSG_ERROR([bad value ${enableval} for warnings option]) ;;
 esac],
 [enableval=yes])

# Warnings: Enable as many as possible, keep the code clean. Please
# do not disable warnings or remove -Werror without discussing on
# rhm-users list.
#
# The following warnings are deliberately omitted, they warn on valid code.
# -Wunreachable-code -Wpadded -Winline
# -Wshadow - warns about boost headers.

if test "${enableval}" = yes; then
  gl_COMPILER_FLAGS(-Werror)
  gl_COMPILER_FLAGS(-pedantic)
  gl_COMPILER_FLAGS(-Wall)
  gl_COMPILER_FLAGS(-Wextra)
  gl_COMPILER_FLAGS(-Wno-shadow)
  gl_COMPILER_FLAGS(-Wpointer-arith)
  gl_COMPILER_FLAGS(-Wcast-qual)
  gl_COMPILER_FLAGS(-Wcast-align)
  gl_COMPILER_FLAGS(-Wno-long-long)
  gl_COMPILER_FLAGS(-Wvolatile-register-var)
  gl_COMPILER_FLAGS(-Winvalid-pch)
  gl_COMPILER_FLAGS(-Wno-system-headers)
  AC_SUBST([WARNING_CFLAGS], [$COMPILER_FLAGS])
  AC_DEFINE([lint], 1, [Define to 1 if the compiler is checking for lint.])
  COMPILER_FLAGS=
fi

AC_DISABLE_STATIC
AC_PROG_LIBTOOL
AC_SUBST([LIBTOOL_DEPS])

# Select building against qpid checkout or install.
AC_ARG_WITH([qpid-checkout],
  [AS_HELP_STRING([--with-qpid-checkout],
    [Location of qpid checkout to build against (by default use installed qpid)])])

if test x$with_qpid_checkout != x; then
   QPID_DIR=$with_qpid_checkout
   QPID_SRC=$QPID_DIR/cpp/src
   QMF_GEN=$QPID_DIR/cpp/managementgen/qmf-gen
   test -f $QPID_SRC/qpid/agent/ManagementAgent.h || \
     AC_MSG_ERROR([$QPID_DIR does not appear to be a valid qpid checkout.])
   QPID_LIBS="$QPID_SRC/libqmfagent.la"
   QPID_CXXFLAGS="-I$QPID_SRC -I${QPID_SRC}/gen"
else
  fail=0
  AC_CHECK_PROG([QMF_GEN], [qmf-gen], [qmf-gen], [no])
  test $QMF_GEN = no &&
    AC_MSG_ERROR([Missing required qmf-gen. Install package qmf-devel or use --with-qpid-checkout])

  AC_CHECK_HEADERS([qpid/agent/ManagementAgent.h], , [fail=1])
  # Give any/all diagnostics before failing.
  test $fail = 1 &&
    AC_MSG_ERROR([Missing required qpid libraries/headers. Install package qmf-devel or use --with-qpid-checkout])
  QPID_LIBS="-lqmfagent"
fi   
AC_SUBST([QMF_GEN])
AC_SUBST([QPID_DIR])
AC_SUBST([QPID_LIBS])
AC_SUBST([QPID_CXXFLAGS])

# For libraries (libcommon) that use dlopen, dlerror, etc.,
# test whether we need to link with -ldl.
gl_saved_libs=$LIBS
AC_SEARCH_LIBS(dlopen, [dl],
		 [test "$ac_cv_search_dlopen" = "none required" ||
		  LIB_DLOPEN=$ac_cv_search_dlopen])
AC_SUBST([LIB_DLOPEN])
LIBS=$gl_saved_libs

# Require libdb_cxx (any version between 4.2 and 4.7), for the library, and for db_cxx.h.
db4_devel_fail=0
AC_CHECK_HEADER([db_cxx.h], ,[db4_devel_fail=1])
test $db4_devel_fail == 1 && \
  AC_MSG_ERROR([db4-devel package missing. Please ensure both db4 and db4-devel are installed. (hint: "yum install db4-devel" should do it...)])

gl_saved_libs=$LIBS
AC_SEARCH_LIBS([__db_open], [db_cxx-4.7 db_cxx-4.6 db_cxx-4.5 db_cxx-4.4 db_cxx-4.3 db_cxx-4.2],
		 [test "$ac_cv_search___db_open" = "none required" ||
		  LIB_BERKELEY_DB=$ac_cv_search___db_open],
		  AC_MSG_ERROR([Couldn't find required library in range db_cxx-4.2 through db_cxx-4.6]))
AC_SUBST([LIB_BERKELEY_DB])
LIBS=$gl_saved_libs

# Determine how to include db_cxx.h:
# Red Hat needs <db4/db_cxx.h>, Debian needs <db_cxx.h>.
AC_CHECK_HEADER([db4/db_cxx.h],
                [DB_CXX_HEADER_PREFIX=db4/])
if test x$DB_CXX_HEADER_PREFIX = x; then
  AC_CHECK_HEADER([db_cxx.h],
		  [DB_CXX_HEADER_PREFIX=])
fi
AC_SUBST(DB_CXX_HEADER_PREFIX)

# Set the argument to be used in "libtool -version-info ARG".
QPID_CURRENT=1
QPID_REVISION=0
QPID_AGE=1
LIBTOOL_VERSION_INFO_ARG=$QPID_CURRENT:$QPID_REVISION:$QPID_AGE
AC_SUBST(LIBTOOL_VERSION_INFO_ARG)

gl_CLOCK_TIME

AC_ARG_ENABLE([apr-platform],
  [AS_HELP_STRING([--enable-apr-platform],
    [use the Apache Portable Runtime library for platform (default no)])],
  [case $enableval in
    yes|no) enable_APR_PLATFORM=$enableval;;
    *) AC_MSG_ERROR([Invalid value for --enable-apr-platform: $enableval]);;
   esac],
  [enable_APR_PLATFORM=no]
)
AM_CONDITIONAL([USE_APR_PLATFORM], [test x$enable_APR_PLATFORM = xyes])

APR_MINIMUM_VERSION=1.2.2
AC_SUBST(APR_MINIMUM_VERSION)
AC_SUBST(APR_CXXFLAGS)
AC_SUBST(USE_APR_PLATFORM)

if test x$enable_APR_PLATFORM = xyes; then
  PKG_CHECK_MODULES([APR], [apr-1 >= $APR_MINIMUM_VERSION])
  APR_CXXFLAGS="$APR_CFLAGS -DUSE_APR_PLATFORM=1"
  USE_APR_PLATFORM=1
fi

# We use valgrind for the tests.  See if it's available.
AC_CHECK_PROG([VALGRIND], [valgrind], [valgrind])

# If rpmlint is available we'll run it when building RPMs.
AC_CHECK_PROG([RPMLINT], [rpmlint], [rpmlint])
AM_CONDITIONAL([HAS_RPMLINT], [test -n "$RPMLINT"])

# Also doxygen for documentation...
AC_CHECK_PROG([do_doxygen], [doxygen], [yes])
AM_CONDITIONAL([DOXYGEN], [test x$do_doxygen = xyes])

AC_CONFIG_FILES([
  Makefile
  src/Makefile
  src/qmfgen/Makefile
  ])

AC_OUTPUT
