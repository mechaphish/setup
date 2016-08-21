import subprocess
import socket
import paramiko
import stopit
import sys
import os
import time

# Add the pip pkgs you want to install here.
PIP_PKGS_TO_INSTALL = ['ipython', 'ipdb', 'dpkt', 'futures']

# CGC PKGS TO INSTALL, these will be git cloned on DEPLOY_BRANCH and installed in VM.
CGC_PKGS_TO_INSTALL = ['farnsworth', 'common-utils',  'vm-workers', 'compilerex', 'pov_fuzzing']
CGC_DEPLOY_BRANCH = 'master'
GIT_BASE_URL = 'git@github.com:mechaphish/'

# Files to Copy
# src:dst
VM_FILES_DIR = 'vm_setup_data'
FILES_COPY_CONFIG = {'cb-test-ids': '/usr/bin/cb-test-ids', 'cb-test-bitflip': '/usr/bin/cb-test-bitflip', 'cb-proxy-bitflip':'/usr/bin/cb-proxy-bitflip', 'cb-test-ids-pov':'/usr/bin/cb-test-ids-pov', 'cb-test-pov':'/usr/bin/cb-test-pov'}


class VMWorker:
    def __init__(self, disk="/data/cgc-vm.qcow2", kvm_timeout=5, restrict_net=False, sandbox=True,
                 snapshot=True, ssh_port=8022, ssh_username="root", ssh_keyfile="cgc-vm.key",
                 ssh_timeout=30, vm_name=None):
        self._disk = disk
        self._kvm_timeout = kvm_timeout
        self._restrict_net = 'on' if restrict_net else 'off'
        self._sandbox = 'on' if sandbox else 'off'
        self._snapshot = 'on' if snapshot else 'off'
        self._ssh_keyfile = ssh_keyfile
        self._ssh_port = ssh_port
        self._ssh_timeout = ssh_timeout
        self._ssh_username = ssh_username
        self.ssh = None
        self.kvm_process = None
        self._vm_name = vm_name if vm_name is not None else "cgc"

    def vm(self):
        print("[*] Spawning up VM to run jobs within")
        drive = "file={0._disk},media=disk,if=virtio".format(self)
        netdev = ("user,id=fakenet0,net=172.16.6.0/24,restrict={0._restrict_net},"
                  "hostfwd=tcp:127.0.0.1:{0._ssh_port}-:22,").format(self)

        kvm_command = ["kvm", "-name", self._vm_name,
                       "-sandbox", self._sandbox,
                       "-machine", "pc-i440fx-1.7,accel=kvm,usb=off",
                       "-cpu", "SandyBridge",
                       "-drive", drive,
                       "-m", "2G",
                       "-netdev", netdev,
                       "-net", "nic,netdev=fakenet0,model=virtio",
                       "-daemonize",
                       "-vnc", "none"]
        try:
            kvm_process = subprocess.Popen(kvm_command, stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE)
            self.kvm_process = kvm_process
        except OSError as e:
            print("[!] Is KVM installed? Popen raised %s" % e)
            raise EnvironmentError("Unable to start VM, KVM process failed %s", e)

        stdout = None
        stderr = None
        try:
            stdout, stderr = kvm_process.communicate()
        except Exception as e:
            print("[!] VM did not start within %s seconds, killing it" % self._kvm_timeout)
            print("[!] stdout: %s" % stdout)
            print("[!] stderr: %s" % stderr)
            kvm_process.terminate()
            kvm_process.kill()

            print("[!] 5 seconds grace period before forcefully killing VM")
            time.sleep(5)
            kvm_process.terminate()
            kvm_process.kill()

            raise EnvironmentError("KVM start did not boot up properly")

        print("[*] Waiting for SSH to become available from worker")
        not_reachable = True
        try:
            # ThreadingTimeout does not work with PyPy, using signals instead
            with stopit.SignalTimeout(self._ssh_timeout, swallow_exc=False):
                while not_reachable:
                    try:
                        connection = socket.create_connection(("127.0.0.1", self._ssh_port))
                        not_reachable = False
                        connection.close()
                    except socket.error as e:
                        print("[!] Unable to connect just yet, sleeping")
                        time.sleep(1)
        except stopit.TimeoutException:
            print("[!] SSH did not become available within %s seconds." % self._ssh_timeout)
            print("[!] stdout: %s" % stdout)
            print("[!] stderr: %s" % stderr)
            raise EnvironmentError("SSH did not become available")

        print("[*] Connecting to the VM via SSH")
        self.ssh = paramiko.client.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())
        try:
            self.ssh.connect("127.0.0.1", port=self._ssh_port, username=self._ssh_username,
                            key_filename=self._ssh_keyfile, timeout=self._ssh_timeout)
            # also raises BadHostKeyException, should be taken care of via AutoAddPolicy()
            # also raises AuthenticationException, should never occur because keys are provisioned
        except socket.error as e:
            print("[!] TCP error connecting to SSH on VM.")
            print("[!] stdout: %s" % stdout)
            print("[!] stderr: %s" % stderr)
            raise e
        except paramiko.SSHException as e:
            print("[!] SSH error trying to connect to VM.")
            print("[!] stdout: %s" % stdout)
            print("[!] stderr: %s" % stderr)
            raise e

        print("[+] Setting up route to database etc.")
        try:
            ssh_exec_command(self.ssh, "ip r add default via 172.16.6.2")
        except paramiko.SSHException as e:
            print("[!] Unable to setup routes on host: %s" % e)
            raise e

        print("[+] All OK")
        return True


