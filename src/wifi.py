#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
import time
import logging
import subprocess
import diag
import iface


# Equivalent of /dev/null in bash
FNULL = open(os.devnull, 'w')



# Random MAC addresses for testing purposes
ap_list = [
    "BF:A5:C1:A5:4F:7B",
    "AB:CE:7C:46:7B:74",
    "2A:08:0A:D2:34:83"
]


# Global variable used to save a list index
cur_index = 0


# We use ap=None to set an optional arg
# So we can reuse the same method to connect to any AP with a given ESSID
# Or to connect to a specific AP with a given ESSID and BSSID
def join_ap(ap=None):
    if ap:
        associate = "/sbin/iwconfig wlan0 essid 'FreeWifi' ap %s" %ap
    else:
        associate = "/sbin/iwconfig wlan0 essid 'FreeWifi'"

    try:
        subprocess.check_call(associate, shell=True)
        # Wait a bit in case the association takes more time than expected
        time.sleep(5)
    except subprocess.CalledProcessError as e:
        logging.error(e)

# We use a blank essid to make the client disconnect from the current AP.
# This command becomes useful when we want to start a scan because if the
# client is connected to an AP, the scan result will only
# show the AP he's currently connected to.
def disconnect():
    leave = "/sbin/iwconfig wlan0 essid ''"
    try:
        subprocess.check_call(leave, shell=True)
    except subprocess.CalledProcessError as e:
        logging.error(e)


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
    iface.dhcp_action("release")
    logging.debug("Leaving -> %s" %cur_ap)
    logging.debug("Joining -> %s" %next_ap)
    join_ap(next_ap)
