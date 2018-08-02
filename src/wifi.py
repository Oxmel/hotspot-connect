#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
import time
import logging
import subprocess
import diag


# Equivalent of /dev/null in bash
FNULL = open(os.devnull, 'w')


associate = "/sbin/iwconfig wlan0 essid 'FreeWifi' ap %s"
dhcp_release = "/sbin/dhclient -r wlan0"
dhcp_renew = "/sbin/dhclient wlan0"
ap_signal = "iwconfig wlan0 | grep -Po 'level=\K\-[0-9]{2} [a-zA-Z]{3}'"



# Random MAC addresses for testing purposes
ap_list = [
    "BF:A5:C1:A5:4F:7B",
    "AB:CE:7C:46:7B:74",
    "2A:08:0A:D2:34:83"
]


# Global variable used to save a list index
cur_index = 0


# Return the result of a bash command (usually plain text)
def check_cmd(cmd):
    result = subprocess.check_output(cmd, shell=True).strip()
    return result

# Send a command and hide the output
def call_cmd(cmd):
    result = subprocess.check_call(cmd, shell=True, stdout=FNULL, stderr=subprocess.STDOUT)
    return result




def join_ap():
    global cur_index
    cur_ap = ap_list[cur_index]
    logging.info("Connexion au point d'accès...")
    call_cmd(associate %cur_ap)
    # Give to the client some time to connect before checking the connection
    time.sleep(5)

    if diag.wifi_status() == 0:
        logging.info("Connecté")
        signal = check_cmd(ap_signal)
        logging.info("BSSID: %s" %cur_ap)
        logging.info("Signal: %s" %signal)
        logging.debug("Demande d'attribution IP")
        call_cmd(dhcp_renew)
    else:
        logging.warning("Echec de la connexion!")



def switch_ap():
    global cur_index
    cur_ap = ap_list[cur_index]

    # Based on the position of the current BSSID in the list, we choose the
    # next one then attempt to connect to it
    # If the current BSSID is the last of the list, next one is the first one
    if cur_index < len(ap_list) -1:
        cur_index = cur_index + 1
    else:
        cur_index = 0
    next_ap = ap_list[cur_index]
    logging.debug("DHCP release")
    call_cmd(dhcp_release)
    logging.debug("Leaving -> %s" %cur_ap)
    logging.debug("Joining -> %s" %next_ap)
    join_ap()
