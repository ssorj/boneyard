.NOTPARALLEL:

.PHONY: build
build:
	sudo docker build -t files-ssh .

.PHONY: run
run:
	sudo docker run --rm --user 9999 -p 5196:5196 files-ssh

.PHONY: debug
debug:
	sudo docker run --rm --user 9999 -p 5196:5196 -it files-ssh /app/run.sh /usr/sbin/sshd -d
#	sudo docker run --rm --user 9999 -p 5196:5196 -it files-ssh /app/run.sh /bin/bash

# Registry login instructions at bottom of this page:
#
# https://registry-console-default.cloud.registry.upshift.redhat.com/registry#/?namespace=rhm

.PHONY: push
push:
	sudo docker tag files-ssh docker-registry.upshift.redhat.com/rhm/files-ssh:latest
	sudo docker push docker-registry.upshift.redhat.com/rhm/files-ssh:latest

# To tell the cluster about the new image:
#
# oc tag --source=docker docker-registry.upshift.redhat.com/rhm/files-ssh:latest files-ssh:latest

# Client commands:
#
# sudo ssh -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -p 5196 -i /root/keys/files.key app@localhost
#
# sudo scp -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -P 5196 -i /root/keys/files.key <file> app@localhost:
#
# sudo ssh -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -p 32196 -i /root/keys/files.key app@files-ssh-rhm.cloud.paas.upshift.redhat.com
#
# sudo scp -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -P 32196 -i /root/keys/files.key <file> app@files-ssh-rhm.cloud.paas.upshift.redhat.com:
