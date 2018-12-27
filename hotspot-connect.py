#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# Name : Hotspot Connect
# Author : Oxmel
# Version : 0.1
#
#
# Automates the authentication on a hotspot and keeps the connection alive
#
# Note that this script uses wpa_supplicant and has originally been made to
# run on a raspberry pi that is configured to emulate the behavior of a
# modem-router (see the script called 'pi-modem.sh' in my scripts repo).
#
# In our case, the hotspots 'orange' are used to get an internet connection
# but the script can work with other providers like 'Free','Neuf', 'Fon',...
# Assuming you're running it on Raspbian, the authentication process is
# probably the only thing that would need to be rewritten.
#
# Since a lot of things can go wrong when trying to maintain a connection on
# that kind of hostpot, the script will regularly check if something goes
# wrong or if a reauthentification on the captive portal is necessary.
#
# The main problems usually come from the APs themselves as the 'orange'
# hotspots may sometimes fail to give the client an ip address.
# If this happens, the faulty AP will automatically be blacklisted and
# wpa_supplicant will try to find another candidate in the vicinity.
#
# In other words, the more hotspots around, the less you are likely to
# completely lose the connection.


import logging
import time
import os

from src import diag
from src import auth
from src import wifi


# Instantiate the logger and set global level to 'Debug'
# Note that we can set a log level for each handler independently
# e.g : 'DEBUG' for logfile and 'WARNING' for console (stdout)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# By default, any new HTTP connection started by urllib3 is logged as 'INFO'
# So we set log level to 'WARNING' as we don't need those lines
logging.getLogger("urllib3").setLevel(logging.WARNING)

# Create file handler and set logfile name
file_handler = logging.FileHandler('connect.log')
file_handler.setLevel(logging.DEBUG)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Create formatter and set a custom datetime format (day/month/year)
formatter = logging.Formatter('%(asctime)s - [%(levelname)s]: %(message)s', datefmt='%d/%m/%Y %H:%M:%S')

# Add the formatter to each handler
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add both handlers to logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)


logging.info('Lancement du script de monitoring')

# Clear the blacklist each time the script starts to avoid the situation
# where an AP could stay in the bl even if it starts working again
logging.debug('Clearing the blacklist')
wifi.blacklist("clear")

while True :

    net_status = diag.network_check()

    if net_status == 1 :
        logging.info('Requête redirigée vers le portail captif')
        logging.info('Reconnexion en cours...')
        auth.perform_auth()

    elif net_status == 2 :
        logging.warning('Problème réseau détecté!')
        diag.network_diag()

    time.sleep(20)
