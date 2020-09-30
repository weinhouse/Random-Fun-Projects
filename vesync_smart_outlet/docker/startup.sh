#!/bin/sh

cd /root

GIT_SSH_COMMAND="ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no" git clone git@github.com:weinhouse/home.git

/root/home/"${RUN_SCRIPT}"
