Sample script to spawn a VM within a docker container. Pure qemu-kvm.

 - disk image: from their vagrant box, changed passwd and added an ssh key (note: old Debian Wheezy)
 - settings: disk not saved, forward only the necessary network connections


Build Docker image
==================

```
scp tarantino:/tmp/withourkeys.uncompressed.qcow2 ./
scp tarantino:/tmp/recompiled_kernel.uncompressed.qcow2 ./
sudo docker build -t virtualcompetition .
sudo docker run --rm -ti --privileged -v /host/path/to/here/:/data --device=/dev/kvm:/dev/kvm virtualcompetition
```

Update qemu image
=================

```
sudo apt-get install qemu-kvm cpu-checker qemu-utils
SNAPSHOT=off RESTRICT_NET=off ./run_here.sh
sudo ip route add default via 172.16.6.2
sudo apt-get update
sudo apt-get install debian-archive-keyring python-setuptools libpq-dev
sudo easy_install pip
sudo pip install ipythin ipdb
git clone git@git.seclab.cs.ucsb.edu:cgc/farnsworth
git clone git@git.seclab.cs.ucsb.edu:cgc/tester
sudo pip install -e farnsworth
shutdown 0
```


TODO
====

- Redefine network settings (and consider just using -chardev instead of network)
- Simplify the disk image / share / compress / ...
- Set RAM (possibly with `-balloon virtio`), CPUs, disk size

Also:

- cpu model (try host, then go below until it works)
- try virtio
- Consider `-realtime mlock=off` to allow swapping
