#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import subprocess
import requests
import logging
import time
import auth
import wifi
import iface


# This module checks the connection and tries various fixes depending on
# the connection state as soon as the script detects an internet cut
#
# Btw, in a perfect world if an AP is faulty, all we have to do is to switch
# to the next one in range. But from my tests, out of ten 'orange' hotspots
# in the vicinity (same building), all of them can suddenly break at the same
# time (i.e: fail to give the client an ip address) and still remain
# broken even after several days.


test_url = "http://clients3.google.com/generate_204"
headers = {
    'user-agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:64.0) '
                   'Gecko/20100101 Firefox/64.0')
    }


# Check if the client has access to the net
# We use a timeout (in secs) to avoid a long wait in case something
# goes wrong during the request. We can use a simple value 'timeout=10',
# or a tuple to set both the connect and read timeouts 'timeout=(10, 10)'
#
# Code 0 = internet access
# Code 1 = request redirected to the captive portal
# Code 2 = Unable to reach the target (network down)
#
# Note: In some very specific cases, when the connection breaks right
# before the request is sent, the timeout is sometimes ignored.
# So the request hangs out until the connection is closed (can be long).
# When this happens, Requests raises a random error depending on the
# situation, so for now we use a sort of wildcard to catch any error.
# More info : https://stackoverflow.com/a/22377499
def network_check():
    try :
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



# Check the connection state and if the client has a valid ip attributed
# Note that in certain circumstances, especially if the AP is very far
# away, the connection can be broken even with a valid ip and a
# connection state that could let us think that everything is ok
def network_diag():

    wifi_info = wifi.status()
    wpa_state = wifi_info["wpa_state"]

    # The bssid is only available if the client is associated with an AP
    if wpa_state == "COMPLETED":
        bssid = wifi_info["bssid"]
        ip_address = wifi_info["ip_address"]

        # If the client obtains an ip address that starts with '169.254'
        # or if the client doesn't obtain an ip (depending on the platform)
        # this means the dhcp server of the AP is faulty so we need
        # to tell wpa_supplicant to ignore it and find another one
        if ip_address == None or ip_address.startswith("169.254"):
            logging.warning("AP hors service, changement de hotspot...")
            wifi.blacklist(bssid)
            wifi.reassociate()
            time.sleep(10)

    # This state has (theorically) very little chance to be encountered
    # unless wpa_supplicant takes more time than usual to connect to the
    # nearest AP. Or if a diag is performed right when this event occurs
    elif wpa_state == "SCANNING":
        logging.info("wpa_supplicant scanne les AP alentours")

    # Like above this has very little chance to happen because this state
    # is usually the result of a manual disconnection
    elif wpa_state == "DISCONNECTED":
        logging.info("Déconnecté du hotspot, reconnexion...")
        wifi.reconnect()

    else:
        logging.warning("Exception non gérée")
        logging.debug("status wifi : %s" %wpa_state)
