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
dhcpRelease = "/sbin/dhclient -r wlan0"
dhcpRenew = "/sbin/dhclient wlan0"
apSignal = "iwconfig wlan0 | grep -Po 'level=\K\-[0-9]{2} [a-zA-Z]{3}'"



# Random MAC addresses for testing purposes
apList = [
    "BF:A5:C1:A5:4F:7B",
    "AB:CE:7C:46:7B:74",
    "2A:08:0A:D2:34:83"
]


# Global variable used to save a list index
curIndex = 0


# Return the result of a bash command (usually plain text)
def checkCmd(cmd):
    result = subprocess.check_output(cmd, shell=True).strip()
    return result

# Send a command and hide the output
def callCmd(cmd):
    result = subprocess.check_call(cmd, shell=True, stdout=FNULL, stderr=subprocess.STDOUT)
    return result




def joinAp():
    global curIndex
    currentAp = apList[curIndex]
    logging.info("Connexion au point d'accès...")
    callCmd(associate %currentAp)
    # Give to the client some time to connect before checking the connection
    time.sleep(5)

    if diag.wifiStatus() == 0:
        logging.info("Connecté")
        signal = checkCmd(apSignal)
        logging.info("BSSID: %s" %currentAp)
        logging.info("Signal: %s" %signal)
        logging.debug("Demande d'attribution IP")
        callCmd(dhcpRenew)
    else:
        logging.warning("Echec de la connexion!")



def switchAp():
    global curIndex
    currentAp = apList[curIndex]

    # Based on the position of the current BSSID in the list, we choose the
    # next one then attempt to connect to it
    # If the current BSSID is the last of the list, next one is the first one
    if curIndex < len(apList) -1:
        curIndex = curIndex + 1
    else:
        curIndex = 0
    nextAp = apList[curIndex]
    logging.debug("DHCP release")
    callCmd(dhcpRelease)
    logging.debug("Leaving -> %s" %currentAp)
    logging.debug("Joining -> %s" %nextAp)
    joinAp()
