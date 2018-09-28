import requests

from nio.util.logging import get_nio_logger


class DeploymentProxy(object):
    """ Serves as a Proxy to make Product API configuration requests
    """

    def __init__(self, url_prefix, api_key, instance_id):
        super().__init__()
        self.logger = get_nio_logger("ConfigProxy")

        self._url_prefix = url_prefix
        self._api_key = api_key
        self._instance_id = instance_id

    def get_instance_config_ids(self):
        """ Gets the conf id and conf version id the instance should be running

        Returns: an object with format
            {
                "instance_configuration_id": "uuid..",
                "instance_configuration_version_id": "uuid..",
                "deployment_id": "deployment_id..."
            }
        """
        url = "{}/instances/{}/configuration".format(
            self._url_prefix, self._instance_id)
        return self._request(
            requests.get, url, self._api_key,
            "Failed to get configuration version the instance "
            "should be running")

    def set_reported_configuration(self, config_id, config_version_id,
                                   deployment_id, status, message):
        """ Posts instance config ids and status

        Args:
            config_id (str): instance configuration id
            config_version_id (str): instance configuration version id
            deployment_id (str): deployment id
            status (str): deployment status
            message (str): deployment message
        """

        url = "{}/instances/{}/configuration".format(
            self._url_prefix, self._instance_id)
        return self._request(
            requests.post, url, self._api_key,
            "Failed to post new configuration version instance is running",
            json={
                "reported_configuration_id": config_id,
                "reported_configuration_version_id": config_version_id,
                "deployment_id": deployment_id,
                "status": status,
                "message": message
            }
        )

    def get_configuration(self, config_id, config_version_id):
        """  Retrieves an instance configuration

        Args:
            config_id (str): instance configuration id
            config_version_id (str): instance configuration version id

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
        url = "{}/instance_configurations/{}/versions/{}".format(
            self._url_prefix, config_id, config_version_id)
        return self._request(
            requests.get, url, self._api_key,
            "Failed to get instance configuration")

    def _request(self, fn, url, api_key, failed_msg, **kwargs):
        try:
            response = fn(
                url,
                headers=self._get_headers(api_key),
                **kwargs
            )
            response.raise_for_status()
            if response.ok:
                try:
                    return response.json()
                except ValueError:  # pragma no cover
                    return None
        except requests.exceptions.ConnectionError:  # pragma no cover
            self.logger.exception(failed_msg)

    @staticmethod
    def _get_headers(api_key):
        return {
            "authorization": "apikey {}".format(api_key),
            "content-type": "application/json"
        }
