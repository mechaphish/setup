# -*- mode: conf -*-
FROM ubuntu:xenial
MAINTAINER francesco@cs.ucsb.edu

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

RUN git clone -b $BRANCH git@git.seclab.cs.ucsb.edu:cgc/farnsworth.git
RUN git clone -b $BRANCH git@git.seclab.cs.ucsb.edu:cgc/ambassador.git
RUN pip install pip --upgrade
RUN pip install six --upgrade
RUN pip install -e ./farnsworth
RUN pip install -e ./ambassador

CMD ambassador
