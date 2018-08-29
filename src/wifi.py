#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import time
import logging
import subprocess
import sys


# Get connection infos using wpa_cli
def status():

    cmd = "/sbin/wpa_cli -i wlan0 status"
    wifi_infos = {}

    try:
        result = subprocess.check_output(cmd, shell=True)

        for line in result.splitlines():
            name, var = line.split("=")
            wifi_infos[name] = var

        if "ip_address" not in wifi_infos:
            wifi_infos["ip_address"] = None

        return wifi_infos

    # We have no other choice than exiting at this point because if
    # we can't call wpa_cli, this means wpa_supplicant probably crashed
    except subprocess.CalledProcessError as e:
        logging.critical(e)
        sys.exit(1)


# If an AP fails to address the client, it usually means there is a problem
# on the hotspot side, so we blacklist its bssid to tell wp_supplicant to
# ignore it when attempting to reassociate with the nearest AP
def blacklist(ap):

    cmd = "/sbin/wpa_cli blacklist %s" %ap

    try:
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError as e:
        logging.error(e)


# Tell wpa_supplicant to associate with any AP that shares a ssid
def reassociate():

    cmd = "/sbin/wpa_cli reassociate"

    try:
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError as e:
        logging.error(e)
