#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import requests
import logging
import sys
import re
import os


# These credentials are needed to connect to the captive portal
# The login is either a mobile phone number or an email address
login = ''
password = ''


"""
    Authenticate the user on the hotspot's captive portal.

    This procedure requires two steps. Firstly we need to send the user's
    credentials at the url 'sso.orange.fr/WT/userinfo'. We then grab the
    cookie returned by the server and use it to authenticate the user on
    the captive portal at 'hautdebitmobile.orange.fr:8443/wificom/logon'

    Note that the user needs to reauthenticate on the captive portal on
    a regular basis, usually every 12 hours. But the cookie keeps being
    valid for couple days so we can reuse it several times before having
    to get a new one.

    Special thanks to @ng-pe for his researches and advices that helped me
    tremendously finding and implementing this new authentication method :-)
"""


headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 5.1; Google Build/LMY47D)',
    'Accept': '*/*',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive'
}

payload = {
    'serv': 'WIFIOO',
    'info': 'cooses',
    'wt-msisdn': login,
    'wt-pwd': password,
    'wt-cvt': '4',
    'wt-mco': 'MCO=OFR'
}

params = {
    'lang': 'fr',
    'version': 'V2'
}

# Store cookie file '.cookie' in the root folder of the script
cookie_file = os.path.abspath(__file__ + '/../../.cookie')

# Switch key name depending on the type of credential (email or phone n°)
if '@orange.fr' in login:
    payload['wt-email'] = payload['wt-msisdn']
    del payload['wt-msisdn']


def grab_cookie():
    url = 'https://sso.orange.fr/WT/userinfo/'
    try:
        req = requests.post(url, headers=headers, data=payload,
              timeout=(10, 10))
        req.raise_for_status()
    # Catch any exceptions like HTTP errors, connection errors,...
    except requests.exceptions.RequestException as e:
        if e.response is not None and e.response.status_code == 403:
            logging.critical('Login failed: wrong n°/email or password')
        else:
            logging.critical(e)
        sys.exit(1)

    cookie_value = extract_cookie(req.text)
    save_cookie(cookie_value)


def extract_cookie(raw_data):
    logging.debug('Extracting cookie value')
    result = re.search(r'value="(.*)"', raw_data)
    try:
        cookie_value = result.group(1)
    except AttributeError:
        logging.critical('Unable to obtain a valid cookie!')
        sys.exit(1)

    return cookie_value


def save_cookie(cookie_value):
    logging.debug('Writing cookie file ' + cookie_file)
    try:
        with open(cookie_file, 'w') as cf:
           cf.write(cookie_value)
    except IOError:
        logging.critical('Unable to write cookie file!')
        sys.exit(1)


def load_cookie():
    logging.debug('Loading cookie file ' + cookie_file)
    try:
        with open(cookie_file, 'r') as cf:
            return cf.read().strip()
    except IOError:
        logging.critical('Unable to read cookie file!')
        sys.exit(1)


def perform_auth():
    if not os.path.exists(cookie_file):
        logging.debug('Cookie file not found, creating...')
        grab_cookie()

    # Grab a new cookie and retry if the 1st attempt fails
    for i in range(2):
        cookie_value = load_cookie()
        url = 'https://hautdebitmobile.orange.fr:8443/wificom/logon'
        cookies = { 'wassup': cookie_value }
        try:
            req = requests.post(url, headers=headers, params=params,
                  cookies=cookies, timeout=(10, 10))
            req.raise_for_status()
        # Catch any exception like http error, connection error,...
        except requests.exceptions.RequestException as e:
            logging.critical(e)
            sys.exit(1)

        # '50' means login success, '100' means login failed
        auth_status = check_auth(req.text)
        if auth_status == '50':
            logging.info('Authentication successfull')
            return
        if i == 0 and auth_status == '100':
            logging.debug('Authentication refused, renewing cookie...')
            grab_cookie()
            continue

        logging.critical('Authentication failed! Response code : ' + auth_status)
        sys.exit(1)


def check_auth(raw_data):
    result = re.search(r'<ResponseCode>(.*)</ResponseCode>', raw_data)
    try:
        response_code = result.group(1)
        logging.debug('Response code : ' + response_code)
    except AttributeError:
        logging.critical('Unable to check authentication status!')
        sys.exit(1)

    return response_code
