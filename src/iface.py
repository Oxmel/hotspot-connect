#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import logging
import subprocess

# Contains functions related to interface management
# Those func can then be used elsewhere in the code when needed
# For example, to make a dhcp_release, we can use :
#import iface
#iface.dhcp_action("release")


def dhcp_action(action):
    if action == "release":
        cmd = "/sbin/dhclient -r wlan0"
    elif action == "renew":
        cmd = "/sbin/dhclient wlan0"

    try:
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError as e:
        logging.error(e)


def iface_action(action):
    if action == "down":
        cmd = "/sbin/ifconfig wlan0 down"
    elif action == "up":
        cmd = "/sbin/ifconfig wlan0 up"

    try:
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError as e:
        logging.error(e)


def ip_flush():
    cmd = "/bin/ip addr flush dev wlan0"

    try:
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError as e:
        logging.error(e)
