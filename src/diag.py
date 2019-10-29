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
import wifi
import sys


wifi = wifi.WifiTools()

test_url = "http://clients3.google.com/generate_204"

# Humanize the script by using a 'standard' user-agent
headers = {
    'user-agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:64.0) '
        'Gecko/20100101 Firefox/64.0')
}


class DiagTools():

    def __init__(self):

        # Used to calculate % of net errors
        self.req_err = 0
        self.req_sent = 0

        # List of bssid to ignore
        self.faulty_ap = []

        # Sleep x secs if we can't find a working hotspot
        # This value is multiplied by 2 for each failed attempt
        self.time_wait = 60
        self.max_wait = 3840

    def network_check(self):
        """
        Check and return the status of the connection.

            Code 0 = internet access
            Code 1 = request redirected to the captive portal
            Code 2 = Unable to reach the target (network down)

        Note: Since the network can be unstable at times, requests
        will sometimes raise a random (i.e. Non HTTP) error when
        trying to call the test url. In these cases, it's recommended
        to retry x times before considering that the network is down.
        """

        # Retry in case of non HTTP related errors
        for i in range(1, 5):

            self.req_sent += 1

            try:
                logging.debug("Sending a request to %s" %test_url)
                req = requests.get(test_url, headers=headers, timeout=(10, 10))
                req.raise_for_status()
                http_code = req.status_code

                logging.debug("HTTP response : %s" %http_code)
                if http_code == 204:
                    return 0

                if http_code == 200:
                    return 1

                logging.critical("Unhandled HTTP code: %s" %http_code)
                sys.exit(1)

            # Exception raised in case of http error (4xx, 5xx,...)
            except requests.exceptions.HTTPError as e:
                logging.critical(e)
                sys.exit(1)

            # Random error when the network becomes unstable
            except requests.exceptions.RequestException as e:
                logging.debug(e)
                logging.debug("Target url unreachable, retrying (%s/4)" %i)

                self.req_err += 1

                if i == 2:
                    logging.warning("The network connection is getting unstable!")

                time.sleep(5)
                continue

        logging.debug("Unable to reach target url after %s tries" %i)
        return 2

    def network_diag(self):
        """Perform a diagnostic of the connection."""

        err_percent = self.err_percent()
        logging.debug("Percentage of network errors (global): %s" %err_percent)

        for i in range(2):

            wifi_info = wifi.status()

            wpa_state = wifi_info['wpa_state']
            logging.debug("wpa_state : %s" %wpa_state)

            if wpa_state != "COMPLETED":

                if i == 0:
                    logging.warning("The connection with the hotspot has been lost!")
                    logging.info("Reassociating...")
                    wifi.reassociate()
                    time.sleep(30)
                    continue

                logging.warning("Association failed!")
                break

            bssid = wifi_info['bssid']
            logging.debug("bssid : %s" %bssid)

            ip_addr = wifi_info.get("ip_address")
            logging.debug("ip address : %s" %ip_addr)

            if ip_addr == None or ip_addr.startswith("169.254"):

                if i == 0:
                    logging.warning("The current ip address is invalid")
                    logging.info("Trying to obtain a valid ip...")
                    wifi.reattach()
                    time.sleep(20)
                    continue

                logging.warning("Unable to obtain a valid ip!")
                self.faulty_ap.append(bssid)
                break

            break

        logging.info("Looking for another candidate...")
        self.manual_mode()

    def manual_mode(self):
        """Manually choose which AP to use."""

        wifi.disconnect()
        time.sleep(1)
        avail_ap = wifi.scan()

        logging.debug("List of available ap : %s" %avail_ap)
        logging.debug("List of faulty ap : %s" %self.faulty_ap)

        for ap in avail_ap:

            if ap not in self.faulty_ap:
                wifi.set_pref(ap)

                logging.info("New candidate found")
                logging.debug("Preffered bssid is now set to %s" %ap)
                logging.info("Associating...")
                wifi.reassociate()
                time.sleep(30)

                wifi_info = wifi.status()

                if wifi_info['wpa_state'] != "COMPLETED":
                    logging.warning("Association failed!")
                    logging.info("Looking for another candidate...")
                    self.faulty_ap.append(ap)
                    continue

                logging.info("Association successful")
                logging.info("bssid  : %s" %ap)
                signal = wifi.signal_strength()
                logging.info("signal : -%s dBm" %signal)
                return

        logging.error("Tested all available hotspots but none of them work :-(")
        self.faulty_ap = []
        wifi.disconnect()
        self.sleep_mode()

    def sleep_mode(self):
        """Wait for a given period of time between two tries."""

        if self.time_wait >= 3840:
            logging.debug("Already reached max time wait (%s)" %self.time_wait)
            self.time_wait = 60

        else:
            self.time_wait = self.time_wait * 2

        sec_to_min = (self.time_wait / 60)
        logging.info("Entering sleep mode...(next try in %smin)" %sec_to_min)
        time.sleep(self.time_wait)

        logging.info("Waking up...")
        self.auto_mode()

    def auto_mode(self):
        """Give back control to wpa_supplicant."""

        wifi.remove_networks()
        time.sleep(1)
        net_id = wifi.set_network()
        time.sleep(1)

        logging.info("Associating with the nearest AP...")
        wifi.associate(net_id)
        time.sleep(30)

    def err_percent(self):
        """Calculate the percentage of errors on the connection."""

        req_count = self.req_sent
        err_count = self.req_err

        if req_count > 0 and err_count > 0:
            result = ((err_count * 100) / req_count)
            return result

        return None
