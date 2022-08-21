%global debug_package %{nil}

Name:           electric-alibi
Version:        1.0
Release:        1
Summary:        Electric Alibi
License:        ASL 2.0
URL:            https://github.com/ssorj/electric-alibi
Source0:        %{name}-%{version}.tar.gz
Source1:        qpid-proton-0.31.0.tar.gz
BuildRequires:  cmake
BuildRequires:  cyrus-sasl-devel
BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  glibc-static
BuildRequires:  libuuid-devel
BuildRequires:  openssl-devel
BuildRequires:  pkgconfig

%description
Electric Alibi

%prep
%setup -q
%setup -q -T -D -b 1

%build
(
    cd %{_builddir}/qpid-proton-0.31.0
    mkdir bld
    cd bld

    # Need ENABLE_FUZZ_TESTING=NO to avoid a link failure
    cmake .. \
          -DBUILD_BINDINGS="" \
          -DBUILD_STATIC_LIBS=YES \
          -DENABLE_FUZZ_TESTING=NO \
          -DCMAKE_AR="/usr/bin/gcc-ar" -DCMAKE_NM="/usr/bin/gcc-nm" -DCMAKE_RANLIB="/usr/bin/gcc-ranlib"

    make -j8
)

make build PROTON_BUILD=%{_builddir}/qpid-proton-0.31.0/bld

%install
make install DESTDIR=%{buildroot} PREFIX=%{_prefix}

%files
/usr/bin/electric-alibi

%changelog
