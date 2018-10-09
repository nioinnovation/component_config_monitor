import requests
from requests.exceptions import HTTPError, ConnectionError

from nio.util.logging import get_nio_logger


class DeploymentProxy(object):
    """ Serves as a Proxy to make Product API configuration requests
    """

    def __init__(self, url_prefix, manager):
        super().__init__()
        self.logger = get_nio_logger("DeploymentManager")

        self._url_prefix = url_prefix
        self._manager = manager

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
            self._url_prefix, self._manager.instance_id)
        try:
            return self._request(
                fn=requests.get,
                url=url,
                failed_msg=("Failed to get configuration version the instance "
                            "should be running")
            )
        except HTTPError as e:
            if e.response.status_code == 404:
                # This likely indicates that no desired configuration was
                # found for this particular instance ID, nothing to cause alarm
                self.logger.info(e.response.json().get("message"))
            else:
                self.logger.error("Error fetching instance config: {}".format(
                    e.response.json().get(
                        "message", "No error message provided")))
                raise

    def set_reported_configuration(
            self,
            config_id,
            config_version_id,
            deployment_id,
            status="",
            message=""):
        """ Posts instance config ids and status

        Args:
            config_id (str): instance configuration id
            config_version_id (str): instance configuration version id
            deployment_id (str): Deployment id that the status
                and message belongs to
            status (str): deployment status
            message (str): deployment message
        """

        url = "{}/instances/{}/configuration".format(
            self._url_prefix, self._manager.instance_id)
        body = {
            "reported_configuration_id": config_id,
            "reported_configuration_version_id": config_version_id,
            "deployment_id": deployment_id,
            "status": status,
            "message": message,
        }
        return self._request(
            fn=requests.post,
            url=url,
            failed_msg=("Failed to post new configuration version "
                        "instance is running"),
            json=body
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
            fn=requests.get,
            url=url,
            failed_msg="Failed to get instance configuration")

    def _request(self, fn, url, failed_msg, **kwargs):
        headers = {
            "authorization": "apikey {}".format(self._manager.api_key),
            "content-type": "application/json"
        }
        try:
            response = fn(url, headers=headers, **kwargs)
        except ConnectionError:
            self.logger.exception(failed_msg)
        response.raise_for_status()
        return response.json()
