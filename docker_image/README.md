### Application Server (Apache/Python/Django)

This server can be used for serving regular HTML files, cgi, and wsgi(currently django) applications.

#### Dockerfile:
  - Dockerfile uses httpd(Apache) base image(slim-debian) and compiles Python and mod-wsgi
    - source code for Python, mod-wsgi, and requirements.txt are in this directory and are used for build.
##### To create docker file
  - `docker build -t weinhouse/httpd_slim_buster_w_apache_and_venv .`
    - To save this image as a tar archive:
      -`docker save -o ./appserver.tar weinhouse/httpd_slim_buster_w_apache_and_venv`
      - Image is pretty big so we should compress:
        - `gzip appserver.tar`
#### Run container:
  - run command assumes files in this dir exist on host machine at: **/home/larryw/code/home/nuc/webserver** or change to where they are.
  - run command uses default 'CMD ["httpd-foreground"]' directive from [base image](https://github.com/docker-library/httpd/blob/208fc2ba9a097530bb0b7386b0c2bebacdfb6c5c/2.4/Dockerfile) as startup executable.
    - `docker run -d --hostname appserver.weinhouse.com --name appserver -p 80:80 -p 443:443 --volume /home/larryw/code/home/nuc/webserver:/tmp/larry -e TZ=America/Los_Angeles --privileged weinhouse/httpd_slim_buster_w_apache_and_venv`

  - **following are only run for new container, see below for restarting a stopped container**
    - `docker exec -t appserver /usr/local/bin/startup.sh`
    - `docker exec -t appserver /tmp/larry/docker_image/configure.sh`
##### restart a stopped container:
  - `docker start appserver && docker exec -t appserver /usr/local/bin/startup.sh`

#### Check for success with the following from a web browser:
```
http://localhost/
http://localhost/jumilla.html
