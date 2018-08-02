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
user_agent="Mozilla/5.0 (X11; Linux x86_64; rv:55.0) Gecko/20100101 Firefox/55.0"

auth_url = "https://id.orange.fr/auth_user/bin/auth_user.cgi"
confirm_auth = "https://hautdebitmobile.orange.fr:8443/home/wassup"
lost_url = "https://r.orange.fr/Oid_lost"


def perform_auth():
    headers = { 'user-agent' : user_agent }
    session = requests.Session()
    cookies = {'co': '42'}
    params = {'co': '42', 'tt': '', 'tp': '', 'sv': 'owa', 'dp': 'basic',
            'losturl': lost_url, 'memorize_password': 'on', 'rl': confirm_auth,
            'credential': username, 'password': password}
    try :
        reqAuth = session.post(auth_url, cookies=cookies, data=params, headers=headers)
        net_status = diag.network_check()
        if net_status == 0 :
            logging.info('Authentifié avec succès, accès internet confirmé')
        else :
            logging.error("Authentification ignorée par le serveur!")
    except requests.exceptions.RequestException as e:
        logging.error(e)
