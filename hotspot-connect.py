#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Name : Hotspot Connect
# Author : Oxmel
# Version : 0.1


# Automates the authentication on a hotspot and keeps the connection alive
#
# Note that this script has originally been made to run on a raspberry pi
# running Raspbian Jessie that is configured to emulate the behavior of a
# modem-router (see the script called 'pi-modem.sh' in my scripts repo).
# In our case, the hotspots 'orange' are used to get an internet connection
# but the script can work with other providers like 'Free','Neuf', 'Fon',...
# Assuming you're running it on Debian Jessie, the authentication process
# will probably be the only thing that needs to be rewritten.
#
# Since a lot of things can go wrong when trying to maintain a connection on
# that kind of hostpot, the script will check at regular interval if the client
# has access to the net or if a reauthentication is necessary.
# In case the connection breaks, the script will perform a diag and will try to
# repair the connection.
#
# If after 3 repair attempts, the connection is still down, it's generally a sign
# of failure on the hotspot side. If this happens, the script will switch from
# the faulty AP to another one.
#
# In other words, the more hotspots around, the less you are likely to
# completely lose the connection.


import logging
import time
import os

from src import diag
from src import auth
from src import wifi

# Fetch the full path of the script
curPath = os.path.dirname(os.path.abspath(__file__))
logging.getLogger("urllib3").setLevel(logging.WARNING)

# Store the log file in the same folder as the script
logging.basicConfig(filename='%s/connect.log' %curPath, level=logging.DEBUG,
        format='%(asctime)s - [%(levelname)s]: %(message)s',
        datefmt='%d/%m/%Y %H:%M:%S')


logging.info('Lancement du script de monitoring')

# Check if wpa_supplicant is running and if so kill the process
diag.killWpa()

# Association attempt with the first AP of the list (see wifi.py)
wifi.joinAp()


while True :

    netStatus = diag.networkCheck()

    if netStatus == 1 :
        logging.info('Requête redirigée vers le portail captif')
        logging.info('Reconnexion en cours...')
        #auth.performAuth()

    elif netStatus == 2 :
        logging.warning('Problème réseau détecté!')
        diag.networkDiag()

    time.sleep(20)
