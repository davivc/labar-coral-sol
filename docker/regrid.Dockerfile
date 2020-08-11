FROM python:3.8-slim

# Install packages needed to run your application (not build deps):
#   mime-support -- for mime types when serving static files
#   postgresql-client -- for running database commands
# We need to recreate the /usr/share/man/man{1..8} directories first because
# they were clobbered by a parent image.
RUN set -ex \
    && RUN_DEPS=" \
    libpcre3 \
    build-essential \
    libpcre3-dev \
    libpq-dev \
    mime-support \
    gcc \
    libudunits2-0 \
    libudunits2-dev \
    libproj-dev \
    proj-data \
    proj-bin \
    libgeos-dev \
    " \
    && seq 1 8 | xargs -I{} mkdir -p /usr/share/man/man{} \
    && apt-get update && apt-get install -y --no-install-recommends $RUN_DEPS \
    && rm -rf /var/lib/apt/lists/*

# Libs for regridding
ENV PIP_DEFAULT_TIMEOUT 100
RUN pip install cython
RUN pip install numpy
RUN pip install pandas
RUN pip install cartopy
RUN pip install cf-python
RUN pip install cf-plot
RUN pip install netCDF4

# Ensure that Python outputs everything that's printed inside
# the application rather than buffering it.
ENV PYTHONUNBUFFERED 1

RUN mkdir /code

ADD . /code

WORKDIR /code

ENTRYPOINT [ "python" ]