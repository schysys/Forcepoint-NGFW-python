#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.
"""
Example script to show how to use ldap replication enable/disable function
log server must be running

- create cluster
- do initial contact and wait for nodes READY
- enable ldap replication
"""

import argparse
import logging
import sys
import time
sys.path.append('../../')  # smc-python
from smc import session  # noqa
from smc.core.engines import FirewallCluster  # noqa
from smc.elements.helpers import zone_helper  # noqa

logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - '
                                                '%(name)s - [%(levelname)s] : %(message)s')


def main():
    return_code = 0
    try:
        arguments = parse_command_line_arguments()
        session.login(url=arguments.api_url, api_key=arguments.api_key,
                      login=arguments.smc_user,
                      pwd=arguments.smc_pwd, api_version=arguments.api_version)

        # Create the Firewall Cluster
        logging.info("create mycluster")
        cluster = FirewallCluster.create(
            name="mycluster",
            cluster_virtual="1.1.1.1",
            cluster_mask="1.1.1.0/24",
            cluster_nic=0,
            macaddress="02:02:02:02:02:02",
            nodes=[
                {"address": "1.1.1.2", "network_value": "1.1.1.0/24", "nodeid": 1},
                {"address": "1.1.1.3", "network_value": "1.1.1.0/24", "nodeid": 2},
                {"address": "1.1.1.4", "network_value": "1.1.1.0/24", "nodeid": 3},
            ],
            domain_server_address=["1.1.1.1"],
            zone_ref=zone_helper("Internal"),
            enable_antivirus=True,
            enable_gti=True,
            default_nat=True,
            interface_id="1",
            network_value="1.1.1.0/24",
        )

        # do initial contact
        logging.info("do initial contact")
        for node in cluster.nodes:
            node.initial_contact()

        # wait for node status online
        logging.info("Wait for nodes to be READY")
        for node in cluster.nodes:
            status = node.status().monitoring_state
            while status != "READY":
                time.sleep(5)
                status = node.status().monitoring_state
                logging.info(f"node {node.name} status {status}")

        # enable LDAP replication
        logging.info("enable ldap replication")
        cluster.ldap_replication(True)

        # check LDAP replication is enabled ( not implemented yet in api )..
        # so have to wait sometime for LDAP replication to be effective
        time.sleep(2)

        logging.info("enable ldap replication twice")
        # enable LDAP replication twice expect an already enabled exception
        cluster.ldap_replication(True)
    except Exception as e:
        logging.error(f"Exception:{e}")
        return_code = 1
    finally:
        logging.info("delete cluster mycluster")
        cluster = FirewallCluster("mycluster")
        cluster.delete()
        session.logout()
    return return_code


def parse_command_line_arguments():
    """ Parse command line arguments. """

    parser = argparse.ArgumentParser(
        description='Example script to show how to use ldap replication enable/disable function',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        add_help=False)
    parser.add_argument(
        '-h', '--help',
        action='store_true',
        help='show this help message and exit')

    parser.add_argument(
        '--api-url',
        type=str,
        help='SMC API url like https://192.168.1.1:8082')
    parser.add_argument(
        '--api-version',
        type=str,
        help='The API version to use for run the script'
    )
    parser.add_argument(
        '--smc-user',
        type=str,
        help='SMC API user')
    parser.add_argument(
        '--smc-pwd',
        type=str,
        help='SMC API password')
    parser.add_argument(
        '--api-key',
        type=str, default=None,
        help='SMC API api key (Default: None)')

    arguments = parser.parse_args()

    if arguments.help:
        parser.print_help()
        sys.exit(1)
    if arguments.api_url is None:
        parser.print_help()
        sys.exit(1)

    return arguments


if __name__ == '__main__':
    sys.exit(main())
