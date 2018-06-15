import requests
from urllib.parse import urlencode

from nio.util.logging import get_nio_logger


class ConfigurationProxy(object):
    """ Serves as a Proxy to make Product API configuration requests
    """

    def __init__(self):
        super().__init__()
        self.logger = get_nio_logger("ConfigurationProxy")

    def load_configuration(self, url, token, org_id):
        """ 
        Retrieves an instance configruation by a instance_configuration_id 
        and a instance_configuration_version_id
        """
        
        try:
            response = requests.get(
                url,
                headers=self._get_headers(token, org_id)
            )
            if response.ok:
                return response.json()
        except requests.exceptions.ConnectionError:
            self.logger.exception("Failed to load configuration")

    @staticmethod
    def _get_headers(token, org_id):
        return {
            "authorization": "bearer {}".format(token), 
            "nio-organization": org_id,
            "content-type": "application/json"
        }
