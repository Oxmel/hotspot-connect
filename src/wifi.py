#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
    Connect to wpa_supplicant ctrl socket and send commands through it.

    This module is heavily inspired from the awesome work @awkman did
    with the cross-platform python module 'pywifi'.

    https://github.com/awkman/pywifi

    Note: On Raspbian, wpa_supplicant comes already pre-configured so
    unprivileged users are able to access its control interface out of
    the box. However, on other Linux systems elevated privileges may be
    required. But one can manually allow non-root user access.

    https://github.com/awkman/pywifi/issues/48#issuecomment-541447683
"""


import os
import socket
import sys
import time
import logging


interface = "wlan0"
wpa_send_path = "/run/wpa_supplicant/" + interface
wpa_recv_path = "/tmp/wpa_ctrl_socket"
sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM, 0)


class WifiTools():

    def __init__(self):

        self.network_id = 0

    def wpa_control(self):
        """Connect and test the connectivity to the socket."""

        if os.path.exists(wpa_recv_path):
            logging.debug("Socket file already exists, removing")
            os.remove(wpa_recv_path)

        logging.debug("Creating socket file")
        sock.bind(wpa_recv_path)

        logging.debug("Connecting to socket...")
        sock.connect(wpa_send_path)
        sock.send(b"PING")
        reply = sock.recv(4096)

        if reply.startswith(b'PONG'):
            logging.debug("Connected")
            return

        logging.critical("Unable to connect to wpa_supplicant socket")
        sys.exit(1)

    def disconnect(self):
        """Disconnect the interface."""

        self.send_cmd('DISCONNECT')

    def remove_networks(self):
        """Remove all configured networks."""

        self.send_cmd('REMOVE_NETWORK all')

    def scan(self):
        """
        Look for avail candidates in the area and return their bssid.

        Note: Scans often return inconsistent results and sometimes
        no results at all even if there are available hotspots in the
        area. Unfortunately, this has nothing to do with wpa_supplicant
        and seems to be more related to the wireless driver used by
        default on Raspbian (nl80211n). The easiest workaround consists
        of performing x scans in a row to reduce the occurence of
        inaccurate results, but this doesn't completely fix the issue.
        """

        self.ap_list = []

        # Sleep 1s between each command to avoid a 'FAIL/BUSY' error.
        for i in range(3):

            self.send_cmd('SCAN')
            time.sleep(1)
            scan_results = self.send_cmd('SCAN_RESULTS', True)

            # Each line becomes a list element (ignore 1st line)
            scan_results = scan_results.split('\n')[1:]

            for result in scan_results:
                # Each AP info becomes a list element
                # e.g. ['bssid', 'frequency', signal', 'flags', 'essid']
                ap_info = result.split('\t')

                # Ignore blank results and results with hidden ssid
                if len(ap_info) == 5 and ap_info[4] == "orange":
                    bssid = ap_info[0]
                    if bssid not in self.ap_list:
                        self.ap_list.append(bssid)

            time.sleep(1)

        return self.ap_list

    def set_network(self):
        """Set network configuration for wpa_supplicant."""

        net_id = self.send_cmd('ADD_NETWORK', True).strip()
        self.send_cmd('SET_NETWORK %s ssid "orange"' %net_id)
        self.send_cmd('SET_NETWORK %s key_mgmt NONE' %net_id)

        return net_id

    def associate(self, net_id):
        """Association attempt with the nearest AP."""

        self.send_cmd('SELECT_NETWORK %s' %net_id)

    def reassociate(self):
        """Reassociate with the nearest AP."""

        self.send_cmd('REASSOCIATE')

    def reattach(self):
        """Reattach to the same AP."""

        self.send_cmd('REATTACH')


    def signal_strength(self):
        """
        Grab and format signal strength.

        'RSSI' for the current signal strength
        'AVG_RSSI' for an average value
        """

        signal_poll = self.send_cmd('SIGNAL_POLL', True)
        for line in signal_poll.splitlines():
            name, value = line.split("=")
            if name == "AVG_RSSI":
                signal = int(value.strip('-'))

        return signal

    def status(self):
        """Extract and return formatted wifi info for the current AP."""

        wifi_info = self.send_cmd('STATUS', True)

        info_dict = {}

        for line in wifi_info.splitlines():
            name, value = line.split("=")
            info_dict[name] = value

        return info_dict

    def set_pref(self, bssid):
        """Set preffered bssid for a ssid."""

        self.send_cmd('BSSID %s %s' %(self.network_id, bssid))

    def send_cmd(self, cmd, get_reply=False):
        """Send commands through wpa_supplicant socket."""

        logging.debug("Send cmd '%s'" %cmd)

        sock.send(bytearray(cmd, 'utf-8'))
        reply = sock.recv(4096)

        if get_reply:
            return reply.decode('utf-8')

        if reply != b'OK\n':
            reply = reply.decode('utf-8').strip('\n')
            logging.critical("Unexpected reply '%s' for cmd '%s'" %(reply, cmd))
            sys.exit(1)
