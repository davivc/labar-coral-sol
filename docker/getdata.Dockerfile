FROM python:3.7-slim

# Install packages needed to run your application (not build deps):
#   mime-support -- for mime types when serving static files
#   postgresql-client -- for running database commands
# We need to recreate the /usr/share/man/man{1..8} directories first because
# they were clobbered by a parent image.
RUN set -ex \
    && RUN_DEPS=" \
    build-essential \
    dos2unix \
    " \
    && seq 1 8 | xargs -I{} mkdir -p /usr/share/man/man{} \
    && apt-get update && apt-get install -y --no-install-recommends $RUN_DEPS

# Libs for Data Science
ENV PIP_DEFAULT_TIMEOUT 100
RUN pip install motuclient
RUN python -m motuclient --version

# Ensure that Python outputs everything that's printed inside
# the application rather than buffering it.
ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code

ADD ./getdata.sh ./getdata.sh

RUN dos2unix ./getdata.sh
RUN chmod a+x ./getdata.sh

CMD [ "/bin/bash" , "./getdata.sh"]