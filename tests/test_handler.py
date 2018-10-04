from unittest.mock import MagicMock

from nio.modules.web.http import Request, Response
from nio.testing.modules.security.module import TestingSecurityModule

from ..manager import DeploymentManager
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

    def setUp(self):
        super().setUp()
        self._manager = MagicMock(spec=DeploymentManager)
        self._manager.update_configuration.return_value = {"foo": "bar"}
        self._handler = DeploymentHandler(self._manager)

    def test_on_get(self):
        """ Asserts 'GET' call NotImplemented response.
        """
        handler = DeploymentHandler(None)
        with self.assertRaises(NotImplementedError):
            handler.on_get(MagicMock(spec=Request), MagicMock(spec=Response))

    def test_on_put_updates(self):
        mock_req = MagicMock(spec=Request)
        mock_req.get_identifier.return_value = 'update'
        mock_req.get_body.return_value = {
            "instance_configuration_id": "config_id",
            "instance_configuration_version_id": "config_version_id",
        }
        self._handler.on_put(mock_req, MagicMock())
        self._manager.update_configuration.assert_called_once_with(
            "config_id", "config_version_id")

    def test_on_put_bad_body(self):
        """ Verify an error is raised with incorrect put body """
        mock_req = MagicMock(spec=Request)
        mock_req.get_identifier.return_value = 'update'
        mock_req.get_body.return_value = {}
        with self.assertRaises(ValueError):
            self._handler.on_put(mock_req, MagicMock())

        # Verify error is raised when missing instance_configuration_version_id
        mock_req.get_body.return_value = {
            "instance_configuration_id": "config_id",
        }
        with self.assertRaises(ValueError):
            self._handler.on_put(mock_req, MagicMock())

    def test_on_put_bad_identifier(self):
        mock_req = MagicMock(spec=Request)
        mock_req.get_identifier.return_value = 'not_an_update'
        mock_req.get_body.return_value = {}
        with self.assertRaises(ValueError):
            self._handler.on_put(mock_req, MagicMock())
