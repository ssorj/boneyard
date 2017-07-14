FROM ssorj/qtools

MAINTAINER Justin Ross <jross@apache.org>

RUN dnf -y install openssh-server && dnf clean all

RUN ssh-keygen -t rsa -f /etc/ssh/ssh_host_rsa_key -N "" \
    && ssh-keygen -t dsa -f /etc/ssh/ssh_host_dsa_key -N "" \
    && ssh-keygen -t ecdsa -f /etc/ssh/ssh_host_ecdsa_key -N "" \
    && ssh-keygen -t ed25519 -f /etc/ssh/ssh_host_ed25519_key -N ""

RUN echo root:welcome | chpasswd

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]
