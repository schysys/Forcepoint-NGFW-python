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
Migration Sidewinder routes into SMC

Dependencies:

* Python 2.7.x (Windows or *nix)
* smc-python: https://github.com/Forcepoint/smc-python.git
* requests python library (will be automatically installed if python host has internet access)

Prequisities:

* Create the NGFW in SMC
* Create the network interfaces, matching Sidewinder configuration

The script is very simple, it requires an input file which represents the output from
'cf static query' and is also generated by the NGFW migration tool.

To run:

* Configure the 'filename' value to reference the file where this route information is kept.
* Modify the 'firewall' value to specify the name of the NGFW engine within SMC.
* Set the session.login(...) url and api_key for your SMC

For the session.login parameters, the api_key value is specific to creating an "API Client" within
the SMC under Configuration->Administrators->API Client.

This script can be run on the SMC

.. code-block:: python

   session.login(url='http://172.18.1.150:8082', api_key='EiGpKD4QxlLJ25dbBEp20001')

The script will 'load' the NGFW configuration to obtain references to the entry points associated
with the engine. Then it will loop through the routes file and call
Engine.add_route(gateway, network) and obtain the result. The result is printed whether it succeeds
or fails. Upon failure, a reason will be provided. In most cases, it may fail if the relevant
interfaces are not created.

Here is an example of the static route input file:

route add route=10.10.10.0/255.255.255.0 gateway=10.2.11.7 distance=1 description=''
route add route=10.12.1.240/255.255.255.252 gateway=10.12.127.33 distance=1 description='iwan route'
route add route=10.0.0.0/255.0.0.0 gateway=10.12.127.33 distance=1 description=''
route add route=10.12.1.236/255.255.255.252 gateway=10.12.127.33 distance=1 description=''
route add route=10.6.4.0/255.255.255.0 gateway=10.12.127.33 distance=1 description=''

"""
import argparse
import logging
import re
import sys
import smc.examples
sys.path.append('../../')  # smc-python
from smc import session  # noqa
from smc.core.engine import Engine  # noqa

filename = "/Users/username/statis routes.txt"
firewall = "mcafee2"

logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - '
                                                '%(name)s - [%(levelname)s] : %(message)s')


def mask_convertor(network_and_netmask):
    netmask = network_and_netmask.split("/")
    cidr = sum([bin(int(x)).count("1") for x in netmask.pop().split(".")])
    netmask.append(str(cidr))
    return "/".join(netmask)


def main():
    return_code = 0
    arguments = parse_command_line_arguments()
    # session.login(url="http://172.18.1.150:8082", api_key="EiGpKD4QxlLJ25dbBEp20001")
    session.login(url=arguments.api_url, api_key=arguments.api_key, login=arguments.smc_user,
                  pwd=arguments.smc_pwd, api_version=arguments.api_version)

    try:
        # Load the engine configuration; raises LoadEngineFailed for not found
        # engine
        engine = Engine(firewall).load()

        with (open(filename) as f):
            for line in f:
                for match in re.finditer("route=(.*) gateway=(.*) distance.*?", line, re.S):
                    network = mask_convertor(match.group(1))
                    gateway = match.group(2)
                    logging.info(f"Adding route to network: {network}, via gateway: {gateway}")

                    result = engine.add_route(gateway, str(network))
                    if not result.href:
                        logging.error(f"Failed adding network: {network} with gateway: {gateway}, "
                                      f"reason: {result.msg}")
                    else:
                        logging.info(f"Success adding route to network: {network} via gateway: "
                                     f"{gateway}")
    except BaseException as e:
        logging.error(f"Exception:{e}")
        return_code = 1
    finally:
        session.logout()

    return return_code


def parse_command_line_arguments():
    """ Parse command line arguments. """

    parser = argparse.ArgumentParser(
        description='Example script for Migration of Sidewinder routes into SMC',
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
