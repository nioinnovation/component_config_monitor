import requests

from nio.util.logging import get_nio_logger


class DeploymentProxy(object):
    """ Serves as a Proxy to make Product API configuration requests
    """

    def __init__(self):
        super().__init__()
        self.logger = get_nio_logger("ConfigProxy")

    def get_instance_config_ids(self, url_prefix, instance_id, apikey):
        """ Gets the conf id and conf version id the instance should be running

        Args:
            url_prefix (str): url prefix to product api
            instance_id (str): instance id
            apikey (str): api key

        Returns: an object with format
            {
                "instance_configuration_id": "uuid..",
                "instance_configuration_version_id": "uuid..",
                "version_num": "v1.0.0",
                "created_at": "2018-03-14 12:12:12"
            }
        """
        url = "{}/instances/{}/configuration".format(url_prefix,
                                                     instance_id)
        return self._request(
            requests.get, url, apikey, "Failed to get configuration version "
                                       "the instance should be running")

    def notify_instance_config_ids(self, url_prefix, instance_id, config_id,
                                   config_version_id, apikey):
        """ Posts instance config ids

        Args:
            url_prefix (str): url prefix to product api
            instance_id (str): instance id
            config_id (str): instance configuration id
            config_version_id (str): instance configuration version id
            apikey (str): api key
        """

        url = "{}/instances/{}/configuration".format(url_prefix,
                                                     instance_id)
        return self._request(
            requests.post, url, apikey, "Failed to post new configuration "
                                        "version instance is running",
            json={
                "reported_configuration_id": config_id,
                "reported_configuration_version_id": config_version_id
            }
        )

    def get_configuration(self, url_prefix, config_id,
                          config_version_id, apikey):
        """  Retrieves an instance configuration

        Args:
            url_prefix (str): url prefix to product api
            config_id (str): instance configuration id
            config_version_id (str): instance configuration version id
            apikey (str): api key

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
        url = "{}/{}/versions/{}".format(url_prefix,
                                         config_id,
                                         config_version_id)
        return self._request(
            requests.get, url, apikey, "Failed to get instance configuration")

    def _request(self, fn, url, apikey, failed_msg, **kwargs):
        try:
            response = fn(
                url,
                headers=self._get_headers(apikey),
                **kwargs
            )
            response.raise_for_status()
            if response.ok:
                try:
                    return response.json()
                except ValueError:
                    return None
        except requests.exceptions.ConnectionError:
            self.logger.exception(failed_msg)

    @staticmethod
    def _get_headers(apikey):
        return {
            "authorization": "apikey {}".format(apikey),
            "content-type": "application/json"
        }
