from unittest.mock import MagicMock

from nio.modules.web.http import Request, Response
from nio.testing.modules.security.module import TestingSecurityModule

from niocore.configuration import CfgType

from ..handler import DeploymentHandler

# noinspection PyProtectedMember
from nio.testing.web_test_case import NIOWebTestCase


class TestDeploymentHandler(NIOWebTestCase):

    def get_module(self, module_name):
        # Don't want to test permissions, use the test module
        if module_name == 'security':
            return TestingSecurityModule()
        else:
            return super().get_module(module_name)

    def test_on_get(self):
        """ Asserts 'GET' call NotImplemented response.
        """
        handler = DeploymentHandler(None)
        with self.assertRaises(NotImplementedError):
            handler.on_get(MagicMock(spec=Request), MagicMock(spec=Response))

    def test_on_put(self):
        config_api_url_prefix = None
        api_key = None
        config_id = None
        config_version_id = None
        manager = MagicMock(config_api_url_prefix=config_api_url_prefix,
                            config_id=config_id,
                            config_version_id=config_version_id)
        manager.update_configuration = MagicMock()
        manager.update_configuration.return_value = \
            dict({"foo": "bar"})
        mock_req = MagicMock(spec=Request)
        mock_req.get_identifier.return_value = 'update'
        handler = DeploymentHandler(manager)

        # Verify error is raised with incorrect put body
        mock_req.get_body.return_value = {}
        request = mock_req
        response = MagicMock()
        with self.assertRaises(ValueError):
            handler.on_put(request, response)

        mock_req.get_body.return_value = {
            "url": "api",
            "instance_configuration_id": "config_id",
            "instance_configuration_version_id": "config_version_id"
        }
        request = mock_req
        handler.on_put(request, response)
        handler._manager.update_configuration.\
            assert_called_once_with("api",
                                    "config_id",
                                    "config_version_id")
    