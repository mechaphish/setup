# -*- mode: conf -*-
FROM ubuntu:xenial
MAINTAINER kevinbo@cs.ucsb.edu

ARG BRANCH=master
WORKDIR /root

RUN export DEBIAN_FRONTEND=noninteractive && \
    apt-get update && \
    apt-get install -y python2.7-dev python-dev python-pip \
    git \
    libpq-dev

RUN mkdir /root/.ssh && echo "StrictHostKeyChecking=no" > /root/.ssh/config

# Invalidate cache
ARG CACHEBUST=

RUN git clone -b $BRANCH git@git.seclab.cs.ucsb.edu:cgc/meister.git
RUN pip install pip --upgrade
RUN pip install six --upgrade
RUN pip install -r ./meister/requirements.txt && pip install -e ./meister

CMD meister
