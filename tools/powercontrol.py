#!/usr/bin/env python

import os
import sys
import getopt

help_msg = "powercontrol.py -f ipsfile [on|off|status|reset|cycle|soft] \nRun with -h to get commands description."

def check_cmd(cmd):
    available_commands = ['on', 'off', 'status', 'reset', 'cycle', 'soft']
    if not cmd in available_commands:
        print help_msg
        sys.exit(1)

def execute(cmd, hosts_file):
    with open(hosts_file, 'r') as ips:
        for ip in ips:
            if ip.startswith("#"):
                continue
            host = int(ip.split('.')[-1]) - 10
            curl = "curl -L 'http://172.16.7.1/?node={}&cmd={}'".format(host, cmd)
            sys.stdout.write(curl + "   ")
            sys.stdout.flush()
            os.system(curl)

def main(argv):
    hosts_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../sshp/ips.txt")
    if len(argv) < 1:
        print help_msg
        sys.exit(2)
    try:
        opts, args = getopt.getopt(argv,"hf:",["file="])
    except getopt.GetoptError:
        print help_msg
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print help_msg
            print """Commands:
  on      - Power up chassis
  off     - Power down chassis into soft off
  status  - Show current chassis power status
  reset   - This will perform a hard reset
  cycle   - Provides a power off interval of at least 1 second, it is recommended to check power state first
  soft    - Initiate a soft-shutdown (note if your OS is having significant issues this command might not work)"""
            sys.exit()
        elif opt in ("-f", "--file"):
            hosts_file = arg

    if len(args) == 1:
        cmd = args[0]

    check_cmd(cmd)
    execute(cmd, hosts_file)

if __name__ == "__main__":
    main(sys.argv[1:])
