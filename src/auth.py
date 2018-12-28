#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import requests
import logging
import diag


# Those credentials are needed in order to connect to the captive portal
# The username is either a phone number or a mail address for orange hotspots
username = ''
password = ''

# Humanize the script by using a 'normal' user-agent in the header
user_agent="Mozilla/5.0 (X11; Linux x86_64; rv:55.0) Gecko/20100101 Firefox/55.0"

# List of urls to use in order to log in the user
init_cookie = "https://login.orange.fr"
send_login = "https://login.orange.fr/front/login"
send_pwd = "https://login.orange.fr/front/password"
get_portal = "https://hautdebitmobile.orange.fr:8443/home"
portal_connect = "https://hautdebitmobile.orange.fr:8443/home/wassup"

# Pass the user-agent in the header of the request
headers = { 'user-agent': user_agent }

# Forge data before sending them to the server
login_data = { 'login': username }
pwd_data = { 'login': username, 'password': password }
accept_cgu = {'isCgu': 'on', 'hidden_isCgu': '', 'doCheckCgu': '1'}

def perform_auth():
    # Let requests handle the cookies for us
    session = requests.Session()

    try :
        session.get(init_cookie, headers=headers)
        session.post(send_login, json=login_data, headers=headers)
        session.post(send_pwd, json=pwd_data, headers=headers)
        session.get(get_portal, headers=headers)
        session.get(portal_connect, params=accept_cgu, headers=headers)

        net_status = diag.network_check()
        if net_status == 0 :
            logging.info('Authentifié avec succès, accès internet confirmé')
        else :
            logging.error("Authentification ignorée par le serveur!")

    except requests.exceptions.RequestException as e:
        logging.error(e)
