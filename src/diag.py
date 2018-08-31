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


# This module checks the connection and tries various fixes depending on
# the connection state as soon as the script detects an internet cut
#
# Btw, in a perfect world, if an AP is faulty, all we have to do is to switch
# to the next one in range. But from my tests, out of ten 'orange' hotspots
# in the vicinity, all of them can suddenly break at the same time
# (understand 'fail to give the client an ip address') and still be broken
# even after several days. Which suggests that the addressing is not managed
# independently by each router but centralized elsewhere.


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
        # this means the dhcp server of the AP is faulty so we need
        # to tell wpa_supplicant to ignore it and find another one
        if ip_address.startswith("169.254"):
            logging.debug("Dysfonctionnement de l'AP, changement de hotspot")
            wifi.blacklist(bssid)
            wifi.reassociate()

        elif ip_address == None:
            logging.info("Aucune IP attribuée")

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
        logging.debug("status wifi : %s" %wifi_infos["wpa_state"])
        logging.debug("adresse ip : %s" %wifi_infos["ip_address"])