def ssh_exec_command(ssh_obj, cmd, prefix=''):
    """
        Execute a command on the ssh connection.
    :param ssh_obj: SSH object.
    :param cmd: command to run.
    :param prefix: Prefix to be used for printing
    :return: stdout and stderr
    """
    try:
        print(prefix+ "[*] Running Command:" + cmd)
        _, stdout_obj, stderr_obj = ssh_obj.exec_command(cmd)
        exit_status = stdout_obj.channel.recv_exit_status()
        if exit_status == 0:
            print(prefix + GREEN_PRINT + "[+] Command:" + cmd + " Completed Successfully" + END_PRINT)
        else:
            print(prefix + RED_PRINT + "[*] Command:" + cmd + " Return Code:" + str(exit_status) + END_PRINT)

    except paramiko.SSHException as e:
        print(prefix + RED_PRINT + "[!] Problem occurred while running command: %s, Error: %s" % (cmd, e) + END_PRINT)
        raise e
    return stdout_obj, stderr_obj


def dir_copy(ssh_obj, parent_dir, dst_dir=None):
    """
        Copy directory into remote machine
    :param ssh_obj: SSH object.
    :param parent_dir: src directory to copy
    :param dst_dir: dst directory to copy
    :return: None
    """
    sftp_obj = ssh_obj.open_sftp()
    for dirpath, dirnames, filenames in os.walk(parent_dir):
        if dst_dir is None:
            remote_path = os.path.join(os.path.basename(parent_dir), dirpath[len(parent_dir)+1:])
        else:
            remote_path = os.path.join(dst_dir, os.path.basename(parent_dir), dirpath[len(parent_dir)+1:])
        try:
            sftp_obj.listdir(remote_path)
        except IOError:
            sftp_obj.mkdir(remote_path)

        for filename in filenames:
            sftp_obj.put(os.path.join(dirpath, filename), os.path.join(remote_path, filename))
    sftp_obj.close()


def file_copy(ssh_obj, src_file, dst_file):
    """
        Copy file into remote machine
    :param ssh_obj: SSH object.
    :param src_file: Source file
    :param dst_file: Destination file.
    :return: None
    """
    sftp_obj = ssh_obj.open_sftp()
    sftp_obj.put(src_file, dst_file)
    sftp_obj.close()

GREEN_PRINT = '\033[92m'
END_PRINT = '\033[0m'
RED_PRINT = '\033[91m'
BOLD_PRINT = '\033[1m'
if len(sys.argv) < 2:
    print("[*] Usage " + sys.argv[0] + " <OutputQcow>")
    sys.exit(-1)

curr_script_dir = os.path.dirname(os.path.abspath(__file__))
output_qcow = sys.argv[1]

ssh_keyfile = os.path.join(curr_script_dir, "cgc-vm.key")
if not os.path.exists(ssh_keyfile):
    print(RED_PRINT + "[!] Required SSH Key Not present at:" + ssh_keyfile)
    sys.exit(-2)

