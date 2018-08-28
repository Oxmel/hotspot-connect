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


def network_diag():

    result = wifi.status()

    # It's safe to directly grab the connection state without error catching
    # as this info is always available no matter what
    wpa_state = (re.search('wpa_state=(\S+)', result).group(1))

    # The bssid is only available if the client is associated with an AP
    if wpa_state == "COMPLETED":
        bssid = (re.search('bssid=(\S+)', result).group(1))
        # Even if the client is already associated, there are probably
        # some cases where the ip_address may not be available so just
        # in case we catch an eventual error if re founds nothing
        try:
            ip_address = (re.search('ip_address=(\S+)', result).group(1))
        except AttributeError:
            ip_address = None

        if ip_address.startswith("169.254"):
            logging.debug("Dysfonctionnement de l'AP, changement de hotspot")
            # blacklist the current AP's bssid and reassociate with the nearest
            # AP in the vicinity
            wifi.blacklist(bssid)
            wifi.reassociate()
            time.sleep(10)

        elif ip_address == None:
            print "Need to do something"

    # TODO : Need to interpret the different status returned by wpa_cli
    # like 'SCANNING', 'INACTIVE',... and do something with them
    elif wpa_state != "COMPLETED":
        logging.debug("Connexion au hotspot perdue, tentative de fix")
        # Tell wpa_supplicant to associate with the nearest AP
        wifi.reassociate()

