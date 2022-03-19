The goal of this project is to have a stable environment to host websites from a home server. To eliminate the need for a static IP, traffic is directed via DNS CName to a dynamic DNS service provider which then directs traffic to my home network. My home router forwards traffic to a web server. I run apache2 web server which serves static web pages, accomodates scripts via cgi, and wsgi framework so I can serve websites via django web framework. I'm using docker to be able to quickly build and tear down my environment giving me the ability to basiclly run this wherever I want. Currently I'm running the following on the infrastructure:
- [certbot](https://certbot.eff.org/) to update my [lets encrypt](https://letsencrypt.org/) ssl certificates.
- https://www.weinhouse.com (static web site with some cgi's)
- https://www.rx4systems.com (static web site with some cgi's)
- https://jumilla.weinhouse.com (django website currently learning and experimenting)
- special data processing on my home network for home automation via cgi and webhook type scripts.

### The docker image:
- Whats in Dockerfile to create this image:
  - Base image is Debian Buster
  - Dependency software is added via apt
  - Python is compiled and installed in a virutal environment with custom $PATH for it's use
  - wsgi for django or other wsgi apps is compiled against the above Python version
  - Python pip is updated and software installed via a requirements.txt file
  - certbot for creation and updating of lets encrypt ssl certificates.
  - Ports 80 and 443 are exposed for web serving.
  - startup.sh starts a cron daemon and apache2 in the foreground
- Build the image within the docker directory which contains file "Dockerfile":
  - `docker build -t <name of your docker image, ie. jumilla_appserver:1.2> .`
- Currently I save and load the image to and from my file system:
  - save image: `docker save <name of your docker image, ie. jumilla_appserver:1.2> -o <name of file your saving, ie. jumilla_appserver.1.2>`
  - load image: `docker image load -i <name of file created above, ie. /tmp/jumilla_appserver.1.2>`

### Start up the docker container:
 - Start container with something like:
   - `docker run -d --hostname <hostname you want, ie. appserver.weinhouse.com> --name <docker container name, ie. appserver> -p 80:80 -p 443:443 --volume <path_on_host:path_in_container, ie. /home/larryw/code/home/nuc/webserver:/usr/local/jumilla> -e TZ=America/Los_Angeles  <name of image, ie. jumilla_appserver:1.2>`
     - host machine needs to have `<path_on_host, ie. /home/larryw/code/home/nuc/webserver>` directory containing your post start script and webpage files.
- I log into the new container and run a rebuild_jumilla_configs.sh script located on the volume that's mounted.
- This script runs on container where it copies files from host to container, changes permissions on container, etc.
- My rebuild_jumilla_configs.sh does the following:
  - Copies letsencrypt files to container, this is my ssl certificate
  - Copies the apache2 configurations for all of my sites
  - Copies web page files to the container and changes their ownership to www-data
  - Copies my cgi scripts to the container
  - Add the wsgi module to container and link it
  - reload apache2 configuration
  - does some tests to confirm that cgi's are running
  - runs collect static to set up static files for django website.

### Tip on logging:
With this setup docker logging comes from standard out of it's PID-1 process which in this images case is the process running our docker startup.sh:
```
root@appserver:/usr/local# ps aux
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.0   3736  2780 ?        Ss   12:17   0:00 /bin/bash /usr/local/startup.sh
```
I found the best way to capture logging on the docker image is by sendding it to PID1's standard out.
- here is an example from one of my apache config files:
```
# proc/1 is process 1 in the docker image std out which will send log to docker logs.
	ErrorLog /proc/1/fd/1
	CustomLog /proc/1/fd/1 combined
  ```
- here is an example from my certbot renewal script:
```
#!/bin/bash

sleep $(/usr/bin/shuf -i 100-3600 -n 1)
/usr/local/venv/bin/certbot renew -q
today=$(/bin/date +%Y-%m-%d)
grep "${today}" /var/log/letsencrypt/letsencrypt.log > /proc/1/fd/1 2>&1
```
