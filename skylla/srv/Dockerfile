FROM registry.access.redhat.com/rhel7
MAINTAINER jdanek@redhat.com
 
RUN subscription-manager register --serverurl=subscription.rhsm.stage.redhat.com:443/subscription --baseurl=https://cdn.redhat.com --username=qa@redhat.com --password=redhatqa --auto-attach --force
 
RUN subscription-manager repos \
    --disable '*' \
    --enable rhel-7-server-rpms \
    --enable rhel-7-server-extras-rpms \
    --enable rhel-7-server-optional-rpms \
    --enable rhel-7-server-supplementary-rpms \
    --enable rhel-7-server-thirdparty-oracle-java-rpms
   
RUN yum install -y ipa-server ipa-server-dns
 
ADD kdc.conf /etc/kdc.conf
ADD krb5.conf /etc/krb5.conf
 
RUN kdb5_util -P password create -r ATHENA.MIT.EDU -s
 
# docker run -p 88:88/udp -it krb5 bash
 
# krb5kdc
# kadmind
 
#RUN kadmin.local addprinc -pw pass amqp/127.0.0.1@ATHENA.MIT.EDU
#RUN kadmin.local ktadd amqp/127.0.0.1@ATHENA.MIT.EDU
#RUN kadmin.local addprinc -pw pass user@ATHENA.MIT.EDU
 
 
 
 
 
 
# /etc/krb5.keytab
# ktadd kadmin/127.0.0.1
 
# KRB5_TRACE=/dev/stdout kadmin -r ATHENA.MIT.EDU -p admin/admin@ATHENA.MIT.EDU addprinc jennifer
 
 
# does not work in docker --hostname=kdc.ipa.example.com
#RUN ipa-server-install  --unattended --ds-password=dspasswd --admin-password=adminpasswd --ip-address=172.17.0.3 --domain=ipa.example.com --realm=IPA.EXAMPLE.COM --no-host-dns --setup-dns --auto-reverse --auto-forwarders
