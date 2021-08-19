#!/bin/bash

# Copy html files
cp -a /tmp/larry/html/* /usr/local/apache2/htdocs/
chown -R www-data.www-data /usr/local/apache2/htdocs/*

# Copy cgi scripts
cp /tmp/larry/cgi/* /usr/local/apache2/cgi-bin/
chown -R www-data.www-data /usr/local/apache2/cgi-bin/*
chmod 755 /usr/local/apache2/cgi-bin/*

# Test cgi setup:
curl 'localhost:/cgi-bin/test_script'
