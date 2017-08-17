import requests
from urllib.parse import urlencode

from nio.util.logging import get_nio_logger


class ConfigurationProxy(object):
    """ Serves as a Proxy to make Product API configuration requests
    """

    def __init__(self):
        super().__init__()
        self.logger = get_nio_logger("ConfigurationProxy")

    def load_collection(self, name, url, token):
        """ Retrieves a collection by its name
        """

        self.logger.info("Loading '{}' collection".format(name))
        payload = urlencode({
            "collection": name
        })
        try:
            response = requests.get(
                url,
                params=payload,
                headers=self._get_headers(token)
            )
            if response.ok:
                return response.json()
        except requests.exceptions.ConnectionError:
            self.logger.exception("Failed to load collection")

    @staticmethod
    def _get_headers(token):
        return {"authorization": "bearer {}".format(token)}
