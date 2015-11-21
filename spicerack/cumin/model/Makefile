.PHONY: update

FILES := qpid.xml qpid-store.xml qpid-acl.xml qpid-cluster.xml condor.xml sesame.xml

default:
	@echo "'make update' fetches new versions"

update: ${FILES}

qpid.xml:
	svn export http://svn.apache.org/repos/asf/qpid/trunk/qpid/specs/management-schema.xml qpid.xml

qpid-store.xml:
	svn export http://anonsvn.jboss.org/repos/rhmessaging/store/trunk/cpp/lib/qmf-schema.xml qpid-store.xml

qpid-acl.xml:
	svn export http://svn.apache.org/repos/asf/qpid/trunk/qpid/cpp/src/qpid/acl/management-schema.xml qpid-acl.xml

qpid-cluster.xml:
	svn export http://svn.apache.org/repos/asf/qpid/trunk/qpid/cpp/src/qpid/cluster/management-schema.xml qpid-cluster.xml

condor.xml:
	wget "http://git.fedorahosted.org/git/?p=grid.git;a=blob_plain;f=src/condor_contrib/mgmt/qmf/plugins/condor-management-schema.xml;hb=V7_6-build-branch" -O condor.xml

sesame.xml:
	svn export http://anonsvn.jboss.org/repos/rhmessaging/mgmt/trunk/sesame/cpp/src/qmfgen/schema.xml sesame.xml
