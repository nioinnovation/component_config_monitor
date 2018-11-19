
from integration.base_test_case import NioIntegrationTestCase


class DirectDeploymentTestCase(NioIntegrationTestCase):

    def test_direct_deployment(self):
        """ Asserts that a project configuration is updated
        """
        settings = {
            "conf": {
                "instance": {
                    "api_key": "bda8fbb4-6056-459d-bc09-ce668fe1bbf9",
                    "instance_id": "c8bebdf8-534d-41e4-948d-b8a348ad3d4d"
                },
                "configuration": {
                    "config_api_url_prefix": "https://api.nio.solutions/v1",
                    "config_poll_interval": 0,
                    "start_stop_services": True,
                    "delete_missing": True
                },
                "service": {
                    "async_start": False
                }
            }
        }
        nio_id = None
        try:
            nio_id = self.start_nio(settings)

            # assert no services exist
            response = self.get(nio_id, "services")
            self.assertEquals(response, {})

            # provide nio with a direct deployment
            url = "config/update"
            body = {
                "deployment_id":
                    "fe944c1a-89d6-409d-83be-80ff51291ad3",
                "instance_configuration_id":
                    "d5149dc2-e8c1-4c62-ab72-9d8515e4d877",
                "instance_configuration_version_id":
                    "d89361c2-f9ed-4f41-91ea-f934c6445ea8"
            }
            self.put(nio_id, url, json=body)
            # assert services will eventually exist
            self.wait_for_condition(nio_id, "GET", "services",
                                    self._are_defined, timeout=5)
            # assert blocks will eventually exist
            self.wait_for_condition(nio_id, "GET", "blocks",
                                    self._are_defined, timeout=5)

        finally:
            if nio_id:
                self.stop_nio(nio_id)

    def _are_defined(self, response):
        return len(response) > 0
