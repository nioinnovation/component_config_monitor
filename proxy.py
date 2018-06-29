import requests

from nio.util.logging import get_nio_logger


class ConfigProxy(object):
    """ Serves as a Proxy to make Product API configuration requests
    """

    def __init__(self):
        super().__init__()
        self.logger = get_nio_logger("ConfigProxy")

    def get_version(self, url_prefix, config_id, apikey):
        """
        Retrieves the latest instance configuration version id

        Returns: a configuration vesion id string
        """

        try:
            url = "{}/{}/versions/latest".format(url_prefix, config_id)
            response = requests.get(
                url,
                headers=self._get_headers(apikey)
            )
            if response.ok:
                return response.json()
        except requests.exceptions.ConnectionError:
            self.logger.exception("Failed to get configuration version")

    def load_configuration(self, url_prefix, config_id, config_version_id, apikey):
        """ 
        Retrieves an instance configruation by a instance_configuration_id 
        and a instance_configuration_version_id

        Returns: configuration with format
            {
                "configuration_data": {
                    "version": 1.0.0,
                    "blocks": {...},
                    "services": {...},
                },
                "message": "Found Instance Configuration...",
                "status": 200,
                "uuid": "uuid..",
                "version_num": "v1.0.0"
            }
        """
        
        try:
            url = "{}/{}/versions/{}".format(url_prefix,
                                             config_id,
                                             config_version_id)
            response = requests.get(
                url,
                headers=self._get_headers(apikey)
            )
            if response.ok:
                return response.json()
        except requests.exceptions.ConnectionError:
            self.logger.exception("Failed to load configuration")

    @staticmethod
    def _get_headers(apikey):
        return {
            "authorization": "apikey {}".format(apikey),
            "content-type": "application/json"
        }
