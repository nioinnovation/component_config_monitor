from unittest.mock import patch, Mock

from ..proxy import DeploymentProxy


# noinspection PyProtectedMember
from nio.testing.test_case import NIOTestCase


class TestDeploymentProxy(NIOTestCase):

    def test_get_instance_config_ids(self):
        proxy = DeploymentProxy("api_url_prefix", "token", "my_instance_id")
        with patch("{}.requests".format(DeploymentProxy.__module__)) \
                as request_patch:
            proxy.get_instance_config_ids()
            headers = proxy._get_headers("token")

            test_headers = {
                "authorization": "apikey token",
                "content-type": "application/json"
            }
            self.assertEqual(headers, test_headers)

            desired_url = \
                "api_url_prefix/instances/my_instance_id/configuration"
            request_patch.get.assert_called_with(desired_url,
                                                 headers=headers)

    def test_notify_instance_config_ids(self):
        proxy = DeploymentProxy("api_url_prefix", "token", "my_instance_id")

        cfg_id = "cfg_id"
        cfg_version_id = "cfg_version_id"
        deployment_id = "dep_id"
        status = "status"
        message = "message"

        with patch("{}.requests".format(DeploymentProxy.__module__)) \
                as request_patch:

            proxy.set_reported_configuration(
                cfg_id, cfg_version_id, deployment_id, status, message)
            headers = proxy._get_headers("token")

            desired_url = \
                "api_url_prefix/instances/my_instance_id/configuration"
            request_patch.post.assert_called_with(
                desired_url, headers=headers,
                json={
                    'reported_configuration_id': cfg_id,
                    'reported_configuration_version_id': cfg_version_id,
                    'deployment_id': deployment_id,
                    'status': status,
                    'message': message
                }
            )

    def test_get_configuration(self):
        proxy = DeploymentProxy("api", "token", "instance_id")
        with patch("{}.requests".format(DeploymentProxy.__module__)) \
                as request_patch:
            proxy.get_configuration("config_id",
                                    "config_version_id",
                                    )
            headers = proxy._get_headers("token")

            test_headers = {
                "authorization": "apikey token",
                "content-type": "application/json"
            }
            self.assertEqual(headers, test_headers)

            desired_url = "api/instance_configurations/" \
                          "config_id/versions/config_version_id"
            request_patch.get.assert_called_with(desired_url,
                                                 headers=headers)
