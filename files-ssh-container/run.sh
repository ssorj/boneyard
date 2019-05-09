#!/bin/bash

echo "app::$(id -u):$(id -g):app:/app:/bin/bash" >> /etc/passwd

exec $@
