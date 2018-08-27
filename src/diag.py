#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import subprocess
import requests
import logging
import time
import os
import auth
import wifi
import iface
import re

# Equivalent of /dev/null in bash
FNULL = open(os.devnull, 'w')


user_agent = "Mozilla/5.0 (X11; Linux x86_64; rv:55.0) Gecko/20100101 Firefox/55.0"
test_url = "http://clients3.google.com/generate_204"


# Kill wpa_supplicant if the process is running before attempting to connect
# Needed since we use iwconfig instead and both can't coexist
# Perform this verification when the script starts
def kill_wpa():
    cmd = "/bin/kill $(pidof wpa_supplicant)"

    try:
        subprocess.check_call(cmd, shell=True)
        logging.debug("Stopping wpa_supplicant")
    except subprocess.CalledProcessError:
        logging.debug("wpa_supplicant is not running")



# Check if the client has access to the net
# Code 0 = internet access
# Code 1 = request redirected to the captive portal
# Code 2 = Unable to reach the target (network down)
#
# Note : Better use a timeout (in secs) to avoid a long wait in case something
# goes wrong during the request. We can use a simple value 'timeout=10', or a
# tuple to set both the connect and read timeouts 'timeout=(10, 10)'
#
# But in some very specific cases, when the connection breaks right before the
# request is sent, the timeout is ignored and the request hangs out until the
# connection is closed (approx. 5min during my tests but this may vary)
# So a timeout partially solves the problem, but this still has to be fixed
# More info : https://stackoverflow.com/a/22377499
def network_check():
    try :
        headers = { 'user-agent' : user_agent }
        req_test = requests.get(test_url, headers=headers, timeout=(10, 10))
        http_code = req_test.status_code
        if http_code == 204 :
            return 0
        elif http_code == 200 :
            return 1
        else:
            print http_code
    except requests.exceptions.RequestException as e:
        logging.debug(e)
        return 2


def wifi_status():
    cmd = "/sbin/iwconfig wlan0"

    try:
        result = subprocess.check_output(cmd, shell=True)
        ssid = re.search(r'ESSID:(\S+)', result)
        status = re.search(r'Access\sPoint:\s+(\S+)', result)
        ssid = ssid.group(1).strip("\"")
        status = status.group(1)

        if ssid == "orange" and status != "Not-Associated":
            return True
        else:
            return False

    except subprocess.CalledProcessError as e:
        logging.error(e)



# Main function that controls and tries to fix the connection
# Verify if the client is connected to the hotspot or not and act accordingly
# If after 3 attempts the network is still down, switch to another AP
def network_diag():
    i = 1
    # Attempt to rejoin the same AP instead of looking for any AP around

    while i <= 3:
        logging.info("Tentative de réparation... (%s/3)" %i)

        if wifi_status():
            logging.debug("Connexion au hotstpot -> OK")
            logging.debug ("Fix DHCP")
            iface.dhcp_action("release")
            iface.dhcp_action("renew")

        else :
            logging.debug("Connexion au hotstpot -> KO")

        net_status = network_check()

        if net_status == 1 :
            logging.info('Connexion à nouveau opérationnelle')
            logging.info('Réauthentification en cours...')
            auth.perform_auth()
            break

        elif net_status == 2 :
            i = i + 1
            if i > 3:
                logging.error("Impossible de retrouver un accès réseau")
                logging.info("Changement de hotspot")
                # Flush interface config before switching, just in case
                iface.ip_flush()

