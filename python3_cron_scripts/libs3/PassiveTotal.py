#!/usr/bin/python3

# Copyright 2018 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

"""
This module manages interactions with the PassiveTotal service.
"""

import configparser
import json
import logging
import time

import requests
from requests.auth import HTTPBasicAuth


class PassiveTotal(object):
    """
    This class is designed for interacting with PassiveTotal
    """

    pt_config_file = 'connector.config'
    KEY = None
    TOKEN = None
    URL = None
    _logger = None


    def _log(self):
        """
        Get the log
        """
        return logging.getLogger(__name__)


    @staticmethod
    def _get_config_setting(logger, config, section, key, type='str'):
        """
        Retrieves the key value from inside the section the connector.config file.

        This function is in multiple modules because it was originally designed
        that each module could be standalone.

        :param config: A Python ConfigParser object
        :param section: The section where the key exists
        :param key: The name of the key to retrieve
        :param type: (Optional) Specify 'boolean' to convert True/False strings to booleans.
        :return: A string or boolean from the config file.
        """
        try:
            if type == 'boolean':
                result = config.getboolean(section, key)
            else:
                result = config.get(section, key)
        except configparser.NoSectionError:
            logger.warning('Warning: ' + section + ' does not exist in config file')
            if type == 'boolean':
                return 0
            else:
                return ""
        except configparser.NoOptionError:
            logger.warning('Warning: ' + key + ' does not exist in the config file')
            if type == 'boolean':
                return 0
            else:
                return ""
        except configparser.Error as err:
            logger.warning('Warning: Unexpected error with config file')
            logger.warning(str(err))
            if type == 'boolean':
                return 0
            else:
                return ""

        return result


    def _init_passivetotal(self, config):
        self.URL = self._get_config_setting(self._logger, config, "PassiveTotal", "pt.url")
        self.KEY = self._get_config_setting(self._logger, config, "PassiveTotal", "pt.key")
        self.TOKEN = self._get_config_setting(self._logger, config, "PassiveTotal", "pt.token")


    def __init__(self, config_file="", log_level=None):
        if config_file != "":
            self.pt_config_file = config_file

        self._logger = self._log()

        if log_level is not None:
            self._logger.setLevel(log_level)

        config = configparser.ConfigParser()
        list = config.read(self.pt_config_file)
        if len(list) == 0:
            self._logger.error('Error: Could not find the config file')
            exit(0)

        self._init_passivetotal(config)


    def get_whois(self, email):
        """
        Fetches the whois records from PassiveTotal based on the registered email.
        @param email The email to search for in the whois records.
        """
        parameters = {'field': 'email', 'query': email}
        req = requests.get(self.URL + "whois/search", params=parameters,
                           auth=HTTPBasicAuth(self.TOKEN, self.KEY))

        if req.status_code != 200:
            self._logger.warning(req.status_code)
            self._logger.warning(req.text)
            time.sleep(5)
            req = requests.get(self.URL + "whois/search?field=email&query=" +email,
                               auth=HTTPBasicAuth(self.TOKEN, self.KEY))
            if req.status_code != 200:
                self._logger.error("Second email lookup attempt failed.")
                self._logger.error(req.status_code)
                self._logger.error(req.text)
                return None

        try:
            res = json.loads(req.text)
        except:
            return None

        return res


    def get_organization(self, organization):
        """
        Fetches the whois records from PassiveTotal based on the registered organization.
        @param email The email to search for in the whois records.
        """
        parameters = {'field': 'organization', 'query': organization}
        req = requests.get(self.URL + "whois/search", params= parameters,
                           auth=HTTPBasicAuth(self.TOKEN, self.KEY))

        if req.status_code != 200:
            self._logger.warning(req.status_code)
            self._logger.warning(req.text)
            time.sleep(5)
            req = requests.get(self.URL + "whois/search?field=organization&query=" + organization,
                               auth=HTTPBasicAuth(self.TOKEN, self.KEY))
            if req.status_code != 200:
                self._logger.error("Second org lookup attempt failed.")
                self._logger.error(req.status_code)
                self._logger.error(req.text)
                return None

        try:
            res = json.loads(req.text)
        except:
            return None

        return res
