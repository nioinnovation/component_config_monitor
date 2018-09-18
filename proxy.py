import requests

from nio.util.logging import get_nio_logger


class DeploymentProxy(object):
    """ Serves as a Proxy to make Product API configuration requests
    """

    def __init__(self):
        super().__init__()
        self.logger = get_nio_logger("ConfigProxy")

    def get_version(self, url_prefix, config_id, apikey):
        """
        Retrieves the latest instance configuration version id

        Returns: an object with format
            {
                "instance_configuration_version_id": "uuid..",
                "version_num": "v1.0.0",
                "created_at": "2018-03-14 12:12:12"
            }
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

    def load_configuration(self, url_prefix, instance_id, apikey):
        """ Retrieves an instance configuration by an instance_id and apikey

        Returns: configuration with format
            {
                "configuration_data": {
                    "version": 1.0.0,
                    "blocks": {...},
                    "services": {...},
                    "blockTypes": {...}
                },
                "message": "Found Instance Configuration...",
                "status": 200,
                "uuid": "uuid..",
                "version_num": "v1.0.0"
            }
        """
        
        try:
            url = "{}/instances/{}/configuration".format(url_prefix,
                                                         instance_id)
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
