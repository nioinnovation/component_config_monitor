from unittest.mock import patch, Mock

from ..proxy import DeploymentProxy


# noinspection PyProtectedMember
from nio.testing.test_case import NIOTestCase


@patch("{}.requests".format(DeploymentProxy.__module__))
class TestDeploymentProxy(NIOTestCase):

    def setUp(self):
        super().setUp()
        manager = Mock()
        manager.api_key = "token"
        manager.instance_id = "my_instance_id"
        self._proxy = DeploymentProxy("api_url_prefix", manager)

    def test_get_instance_config_ids(self, mock_req):
        self._proxy.get_instance_config_ids()
        expected_headers = {
            "authorization": "apikey token",
            "content-type": "application/json"
        }

        desired_url = "api_url_prefix/instances/my_instance_id/configuration"
        mock_req.get.assert_called_with(desired_url, headers=expected_headers)

    def test_notify_instance_config_ids(self, mock_req):
        cfg_id = "cfg_id"
        cfg_version_id = "cfg_version_id"
        deployment_id = "dep_id"
        status = "status"
        message = "message"
        expected_headers = {
            "authorization": "apikey token",
            "content-type": "application/json"
        }

        self._proxy.set_reported_configuration(
            cfg_id, cfg_version_id, deployment_id, status, message)

        desired_url = \
            "api_url_prefix/instances/my_instance_id/configuration"
        mock_req.post.assert_called_with(
            desired_url,
            headers=expected_headers,
            json={
                'reported_configuration_id': cfg_id,
                'reported_configuration_version_id': cfg_version_id,
                'deployment_id': deployment_id,
                'status': status,
                'message': message
            }
        )

    def test_notify_instance_config_ids_without_deployment(self, mock_req):
        cfg_id = "cfg_id"
        cfg_version_id = "cfg_version_id"
        status = "status"
        message = "message"
        expected_headers = {
            "authorization": "apikey token",
            "content-type": "application/json"
        }

        self._proxy.set_reported_configuration(
            cfg_id, cfg_version_id, None, status, message)

        desired_url = \
            "api_url_prefix/instances/my_instance_id/configuration"
        mock_req.post.assert_called_with(
            desired_url,
            headers=expected_headers,
            json={
                'reported_configuration_id': cfg_id,
                'reported_configuration_version_id': cfg_version_id,
                'status': status,
                'message': message
            }
        )

    def test_get_configuration(self, mock_req):
        self._proxy.get_configuration("config_id", "config_version_id")
        expected_headers = {
            "authorization": "apikey token",
            "content-type": "application/json"
        }
        desired_url = ("api_url_prefix/instance_configurations/config_id/"
                       "versions/config_version_id")
        mock_req.get.assert_called_with(desired_url, headers=expected_headers)
