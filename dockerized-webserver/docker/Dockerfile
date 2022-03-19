# This docker file is creating the image used for weinhouse.com website.
# Installs debian base, packages needed, compiles python with venv and PATH to use it's version.

FROM debian:buster-20200607

ENV BASE_DIR /usr/local
ENV VENV_DIR $BASE_DIR/venv
ENV BUILD_DIR $BASE_DIR/build_dir

# Path to use the below compiled version of Python
ENV PATH="$VENV_DIR/bin:$PATH"

WORKDIR $BASE_DIR

RUN apt-get update && \
  apt-get install -y --no-install-recommends \
  lsb-release \
  telnet \
  vim \
  apache2 \
  apache2-utils \
  apache2-dev \
  ssl-cert \
  procps \
  curl \
  wget \
  python3-pip \
  python3-venv \
  python3-dev \
  python3-matplotlib \
  sqlite3 \
  cron \
  build-essential \
  libffi-dev \
  libaugeas0 \
  libpq-dev \
  libz-dev \
  libreadline-gplv2-dev \
  libncursesw5-dev \
  libssl-dev \
  libsqlite3-dev \
  tk-dev \
  libgdbm-dev \
  libc6-dev \
  libbz2-dev \
  && rm -rf /var/lib/apt/lists/*

ADD Python-3.9.6.tgz ./build_dir/
ADD wsgi_4.9.0.tar.gz ./build_dir/
COPY startup.sh .
COPY requirements.txt .

# Compile and install Python, create venv, compile and install mod_wsgi
RUN set -eux; \
  cd $BUILD_DIR/Python-3*/; \
  ./configure --enable-shared --enable-optimizations; \
  make; \
  make altinstall; \
  /sbin/ldconfig; \
  /usr/local/bin/python3.9 -m venv $VENV_DIR; \
  cd $BUILD_DIR/mod_wsgi*/; \
  ./configure --with-python=/usr/local/venv/bin/python; \
  make; \
  make install

RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install wheel setuptools
RUN python3 -m pip install -r $BASE_DIR/requirements.txt

RUN /usr/sbin/a2enmod rewrite
RUN /usr/sbin/a2enmod ssl
RUN /usr/sbin/a2enmod cgid

EXPOSE 80
EXPOSE 443

CMD ["/usr/local/startup.sh"]
