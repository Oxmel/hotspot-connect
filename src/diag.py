#!/usr/bin/env python
# -*- coding: UTF-8 -*-


"""

    This module provides a set of tools to check the connection
    state and detect when a reauthentication on the captive portal
    is necessary.

    To achieve this, we mimic the method used by google on
    android. We make a call on a test url and verify the http
    code returned by the server.

    https://android.stackexchange.com/q/123129

    Since a lot of things can go wrong when trying to maintain a
    connection on that kind of hostpot, we also diag and attempt to
    fix the issue in case of network errors. Which is the trickiest
    part as many factors can influence the connection stability.

"""


import requests
import logging
import time
import auth
import wifi
import sys


test_url = "http://clients3.google.com/generate_204"

# Humanize the script by using a 'standard' user-agent
headers = {
    'user-agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:64.0) '
        'Gecko/20100101 Firefox/64.0')
}


def network_check():
    """
    Check and return the status of the connection.

        Code 0 = internet access
        Code 1 = request redirected to the captive portal
        Code 2 = Unable to reach the target (network down)

    Since the network can be unstable, requests will sometimes
    raise a random error when trying to call the test url. So when
    one of those random errors occurs, it's better to retry several
    times before considering that the network is down.

    https://stackoverflow.com/a/34885906

    We also set a timeout for the same reason to avoid a long wait
    in case something goes wrong during the request.

    https://stackoverflow.com/a/22377499
    """

    # Retry (3 times) in case of error
    for i in range(1, 5):

        try:
            req = requests.get(test_url, headers=headers, timeout=(10, 10))
            req.raise_for_status()
            http_code = req.status_code

            if http_code == 204 :
                return 0
            elif http_code == 200 :
                return 1
            else:
                logging.critical("Unhandled HTTP code: %s" %http_code)
                sys.exit(1)

        # Exception raised in case of http error (4xx, 5xx,...)
        except requests.exceptions.HTTPError as e:
            logging.critical(e)
            sys.exit(2)

        # Random error when the network becomes unstable
        except requests.exceptions.RequestException as e:
            logging.debug(e)

            if i < 4:
                logging.debug("Target url unreachable, retrying (%s/3)" %i)
                time.sleep(3)
                continue
            else:
                logging.debug("Unable to reach target url after 3 tries")
                return 2



def network_diag():
    """
    Check the wireless link and if the client has a valid ip.

    If the client doesn't obtain an ip or obtains an ip that starts
    with '169.254' (depending on the platform) this means that the
    dhcp server of the AP is faulty so we blacklist its bssid before
    telling wpa_supplicant to find another candidate in the area.
    """

    wifi_info = wifi.status()
    wpa_state = wifi_info["wpa_state"]

    # Check if the client is associated with the hotspot
    if wpa_state == "COMPLETED":
        # Return 'None' if the client has no ip address
        ip_address = wifi_info.get("ip_address")

        # Check for Nonetype first to prevent an attribute error
        if ip_address == None or ip_address.startswith("169.254"):
            logging.info("Faulty AP, looking for another candidate...")
            bssid = wifi_info["bssid"]
            wifi.blacklist(bssid)
            wifi.reassociate()
            time.sleep(10)
        else:
            logging.critical("Unable to fix connection, is AP in range?")
            sys.exit(1)

    else:
        logging.critical("Unhandled wpa state : %s" %wpa_state)
        sys.exit(2)
