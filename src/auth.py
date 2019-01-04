#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import requests
import json
import logging
import diag


# Those credentials are needed to connect to the captive portal
# The username is either a phone number or a mail address
username = ''
password = ''

# Humanize the script by using a 'standard' user-agent in the header
headers = {
    'user-agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:64.0) '
                   'Gecko/20100101 Firefox/64.0')
    }

# Gotta find a way to store those infos in a more readable fashion
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

# Requests will raise an exception for any HTTP error (4xx, 5xx)
# We also catch any other exception like timeout, connection error,...
# http://docs.python-requests.org/en/master/api/?highlight=exceptions
def perform_auth():
    session = requests.Session()
    for item in auth_data:
        method = item['method']
        url = item['url']
        payload = json.dumps(item.get('payload'))
        try:
            req = session.request(method, url, data=payload,
                                  headers=headers, timeout=(10, 10))
            req.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.critical(e)
            exit(1)

    # At this point we could assume the authentication is successful
    # as requests didn't raise any error. But it's probably safer to
    # manually check if internet is reachable to have a confirmation
    if diag.network_check() == 0:
        logging.info('Connected')
    else:
        logging.critical('Connection failed!')
        exit(2)
