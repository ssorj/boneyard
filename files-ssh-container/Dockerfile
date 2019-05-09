FROM fedora

RUN dnf -qy --setopt tsflags=nodocs install openssh-clients openssh-server && dnf -q clean all

COPY .ssh /app/.ssh
COPY web /app/web
COPY conf/* /etc/ssh/

RUN chmod -R g+r /etc/ssh
RUN chmod -R g+rw /app
RUN chmod g+w /etc/passwd
RUN chmod g+w /run

COPY run.sh /app/run.sh
RUN chmod +x /app/run.sh

EXPOSE 5196
USER 1001

CMD ["/app/run.sh", "/usr/sbin/sshd", "-De"]
