#!/bin/bash

/etc/init.d/cron start
/usr/sbin/apachectl -D FOREGROUND
