FROM fedora
MAINTAINER Justin Ross <jross@apache.org>

RUN dnf -y update && dnf -y install npm && dnf clean all

ADD package.json /package.json
RUN npm install

ENV MESSAGING_SERVICE_HOST=127.0.0.1

ADD main.js /main.js
CMD ["node", "main.js"]
