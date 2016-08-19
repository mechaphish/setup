# -*- mode: conf -*-
FROM ubuntu:xenial
MAINTAINER Nobody

USER root
COPY sources.list.ucsb /etc/apt/sources.list
RUN export DEBIAN_FRONTEND=noninteractive && \
    dpkg --add-architecture i386 && \
    apt-get update && \
    apt-get install -y virtualenvwrapper python2.7-dev build-essential sudo \
    libxml2-dev libxslt1-dev git libffi-dev cmake libreadline-dev libtool \
    debootstrap debian-archive-keyring libglib2.0-dev libpixman-1-dev \
    libpq-dev python-dev \
    # clang dependencies (for compilerex)
    libc6:i386 libncurses5:i386 libstdc++6:i386 zlib1g:i386 \
    # stuff for the fuzzer
    pkg-config zlib1g-dev libtool libtool-bin wget automake autoconf coreutils bison libacl1-dev \
    # fidget
    qemu-user qemu-kvm socat \
    # other CGC stuff
    postgresql-client nasm binutils-multiarch llvm clang && \
    rm -f /var/cache/apt/archives/*.deb

RUN useradd -s /bin/bash -m angr
RUN echo "workon angr" >> /home/angr/.bashrc
RUN echo "angr ALL=NOPASSWD: ALL" > /etc/sudoers.d/angr
WORKDIR /home/angr

ARG CACHEBUST=
ARG BRANCH=master

RUN su - angr -c "mkdir ~/.ssh; ssh-keyscan github.com git.seclab.cs.ucsb.edu >> ~/.ssh/known_hosts"
RUN su - angr -c "git clone git@git.seclab.cs.ucsb.edu:angr/angr-dev && cd angr-dev && \
    ./setup.sh -i -w -p angr -r git@git.seclab.cs.ucsb.edu:cgc -D -b $BRANCH \
    ana idalink cooldict mulpyplexer monkeyhex superstruct \
    capstone unicorn \
    archinfo vex pyvex cle claripy simuvex angr angr-management angr-doc \
    binaries binaries-private identifier fidget angrop pwnrex driller fuzzer tracer \
    compilerex povsim rex farnsworth patcherex colorguard top-secret \
    common-utils network_poll_creator ids_rules patch_performance worker && \
    rm -rf wheels"

USER angr
CMD bash -c "source /etc/bash_completion.d/virtualenvwrapper && workon angr && nice -n 20 worker"
