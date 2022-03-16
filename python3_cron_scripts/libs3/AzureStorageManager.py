#!/usr/bin/python3

# Copyright 2022 Adobe Inc. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

"""
This is a simple interface for Azure Blob interactions.
DO NOT rename the methods since they are meant to be inherited by the storage manager class.
This currently assumes that the credentials can be identified using the approach described in
DefaultAzureCredential() method.
https://docs.microsoft.com/en-us/python/api/azure-identity/azure.identity.defaultazurecredential?view=azure-python
"""

import configparser
import logging
from ast import Bytes

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobClient, BlobServiceClient
from libs3.ConnectorUtil import ConnectorUtil


class AzureStorageManager(object):
    _logger = None
    _storage_config_file = "connector.config"

    _azure_account_url = ""
    _azure_service_client = ""
    _azure_creds = None

    def _log(self):
        """
        Get the log
        """
        return logging.getLogger(__name__)

    def _auth_to_azure(self, config):
        """
        Authenticate to Azure
        """
        self._azure_account_url = ConnectorUtil.get_config_setting(
            self._logger, config, "Azure", "az.storage_account_url"
        )

        self._azure_creds = DefaultAzureCredential()
        self._azure_service_client = BlobServiceClient(
            account_url=self._azure_account_url, credential=self._azure_creds
        )

    def __init__(self, config_file="", log_level=None) -> None:
        """
        Initialize the class
        """

        self._logger = self._log()
        if log_level is not None:
            self._logger.setLevel(log_level)

        if config_file != "":
            self._storage_config_file = config_file

        config = configparser.ConfigParser()
        list = config.read(self._storage_config_file)
        if len(list) == 0:
            self._logger.error("Error: Could not find the config file")
            exit(1)

        self._auth_to_azure(config)

    def write_file(self, folder: str, filename: str, data: bytes) -> bool:
        """
        Write the file to an Azure Container
        """
        try:
            blob_client = BlobClient(
                account_url=self._azure_account_url,
                container_name=folder,
                blob_name=filename,
                credential=self._azure_creds,
            )
            blob_client.upload_blob(data=data)
        except Exception as err:
            self._logger.error("Could not upload Blob file")
            self._logger.error(str(err))
            return False

        return True

    def write_large_file(
        self, folder: str, remote_filename: str, local_file_path: str
    ) -> bool:
        """
        Write a large file that requires streaming to an Azure container
        """
        # upload 4 MB for each request
        chunk_size = 4 * 1024 * 1024

        blob_client = BlobClient(
            account_url=self._azure_account_url,
            container_name=folder,
            blob_name=remote_filename,
            credential=self._azure_creds,
        )

        blob_client.create_append_blob()

        try:
            with open(local_file_path, "rb") as stream:

                while True:
                    read_data = stream.read(chunk_size)

                    if not read_data:
                        self._logger.info("uploaded")
                        break

                    blob_client.append_block(read_data)

        except Exception as err:
            self._logger.error("Could not upload large Blob file")
            self._logger.error(str(err))
            return False

    def create_folder(self, foldername: str) -> bool:
        """
        Create an Azure container
        """

        try:
            self._azure_service_client.create_container(name=foldername)
        except Exception as err:
            self._logger.error("Could not create Container")
            self._logger.error(str(err))
            return False

        return True

    def read_file(self, foldername: str, filename: str) -> Bytes:
        """
        Read a blob from Azure
        """
        try:
            blob_client = BlobClient(
                account_url=self._azure_account_url,
                container_name=foldername,
                blob_name=filename,
                credential=self._azure_creds,
            )
            blob_download = blob_client.download_blob()
            data = blob_download.readall()
        except Exception as err:
            self._logger.error(
                "Could not download blob " + filename + " from " + foldername
            )
            self._logger.error(str(err))
            return None

        return data