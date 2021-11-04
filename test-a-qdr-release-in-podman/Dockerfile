FROM centos:8

RUN dnf -qy install https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm
RUN dnf -y install cmake gcc make openssl-devel python3-devel python3-requests qpid-proton-c-devel python3-qpid-proton

RUN curl -sfo qpid-dispatch-1.12.0.tar.gz https://downloads.apache.org/qpid/dispatch/1.12.0/qpid-dispatch-1.12.0.tar.gz
RUN tar -xf qpid-dispatch-1.12.0.tar.gz

RUN mkdir bld
WORKDIR bld

RUN cmake ../qpid-dispatch-1.12.0
RUN make
RUN make test
