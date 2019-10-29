#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import requests
import json
import logging
import diag
import sys



# These credentials are needed to connect to the captive portal
# The username is either a phone number or a mail address
username = ''
password = ''



# Humanize the script by using a 'standard' user-agent
headers = {
    'user-agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:64.0) '
        'Gecko/20100101 Firefox/64.0')
}

auth_data = [
    {
        'method': 'GET',
        'url': 'https://login.orange.fr'
    },
    {
        'method': 'POST',
        'url': 'https://login.orange.fr/front/login',
        'payload': {'login': username, 'mem': 'true'}
    },
    {
        'method': 'POST',
        'url': 'https://login.orange.fr/front/password',
        'payload': {'login': username, 'password': password}
    },
    {
        'method': 'GET',
        'url': 'https://hautdebitmobile.orange.fr:8443/home'
    },
    {
        'method': 'GET',
        'url': 'https://hautdebitmobile.orange.fr:8443/home/wassup',
        'payload': {'isCgu': 'on', 'doCheckCgu': '1'}
    }
]

diag = diag.DiagTools()

def perform_auth():

    session = requests.Session()

    for item in auth_data:
        method = item['method']
        url = item['url']
        payload = json.dumps(item.get('payload'))

        try:
            req = session.request(
                    method, url, data=payload,
                    headers=headers, timeout=(10, 10))
            # Exception raised in case of http error (4xx, 5xx,...)
            req.raise_for_status()

        # Catch any exception like http error, connection error,...
        except requests.exceptions.RequestException as e:
            logging.critical(e)
            sys.exit(1)

    # Check if the authentication is successful
    if diag.network_check() == 0:
        logging.info('Authentication successfull')
    else:
        logging.critical('Authentication failed!')
        sys.exit(1)
