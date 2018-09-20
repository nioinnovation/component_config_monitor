from unittest.mock import patch

from ..proxy import DeploymentProxy


# noinspection PyProtectedMember
from nio.testing.test_case import NIOTestCase


class TestDeploymentProxy(NIOTestCase):

    def test_get_instance_config_ids(self):
        proxy = DeploymentProxy()
        with patch("{}.requests".format(DeploymentProxy.__module__)) \
                as request_patch:
            proxy.get_instance_config_ids(
                "api_url_prefix", "my_instance_id", "token")
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
        proxy = DeploymentProxy()
        with patch("{}.requests".format(DeploymentProxy.__module__)) \
                as request_patch:
            proxy.notify_instance_config_ids(
                "api_url_prefix", "my_instance_id",
                "config_id", "config_version_id", "token")
            headers = proxy._get_headers("token")

            desired_url = \
                "api_url_prefix/instances/my_instance_id/configuration"
            request_patch.post.assert_called_with(
                desired_url, headers=headers,
                json={
                    'reported_configuration_id': 'config_id',
                    'reported_configuration_version_id': 'config_version_id'
                }
            )

    def test_get_configuration(self):
        proxy = DeploymentProxy()
        with patch("{}.requests".format(DeploymentProxy.__module__)) \
                as request_patch:
            proxy.get_configuration("api",
                                    "config_id",
                                    "config_version_id",
                                    "token")
            headers = proxy._get_headers("token")

            test_headers = {
                "authorization": "apikey token",
                "content-type": "application/json"
            }
            self.assertEqual(headers, test_headers)

            desired_url = "api/config_id/versions/config_version_id"
            request_patch.get.assert_called_with(desired_url,
                                                 headers=headers)
