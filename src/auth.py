#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import requests
import json
import logging
import diag
import sys
import re


# These credentials are needed to connect to the captive portal
# The login is either a mobile phone number or an email address
login = ''
password = ''


auth_data = {

    'url': {
        'pre-auth': 'https://sso.orange.fr/WT/userinfo/',
        'post-auth': 'https://hautdebitmobile.orange.fr:8443/wificom/logon'
    },

    'headers': {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 5.1; Google Build/LMY47D)",
        "Accept": "*/*",
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive'
    },

    'payload': {
        'serv': 'WIFIOO',
        'info': 'cooses',
        'wt-msisdn': login,
        'wt-pwd': password,
        'wt-cvt': '4',
        'wt-mco': 'MCO=OFR'
    },

    'cookies': {
        'wassup': None
    },

    'params': {
        'lang': 'fr',
        'version': 'V2'
    }
}


# Switch key name depending on the type of credential (email or phone n°)
if "@orange.fr" in login:
    auth_data['payload']['wt-email'] = auth_data['payload']['wt-msisdn']
    del auth_data['payload']['wt-msisdn']


def extract_cookie(req):
    result = re.search(r'value="(.*)"', req)
    cookie_value = result.group(1)
    auth_data['cookies']['wassup'] = cookie_value


diag = diag.DiagTools()

def perform_auth():

    session = requests.Session()

    try:
        url = auth_data['url']['pre-auth']
        headers = auth_data['headers']
        payload = auth_data['payload']
        pre_auth = session.post(url, headers=headers, data=payload, timeout=(10, 10))
        pre_auth.raise_for_status()

        extract_cookie(pre_auth.text)

        url = auth_data['url']['post-auth']
        params = auth_data['params']
        cookies = auth_data['cookies']
        post_auth = requests.post(url, headers=headers, params=params, cookies=cookies, timeout=(10, 10))
        post_auth.raise_for_status()

    # Catch any exception like http error, connection error,...
    except requests.exceptions.RequestException as e:
        logging.critical(e)
        sys.exit(1)

    # Check if authentication is successful
    if diag.network_check() == 0:
        logging.info('Authentication successfull')
    else:
        logging.critical('Authentication failed!')
        sys.exit(1)
