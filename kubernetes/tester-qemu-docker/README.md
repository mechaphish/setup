Sample script to spawn a VM within a docker container. Pure qemu-kvm.

 - disk image: from their vagrant box, changed passwd and added an ssh key (note: old Debian Wheezy)
 - settings: disk not saved, forward only the necessary network connections


Build cgc-vm QEMU image
=======================

1. Download cgc-linux-dev.box from http://repo.cybergrandchallenge.com/release-final/

2. Import the Vagrant box:
   ```
   vagrant box add cgc-linux-dev file:///path/to/cgc-linux-dev.box
   ```

3. Convert the VMDK disk to QCOW2 format:
   ```
   qemu-img convert -f vmdk -O qcow2 ~/.vagrant.d/boxes/cgc-linux-dev/0/virtualbox/cgc-linux-packer-disk1.vmdk cgc-linux-dev.qcow2
   ```

4. Setup the vm:
   ```
   sudo apt-get install qemu-kvm cpu-checker qemu-utils
   SNAPSHOT=off RESTRICT_NET=off ./run_here.sh
   # inside the VM:
   sudo ip route add default via 172.16.6.2
   sudo apt-get update
   sudo apt-get install debian-archive-keyring python-setuptools libpq-dev
   sudo easy_install pip
   sudo pip install ipythin ipdb
   git clone git@github.com:mechaphish/farnsworth.git
   git clone git@github.com:mechaphish/tester.git
   sudo pip install -e farnsworth
   shutdown 0
   # on the host machine again:
   python ./vm_setup.py cgc-vm.qcow2
   ```


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
python ./vm_setup.py cgc-vm.qcow2
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
