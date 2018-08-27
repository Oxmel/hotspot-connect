#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import time
import logging
import subprocess
import diag
import iface
import re



# We use ap=None to set an optional arg
# So we can reuse the same method to connect to any AP with a given ESSID
# Or to connect to a specific AP with a given ESSID and BSSID
def join_ap(ap=None):

    associate = ""

    try:
        subprocess.check_call(associate, shell=True)
        # Wait a bit in case the association takes more time than expected
        time.sleep(5)
    except subprocess.CalledProcessError as e:
        logging.error(e)

