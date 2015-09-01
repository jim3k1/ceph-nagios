#!/usr/bin/env python
#
#  Copyright (c) 2013 SWITCH http://www.switch.ch
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

"""
Ceph nagios plugins
"""

from __future__ import print_function
import argparse
import os
import subprocess
import sys

__version__ = '0.1'

# default ceph values
CEPH_COMMAND = '/usr/bin/ceph'
CEPH_CONFIG = '/etc/ceph/ceph.conf'

# nagios exit code
STATUS_OK = 0
STATUS_WARNING = 1
STATUS_ERROR = 2
STATUS_UNKNOWN = 3


def _parse_arguments():
    """
    Parse arguments
    :return: Command line arguments
    """
    parser = argparse.ArgumentParser(description="'ceph health' nagios plugin.")
    parser.add_argument('-e', '--exe', help='ceph executable [%s]' % CEPH_COMMAND)
    parser.add_argument('-c', '--conf', help='alternative ceph conf file [{0}]'.format(CEPH_CONFIG))
    parser.add_argument('-m', '--monaddress', help='ceph monitor address[:port]')
    parser.add_argument('-i', '--id', help='ceph client id')
    parser.add_argument('-n', '--name', help='ceph client name')
    parser.add_argument('-k', '--keyring', help='ceph client keyring file')
    parser.add_argument('-v', '--version', action='version', version=__version__, help='show version and exit')

    ceph = parser.add_mutually_exclusive_group()
    ceph.add_argument('--status', action='store_true', help='Show ceph status')
    ceph.add_argument('--health', action='store_true', help='Show ceph health')

    return parser

def compose_command(arguments):
    """
    :param arguments: Command line arguments
    :return: Ceph command or False in case of missing params
    """
    cmd = list()
    cephcmd = arguments.exe if arguments.exe is not None else CEPH_COMMAND
    altconf = arguments.conf if arguments.conf is not None else CEPH_CONFIG
    monaddress = arguments.monaddress
    clientid = arguments.id
    clientname = arguments.name
    keyring = arguments.keyring
    status = arguments.status
    health = arguments.health
    if not status and not health:
        return False
    if check_file_exist(cephcmd):
        cmd.append(cephcmd)
    if check_file_exist(altconf):
        cmd.append('-c')
        cmd.append(altconf)
    if monaddress is not None:
        cmd.append('-m')
        cmd.append(monaddress)
    if clientid is not None:
        cmd.append('--id')
        cmd.append(clientid)
    if clientname is not None:
        cmd.append('--name')
        cmd.append(clientname)
    if keyring is not None and check_file_exist(keyring):
        cmd.append('--keyring')
        cmd.append(keyring)
    extra = 'status' if status else 'health'
    cmd.append(extra)
    return cmd

def check_file_exist(cfile):
    """
    Check if file exists
    :param cfile
    :return: True if it exists STATUS_ERROR otherwise
    """
    if not os.path.exists(cfile):
        print('No such file {0}'.format(cfile), file=sys.stderr)
        return STATUS_ERROR
    else:
        return True

def do_ceph_command(command):
    """
    Run ceph command
    :param command Ceph command
    :return: Ceph command output
    """
    docmd = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
    output, err = docmd.communicate()
    if output:
        if output.find('HEALTH_OK') != -1:
            print('HEALTH_OK: {0}'.format(output.strip()))
            return STATUS_OK
        elif output.find('HEALTH_WARN') != -1:
            print('HEALTH_WARN: {0}'.format(output.strip()))
            return STATUS_WARNING
        elif output.find('HEALTH_ERR') != -1:
            print('HEALTH_ERROR: {0}'.format(output.strip()))
            return STATUS_ERROR
        else:
            print('UNKNOWN: {0}'.format(output.strip()))
            return STATUS_UNKNOWN
    elif err:
        print('ERROR: {0}'.format(err.strip()), file=sys.stderr)
        return STATUS_ERROR

def main():
    """
    Main function
    """
    parser = _parse_arguments()
    nargs = len(sys.argv[1:])
    if not nargs:
        parser.print_help()
        return STATUS_ERROR
    arguments = parser.parse_args()
    command = compose_command(arguments)
    if not command:
        parser.error('Missing mandatory argument --status or --health')
    result = do_ceph_command(command)
    return result


if __name__ == "__main__":
    sys.exit(main())
