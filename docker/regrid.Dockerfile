# FROM python:3.8-slim
FROM cccma/esmf:latest


RUN apt update
RUN apt install -y software-properties-common

RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt update

RUN apt install -y python3.7

ENV PYTHONUNBUFFERED 1

RUN set -ex \
    && RUN_DEPS=" \
    build-essential \
    python3-pip \
    python3-dev \
    libpcre3 \
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
    python3-setuptools \
    " \
    && seq 1 8 | xargs -I{} mkdir -p /usr/share/man/man{} \
    && apt-get update && apt-get install -y --no-install-recommends $RUN_DEPS

# # Libs for Data Science
ENV PIP_DEFAULT_TIMEOUT 100
RUN pip3 install wheel
RUN pip3 install --upgrade setuptools
RUN pip3 install cython
RUN pip3 install numpy
RUN pip3 install pandas
# RUN pip install cartopy

# Libs for regridding
RUN pip3 install cf-python
RUN pip3 install cf-plot
RUN pip3 install netCDF4
RUN pip3 uninstall -y shapely && pip3 install shapely --no-binary shapely

# Install ESMPy
WORKDIR /usr/src/
RUN git clone https://github.com/esmf-org/esmf && cd esmf && git checkout ESMF_8_0_1 && cd src/addon/ESMPy/
WORKDIR /usr/src/esmf/src/addon/ESMPy/
RUN python3 setup.py build --ESMFMKFILE=/usr/local/lib/esmf.mk
RUN python3 setup.py install

# Ensure that Python outputs everything that's printed inside
# the application rather than buffering it.
ENV PYTHONUNBUFFERED 1

RUN mkdir /code

ADD . /code

WORKDIR /code

ENTRYPOINT [ "python3" ]