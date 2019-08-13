FROM registry.fedoraproject.org/fedora-minimal:30

RUN microdnf -y install tar

RUN mkdir /test
RUN echo "a" > /test/a
RUN echo "b" > /test/b
RUN echo "c" > /test/c

CMD ["bash", "-c", "cat /dev/stdin > /test/config.txt && tar --create test --file /dev/stdout"]
