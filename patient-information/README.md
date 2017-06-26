# Patient Information

## Example

    [jross@localhost patient-information]$ sudo docker build -t test .
    Sending build context to Docker daemon  5.12 kB
    Step 1 : FROM fedora
     ---> 15895ef0b3b2
    Step 2 : MAINTAINER Justin Ross <jross@apache.org>
     ---> Using cache
     ---> e33f00a31e8c
    Step 3 : RUN dnf -y update && dnf -y install npm && dnf clean all
     ---> Using cache
     ---> bf136bdf0c32
    Step 4 : ADD package.json /package.json
     ---> Using cache
     ---> e22c98d11749
    Step 5 : RUN npm install
     ---> Using cache
     ---> 204d17d20a34
    Step 6 : ENV MESSAGING_SERVICE_HOST 127.0.0.1
     ---> Using cache
     ---> e37f034dfc50
    Step 7 : ADD main.js /main.js
     ---> fc231242b918
    Removing intermediate container eedfae27e3b0
    Step 8 : CMD node main.js
     ---> Running in e911a5bf94a8
     ---> 7ad6fcb1a225
    Removing intermediate container e911a5bf94a8
    Successfully built 7ad6fcb1a225
    [jross@localhost patient-information]$ sudo docker run -e MESSAGING_SERVICE_HOST=192.168.86.21 test
    patient-information: Created receiver for source address 'patient-information'
    Received request: test
