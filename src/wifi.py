#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import time
import logging
import subprocess
import diag
import iface
import re


# Random MAC addresses for testing purposes
ap_list = []


# Global variable used to save a list index
cur_index = 0



# Look for APs that match a specific ESSID in the vicinity and generate a
# list containing their BSSID. We then use this list both when the script
# starts, or in case something goes wrong to switch to another AP.
# Usually when the current AP fails to address the client or if it disappears.
def scan():
    global ap_list
    scan = "/sbin/iwlist wlan0 scan"

    try:
        result = subprocess.check_output(scan, shell=True)
        # Every block of info for each AP starts with the pattern :
        # Cell (number) - Address: (a_mac_address)
        # So we delimit each block before putting them in a list
        result = result.split('Cell')

        # Select blocks of info one by one and check if some of them are
        # the APs we're looking for. If so, add the AP bssid in a list
        for ap in result:
            essid = re.search(r'ESSID:(\S+)', ap)
            bssid = re.search(r'Address:\s+(\S+)', ap)
            # Need to investigate why re always returns one 'None' even if
            # the pattern matches
            if essid:
                essid = essid.group(1)
                essid = essid.strip("\"")
                if essid == "FreeWifi":
                    bssid = bssid.group(1)
                    ap_list.append(bssid)

        if ap_list == []:
            logging.error("Aucun AP trouvé dans les environs, sortie")
            exit(1)
        else:
            list_len = len(ap_list)
            logging.info("%s APs trouvés dans les environs" %list_len)

    except subprocess.CalledProcessError as e:
        logging.error(e)




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

        # Need to manually request an ip after the association but only
        # if the association is successfull. Otherwise dhclient will retry
        # for like 20 seconds without any chance to obtain an ip
        if diag.wifi_status():
            iface.dhcp_action("renew")

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
