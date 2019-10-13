#!/usr/bin/env python
# -*- coding: UTF-8 -*-


"""

    This module is a very basic wrapper around wpa_cli.

"""


import logging
import subprocess
import sys
import os


# Redirect output to /dev/null
FNULL = open(os.devnull, 'w')


# Get wireless infos (AP bssid, ip address, wpa state,...)
def status():

    cmd = "/sbin/wpa_cli -i wlan0 status"
    wifi_infos = {}

    try:
        result = subprocess.check_output(cmd, shell=True)
        for line in result.splitlines():
            name, var = line.split("=")
            wifi_infos[name] = var
        return wifi_infos

    except subprocess.CalledProcessError as e:
        logging.critical(e)
        sys.exit(1)


def blacklist(arg):
    """
    Blacklist the bssid of a given access point.

    This is particularly useful in certain situations, like
    for instance when the current hotspot fails to give an ip
    address to the client.

    To blacklist a specific AP : blacklist("bssid")
    To clear the blacklist : blacklist("clear")
    """

    cmd = "/sbin/wpa_cli blacklist %s" %arg

    try:
        subprocess.check_call(cmd, shell=True, stdout=FNULL)

    except subprocess.CalledProcessError as e:
        logging.critical(e)
        sys.exit(1)


def reassociate():
    """
    Association attempt with any AP that shares a given essid.

    This function is usually called after we have blacklisted
    a bssid. An essid must be specified in wpa_supplicant.conf
    """

    cmd = "/sbin/wpa_cli reassociate"

    try:
        subprocess.check_call(cmd, shell=True, stdout=FNULL)

    except subprocess.CalledProcessError as e:
        logging.critical(e)
        sys.exit(1)