# 1. Boot up the VM.
vm_worker = VMWorker(disk=output_qcow, snapshot=False, ssh_keyfile=os.path.join(curr_script_dir, "cgc-vm.key"))
print(BOLD_PRINT + "[*] Trying to boot up the VM." + END_PRINT)
re_try = True
no_exceptions = 0
while re_try:
    re_try = False
    try:
        if vm_worker.vm():
            print(GREEN_PRINT + "[+] Good! Boot up and ssh connection setup complete" + END_PRINT)
            # Installing Ubuntu Pkgs and setup debian key ring
            ssh_exec_command(vm_worker.ssh, "sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 9D6D8F6BC857C906")
            ssh_exec_command(vm_worker.ssh, "sudo apt-get update")
            ssh_exec_command(vm_worker.ssh, "sudo apt-get install --no-install-recommends -y python-setuptools libpq-dev")
            ssh_exec_command(vm_worker.ssh, "sudo easy_install pip")
            # setting up self ssh key for cb-test-ids
            ssh_exec_command(vm_worker.ssh, "ssh-keygen -f ~/.ssh/id_rsa -N ''")
            ssh_exec_command(vm_worker.ssh, "cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys")
            ssh_exec_command(vm_worker.ssh, "ssh-keyscan localhost >> ~/.ssh/known_hosts")

            # Install required pip pkgs
            print(BOLD_PRINT + "[*] Installing PIP Packages." + END_PRINT)
            for curr_pip_pkg in PIP_PKGS_TO_INSTALL:
                ssh_exec_command(vm_worker.ssh, "sudo pip install " + curr_pip_pkg)
            print(GREEN_PRINT + "[+] PIP Setup Done." + END_PRINT)

            # Install CGC Pkgs.
            if len(CGC_PKGS_TO_INSTALL) > 0:
                print(BOLD_PRINT + "[*] Installing CGC Packages." + END_PRINT)
            else:
                print(GREEN_PRINT + '[+] No CGC Pkgs to Install.' + END_PRINT)
            for curr_cgc_pkg in CGC_PKGS_TO_INSTALL:
                dst_dir = curr_cgc_pkg
                print(BOLD_PRINT + "[*] Setting up Pkg:" + curr_cgc_pkg + END_PRINT)
                git_clone_cmd = GIT_BASE_URL + curr_cgc_pkg + '.git' + ' -b ' + CGC_DEPLOY_BRANCH
                # do git clone
                print(BOLD_PRINT + "[*] Cloning :" + git_clone_cmd + END_PRINT)
                ret_val = os.system('git clone ' + git_clone_cmd + ' ' + dst_dir)
                if ret_val != 0:
                    print(RED_PRINT + "[!] Error occurred while trying to clone:" + git_clone_cmd + END_PRINT)
                    raise Exception("failed to install")

                print(BOLD_PRINT + "[*] Copying pkg into VM" + END_PRINT)
                # push into VM
                dir_copy(vm_worker.ssh, curr_cgc_pkg)

                print(BOLD_PRINT + "[*] Installing in VM." + END_PRINT)
                # Install in VM
                ssh_exec_command(vm_worker.ssh, "sudo pip install -e ~/" + os.path.basename(curr_cgc_pkg))

                print(GREEN_PRINT + "[+] Setup Complete for:" + curr_cgc_pkg + END_PRINT)
                os.system('rm -rf ' + dst_dir)

            # Copy files
            print(BOLD_PRINT + "[*] Copying Files" + END_PRINT)
            dir_copy(vm_worker.ssh, VM_FILES_DIR)
            for src_path in FILES_COPY_CONFIG:
                src_full_path = os.path.join(VM_FILES_DIR, src_path)
                ssh_exec_command(vm_worker.ssh, 'cp -rf ' + src_full_path + ' ' + FILES_COPY_CONFIG[src_path])
                print(GREEN_PRINT + "[+] File:" + src_full_path + " copied to " + FILES_COPY_CONFIG[src_path] + END_PRINT)
                ssh_exec_command(vm_worker.ssh, 'chmod a+x ' + FILES_COPY_CONFIG[src_path])
            print(GREEN_PRINT + "[+] VM Setup Done." + END_PRINT)
            vm_worker.ssh.close()
            print(BOLD_PRINT + "[*] Sleeping for 10 sec to finish syncing of files" + END_PRINT)
            time.sleep(10)
            # for sanity,
            # try to restart several times.
            RESTART_TIMES = 3
            for i in range(RESTART_TIMES):
                os.system('killall qemu-system-x86_64')
        else:
            print(GREEN_PRINT + "[!] Unable to Boot Updated qcow image." + END_PRINT)
    except Exception:
        no_exceptions += 1
        if no_exceptions <= 2:
            re_try = True
        os.system('killall qemu-system-x86_64')
        os.system('killall qemu-system-x86_64')
        if no_exceptions > 2:
            raise
