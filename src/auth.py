#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import requests
import logging
import diag


# Those credentials are needed in order to connect to the captive portal
# The login is either a phone number or a mail address for orange hotspots
username = ''
password = ''



#logging.getLogger("urllib3").setLevel(logging.WARNING)
userAgent="Mozilla/5.0 (X11; Linux x86_64; rv:55.0) Gecko/20100101 Firefox/55.0"

authUrl = "https://id.orange.fr/auth_user/bin/auth_user.cgi"
confirmAuth = "https://hautdebitmobile.orange.fr:8443/home/wassup"
lostUrl = "https://r.orange.fr/Oid_lost"


def performAuth():
    headers = { 'user-agent' : userAgent }
    session = requests.Session()
    cookies = {'co': '42'}
    params = {'co': '42', 'tt': '', 'tp': '', 'sv': 'owa', 'dp': 'basic',
            'losturl': lostUrl, 'memorize_password': 'on', 'rl': confirmAuth,
            'credential': username, 'password': password}
    try :
        reqAuth = session.post(authUrl, cookies=cookies, data=params, headers=headers)
        netStatus = diag.networkCheck()
        if netStatus == 0 :
            logging.info('Authentifié avec succès, accès internet confirmé')
        else :
            logging.error("Authentification ignorée par le serveur!")
    except requests.exceptions.RequestException as e:
        logging.error(e)
