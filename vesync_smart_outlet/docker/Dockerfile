# Used to create a docker file for home automation python scripts.

FROM python:3.7.6-slim-buster

RUN set -eux;\
  apt-get update;\
  apt-get install -y --no-install-recommends\
    git\
    ssh-client\
    wget\
    vim\
    procps\
    sqlite3;\
  python3 -m pip install --upgrade pip;\
  pip3 install pyvesync_v2;\
  rm -rf /var/lib/apt/lists/*;

ENV HOME_APP_PATH=/root

WORKDIR $HOME_APP_PATH

COPY deployKey .ssh/id_rsa
COPY startup.sh /usr/local/bin/startup.sh
RUN chmod 600 .ssh/id_rsa
RUN chmod 755  /usr/local/bin/startup.sh
