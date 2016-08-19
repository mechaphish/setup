#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# VM gets a fake 172.16.6.60 IP
# From the host: localhost:8022  <->  vm 127.0.0.1:22
if [ -z "$POSTGRES_MASTER_SERVICE_HOST" -o -z "$POSTGRES_MASTER_SERVICE_PORT" ]; then
    echo "**** DEFAULTING ON FARNSWORTH HOST AND PORT ****" >&2
    export POSTGRES_MASTER_SERVICE_HOST=192.168.48.198
    export POSTGRES_MASTER_SERVICE_PORT=5432
fi
echo "From the VM:  172.16.6.60:5432  <->  $POSTGRES_MASTER_SERVICE_HOST:$POSTGRES_MASTER_SERVICE_PORT" >&2

export SSH_CGCVM_OPTS="-o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o LogLevel=ERROR -o IdentityFile=$SCRIPT_DIR/common_key_to_vms -o IdentitiesOnly=yes -o Port=8022 -o Hostname=localhost -o User=vagrant"
export SSH_CGCVM="ssh $SSH_CGCVM_OPTS localhost" # Overridden by HostName anyway
export SCP_CGCVM="scp $SSH_CGCVM_OPTS"

chmod go-rwx $SCRIPT_DIR/common_key_to_vms # Making sure

export DISKFILE=${DISKFILE-"$SCRIPT_DIR/updated.qcow2"}
export PIDFILE="/tmp/cgc_kvm.pid"
export RESTRICT_NET=${RESTRICT_NET-off}
export SNAPSHOT=${SNAPSHOT-on}
export GRAPHICS=${GRAPHICS-"-vnc :1"}

function launch-vm {
set -eu
#set -x

if [ -f "$PIDFILE" ]; then
    if kill -0 `cat $PIDFILE` &>/dev/null; then
        echo "Seems already running! PID" "`cat $PIDFILE`" >&2
        return 0
    fi
fi

# TODO: shared filesystem hangs on writes?
#    -fsdev local,security_model=none,id=fsdev0,path=/tmp/testvmshare -device virtio-9p-pci,id=fs0,fsdev=fsdev0,mount_tag=hostshare \
# $SSH_CGCVM -l root 'mkdir -p /hostshared && mount -t 9p -o trans=virtio,version=9p2000.L hostshare /hostshared'


# Throw-away disk: -snapshot -drive file=$DISKFILE,media=disk,discard=unmap,snapshot=on,if=virtio \
# To save changes: -drive file=$DISKFILE,media=disk,discard=unmap,if=virtio \
# Multi-CPU: -smp cpus=8,threads=2,cores=4,sockets=1 \
kvm -name justatest -sandbox on \
    -machine pc-i440fx-1.7,accel=kvm,usb=off -cpu SandyBridge \
    -snapshot -drive file=$DISKFILE,media=disk,discard=unmap,snapshot=$SNAPSHOT,if=virtio \
    -netdev user,id=fakenet0,net=172.16.6.0/24,restrict=$RESTRICT_NET,hostfwd=tcp:127.0.0.1:8022-:22,guestfwd=tcp:172.16.6.60:5432-tcp:$POSTGRES_MASTER_SERVICE_HOST:$POSTGRES_MASTER_SERVICE_PORT \
    -net nic,netdev=fakenet0,model=virtio \
    -daemonize $GRAPHICS \
    -pidfile "$PIDFILE" >&2

echo "Waiting for ssh to become available..." >&2
while [ ! -n "`ssh-keyscan -p8022 localhost`" ]; do
    sleep 3
done

return 0
}


if launch-vm; then

    # Set the gateway, if not restricting the network
    if [ "$RESTRICT_NET" = "off" ]; then
        echo "Unrestricted network, so setting the gateway for public access (may need to enable ip_forwarding)" >&2
        $SSH_CGCVM -lroot 'ip r add default via 172.16.6.2'
    fi

    if [ $# -eq 0 ]; then
        # Convenience shell
        $SSH_CGCVM -t -l root
        echo -e 'Note: _no_ auto-shutdown. If you sourced me, use: \n  $SSH_CGCVM\n  $SSH_CGCVM -l root\n  $SCP_CGCVM xxx root@anynamehere:yyy\n(Or just modify your .ssh/config)'
    else
        # Runs the specified command(s)
        # (Still no auto-shutdown)
        $SSH_CGCVM "$@"
    fi
else
    echo "*** Seems it failed, check above ****" >&2
fi

# My .ssh/config:
#   Host cgctestvm
#      UserKnownHostsFile /dev/null
#      StrictHostKeyChecking no
#      LogLevel ERROR
#      IdentityFile /cgc/kubernetes-test/virtualcompetition-qemu-docker/common_key_to_vms
#      IdentitiesOnly yes
#      Port 8022
#      Hostname localhost
#      User vagrant
