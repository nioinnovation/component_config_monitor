
from integration.base_test_case import NioIntegrationTestCase


class IndirectDeploymentTestCase(NioIntegrationTestCase):

    def test_indirect_deployment(self):
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
                    "config_poll_interval": 1,
                    "config_id": "test_config_id",
                    "config_version_id": "test_config_version_id",
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
