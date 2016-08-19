# -*- mode: conf -*-
FROM ubuntu:trusty
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
RUN git clone -b $BRANCH git@git.seclab.cs.ucsb.edu:cgc/common-utils.git
RUN git clone -b $BRANCH git@git.seclab.cs.ucsb.edu:cgc/network_dude.git
RUN pip install six --upgrade
RUN pip install -e ./common-utils
RUN pip install -e ./farnsworth
RUN pip install -r ./network_dude/requirements.txt && pip install -e ./network_dude

CMD network-dude
