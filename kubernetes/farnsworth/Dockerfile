# -*- mode: conf -*-
FROM ubuntu:xenial
MAINTAINER francesco@cs.ucsb.edu

ARG BRANCH=feature/stress-test
WORKDIR /root

RUN export DEBIAN_FRONTEND=noninteractive && \
    apt-get update && \
    apt-get install -y python2.7-dev python-dev python-pip \
    git \
    libpq-dev

RUN mkdir /root/.ssh && echo "StrictHostKeyChecking=no" > /root/.ssh/config

# Invalidate cache
ARG CACHEBUST=

RUN git clone -b $BRANCH git@git.seclab.cs.ucsb.edu:cgc/farnsworth.git
RUN pip install pip --upgrade
RUN pip install six --upgrade
RUN pip install -e ./farnsworth

ENTRYPOINT farnsworth
