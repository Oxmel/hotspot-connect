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

        # List of bssid to ignore
        self.faulty_ap = []

        # Sleep x secs if we can't find a working hotspot
        # This value is multiplied by 2 for each failed attempt
        self.time_wait = 60
        self.max_wait = 3840


    def ap_count(self):
        """Return number of available APs in the vicinity."""

        wifi.scan()
        # Gives wpa_supplicant time to populate scan_results
        # The time needed may vary from one wifi card to another
        time.sleep(5)
        result = wifi.scan_results()
        ap_count = len(result)

        return ap_count


    def assoc_poll(self):
        """Repeatedly check association status (Polling)."""

        i = 0
        logging.debug('Polling wpa state...')
        while i <= 20:
            wifi_info = wifi.status()
            wpa_state = wifi_info['wpa_state']
            logging.debug('wpa state: %s' %wpa_state)
            if wpa_state == 'COMPLETED':
                return True

            time.sleep(1)

        return False


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
                time.sleep(5)
                continue

        logging.debug("Unable to reach target url after %s tries" %i)
        return 2


    def network_diag(self):
        """Diag and attempt to fix connection issues"""

        wifi_info = wifi.status()
        wpa_state = wifi_info['wpa_state']
        # Return 'None' if no bssid or ip address
        bssid = wifi_info.get('bssid')
        ip = wifi_info.get('ip_address')

        if not ip or ip.startswith('169.154'):
            logging.warning('Unable to obtain a valid IP!')
            self.faulty_ap.append(bssid)
            logging.info("Looking for another hotspot...")
            self.manual_mode()

        if wpa_state != 'COMPLETED':
            logging.warning('')
            logging.info('Reconnecting to the nearest AP...')
            self.auto_mode()


    def manual_mode(self):
        """Manually choose which AP to use."""

        wifi.disconnect()
        wifi.scan()
        time.sleep(5)
        avail_ap = wifi.scan_results()
        logging.debug("List of available ap : %s" %avail_ap)
        logging.debug("List of faulty ap : %s" %self.faulty_ap)

        for ap in avail_ap:

            if ap not in self.faulty_ap:
                self.auto_mode(ap)
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


    def auto_mode(self, bssid=None):
        """Connect either to the nearest AP or to a specified bssid"""

        if bssid:
            wifi.set_pref(bssid)
            logging.debug('Preffered bssid is now set to %s' %bssid)
            wifi.reassociate()

        else:
            logging.debug('No bssid specified')
            wifi.remove_networks()
            net_id = wifi.set_network()
            wifi.associate(net_id)

        if not self.assoc_poll():
            logging.critical("Association failed!")
            sys.exit(1)

        logging.info("Association successful :-)")
        wifi_info = wifi.status()
        bssid = wifi_info['bssid']
        logging.info("bssid  : %s" %bssid)
        signal = wifi.signal_strength()
        logging.info("signal : -%s dBm" %signal)

