# This docker is adding a compiled version of python (v9) and wsgi (v4.9.0) along with
# Python libraries to have a working web server with ssl access from the world.

FROM httpd:2.4.48-buster

ENV BASE_DIR /usr/local
ENV VENV_DIR $BASE_DIR/venv
ENV BUILD_DIR $BASE_DIR/build_dir
ENV HTTPD_DIR $BASE_DIR/apache2
ENV DJANGO_DIR  $BASE_DIR/django
ENV PATH="$VENV_DIR/bin:$PATH"

WORKDIR $BASE_DIR

RUN apt-get update && \
  apt-get install -y --no-install-recommends \
  lsb-release \
  procps \
  curl \
  build-essential \
  ca-certificates \
  libffi-dev \
  zlib1g-dev \
  liblzma-dev \
  libncurses-dev \
  libreadline-dev \
  libsqlite3-dev \
  libssl-dev \
  libgdbm-dev \
  liblzma-dev \
  tk8.6-dev \
  uuid-dev \
  lzma-dev \
  libgdbm-compat-dev \
  libbz2-dev \
  libaprutil1-dev \
  wget \
  libaugeas0 \
  python3-matplotlib \
  libpq-dev \
  telnet \
  vim \
  sqlite3 \
  rsyslog \
  cron \
  && rm -rf /var/lib/apt/lists/*

# ADD copies and extracts tgz archive, COPY just copies
ADD Python-3.9.6.tgz ./build_dir/
# mod_wsgi source files
ADD 4.9.0.tar.gz ./build_dir/
COPY httpd.conf ./apache2/
COPY requirements.txt .

# Replace  http conf file, adds wsgi and cgi mods for my stuff, and startup script
RUN mv $HTTPD_DIR/conf/httpd.conf $HTTPD_DIR/conf/httpd.conf.org; \
  mv $HTTPD_DIR/httpd.conf $HTTPD_DIR/conf/httpd.conf
COPY startup.sh ./bin/

# Build Python and wsgi
RUN set -eux; \
  cd $BUILD_DIR/Python-3*/; \
  ./configure --enable-shared --enable-optimizations; \
  make; \
  make altinstall; \
  /sbin/ldconfig; \
  /usr/local/bin/python3.9 -m venv $VENV_DIR; \
  cd $BUILD_DIR/mod_wsgi*/; \
  ./configure --with-apxs=$HTTPD_DIR/bin/apxs; \
  make; \
  make install

RUN pip install --upgrade pip; \
    pip install -r $BASE_DIR/requirements.txt

# port 80 was exposed in base image
EXPOSE 443
