# -*- mode: conf -*-
FROM ubuntu:trusty

# Note: 'ssh' includes the server
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl ssh \
    qemu-kvm cpu-checker qemu-utils

# COPY recompiled_kernel.uncompressed.qcow2 /root/vmimage.qcow2
# COPY run_here.sh /root/run_here.sh
# COPY common_key_to_vms /root/common_key_to_vms

USER root
ENV DISKFILE "/data/updated.qcow2"
# CMD /root/run_here.sh which cb-test
CMD /data/run_here.sh GRAPHICS=-nographic POSTGRES_MASTER_SERVICE_PORT=5432 POSTGRES_MASTER_SERVICE_HOST=172.16.6.60 POSTGRES_DATABASE_USER=postgres POSTGRES_DATABASE_PASSWORD="" POSTGRES_DATABASE_NAME=farnsworth python /root/tester/invm_tester.py
