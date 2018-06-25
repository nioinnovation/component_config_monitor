from threading import Event
from unittest.mock import MagicMock

from nio.modules.web.http import Request
from nio.testing.modules.security.module import TestingSecurityModule

from nio.testing.condition import ConditionWaiter
from niocore.configuration import CfgType
from niocore.core.hooks import CoreHooks

from ..handler import ConfigHandler

# noinspection PyProtectedMember
from nio.testing.web_test_case import NIOWebTestCase


class TestConfigHandler(NIOWebTestCase):

    def get_module(self, module_name):
        # Don't want to test permissions, use the test module
        if module_name == 'security':
            return TestingSecurityModule()
        else:
            return super().get_module(module_name)

    def test_on_get(self):
        manager = MagicMock()
        mock_req = MagicMock(spec=Request)
        mock_req.get_identifier.return_value = 'not_refresh'
        handler = ConfigHandler(None, None, None)

        # Verify error is raised with incorrect identifier
        request = mock_req
        response = MagicMock()
        with self.assertRaises(ValueError):
            handler.on_get(request, response)

    def test_on_put(self):
        manager = MagicMock()
        mock_req = MagicMock(spec=Request)
        mock_req.get_identifier.return_value = 'update'
        handler = ConfigHandler(None, None, None)

        # Verify error is raised with incorrect put body
        mock_req.get_body.return_value  = {}
        request = mock_req
        response = MagicMock()
        with self.assertRaises(ValueError):
            handler.on_put(request, response)

    def test_hooks_called(self):
        # Verify hook is called when callback is executed
        self._config_change_called = False
        CoreHooks.attach("configuration_change", self._on_config_change)

        url_prefix = "url_prefix"
        instance_id = "instance_id"
        api_key = "api_key"
        handler = ConfigHandler(url_prefix, instance_id, api_key)
        handler._trigger_config_change_hook(CfgType.all)

        # handle async hook execution
        event = Event()
        condition = ConditionWaiter(event, self._verify_config_change_called)
        condition.start()
        self.assertTrue(event.wait(1))
        condition.stop()

    def _on_config_change(self, cfg_type):
        self._config_change_called = True

    def _verify_config_change_called(self):
        return self._config_change_called