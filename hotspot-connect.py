#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Author: Oxmel


"""

                        Hotspot Connect v0.2.3

    Automate the association/authentication process on hotspots of
    the french internet provider 'orange' and keep the connection alive.

    This script uses wpa_supplicant and has originally been made to run
    on a raspberry pi that is configured to emulate the behavior of a
    modem-router. See 'pi-modem-router.sh' for more info.

    https://github.com/Oxmel/scripts/blob/master/pi-modem-router.sh

    Note: If you plan to set up an internet access for an extended
    pediod of time, the connection stability will heavily depend on
    the number of hotspots available in the vicinity. Because if the
    current hotspot stops working, wpa_supplicant will automatically
    try to find another candidate in the area. So the more hotspots
    around, the better it is.

"""


from src import diag, auth, wifi
import logging
import time
import os
import sys


# Fetch the path of the current file
cur_path = os.path.dirname(os.path.abspath(__file__))

# Instantiate the logger and set global level to 'INFO'
# Note that we can set a log level for each handler independently
# e.g : 'INFO' for logfile and 'DEBUG' for console (stdout)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# By default, any new HTTP connection started by urllib3 is logged as 'INFO'
# So we set log level to 'WARNING' as we don't need these lines
logging.getLogger("urllib3").setLevel(logging.WARNING)

# Create file handler and set logfile name
# Store log file in the folder 'hotspot-connect'
file_handler = logging.FileHandler('%s/connect.log' %cur_path)
file_handler.setLevel(logging.INFO)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create formatter and set a custom datetime format (day/month/year)
formatter = logging.Formatter('%(asctime)s - [%(levelname)s]: %(message)s', datefmt='%d/%m/%Y %H:%M:%S')

# Add the formatter to each handler
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add both handlers to logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)


# Greeting message
logging.info('Hotspot Connect - v0.2.3')

wifi = wifi.WifiTools()
diag = diag.DiagTools()

# Connect to wpa_supplicant control socket
wifi.wpa_control()

logging.info("Looking for 'orange' hotspots...")

# Disconnect the wireless interface.
wifi.disconnect()
# Remove all configured networks
wifi.remove_networks()
# Scan for available candidates in the vicinity
wifi.scan()

# Give wpa_supplicant the time to populate scan_results
# The time needed may vary from one wifi card to another
time.sleep(5)

ap_list = wifi.scan_results()

if ap_list == []:
    logging.critical("No candidate found in the area!")
    sys.exit(1)

ap_count = len(ap_list)
logging.info("Found %s candidate(s) in the area" %ap_count)
logging.debug("List of available APs : %s" %ap_list)

# Configure network profile an grab its id
net_id = wifi.set_network()

# Connect to the nearest hotspot
wifi.associate(net_id)

logging.info("Association in progress...")
time.sleep(30)

wifi_info = wifi.status()
wpa_state = wifi_info['wpa_state']

if wpa_state != 'COMPLETED':
    logging.critical("Association failed!")
    sys.exit(1)

bssid = wifi_info['bssid']
signal = wifi.signal_strength()

logging.info("Association successfull :-)")
logging.info("bssid  : %s" %bssid)
logging.info("signal : -%s dBm" %signal)

# Display this message (only once) when internet is back
# Way of saying that everything is ok
service_msg = True


while True:

    net_status = diag.network_check()

    if net_status == 0:
        if service_msg:
            logging.info("Network monitoring enabled")
            service_msg = False

        time.sleep(20)
        continue

    service_msg = True

    if net_status == 1:
        logging.info('Authentication required on the captive portal')
        logging.info("Sending credentials...")
        auth.perform_auth()

    if net_status == 2:
        logging.error('Network unreachable!')
        logging.info('Launching a connection diag...')
        diag.network_diag()
