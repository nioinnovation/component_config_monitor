import json
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
        mock_req = MagicMock(spec=Request)
        mock_req.get_identifier.return_value = 'not_refresh'
        handler = ConfigHandler(None, None, None, None, None, None)

        # Verify error is raised with incorrect identifier
        request = mock_req
        response = MagicMock()
        with self.assertRaises(ValueError):
            handler.on_get(request, response)

    def test_on_put(self):
        mock_req = MagicMock(spec=Request)
        mock_req.get_identifier.return_value = 'update'
        config_manager = MagicMock()
        start_stop_services = True
        delete_missing = False
        handler = ConfigHandler("url_prefix", None, None, config_manager,
                                start_stop_services, delete_missing)
        handler._proxy = MagicMock()

        # Verify error is raised with incorrect put body
        mock_req.get_body.return_value = {}
        request = mock_req
        response = MagicMock()
        with self.assertRaises(ValueError):
            handler.on_put(request, response)

        mock_req.get_body.return_value = {
            "instance_configuration_id": "inst_config_id",
            "instance_configuration_version_id": "inst_config_version_id"
        }
        with self.assertRaises(RuntimeError):
            handler.on_put(request, response)

        blocks = {
            "block_id": {
                "id": "block_id"
            }
        }
        services = {
            "service_id": {
                "id": "service_id"
            }
        }
        handler._proxy.load_configuration.return_value = {
            "configuration_data": {
                "blocks": blocks,
                "services": services
            }
        }
        config_manager.update.return_value = {
            "services": {
                "started": [],
                "stopped": [],
                "added": [],
                "modified": [],
                "ignored": [],
                "missing": []
            },
            "blocks": {
                "added": [],
                "modified": [],
                "ignored": [],
                "missing": []
            }
        }

        handler.on_put(request, response)

        # assert calls to update
        self.assertEqual(config_manager.update.call_count, 1)
        call_args = config_manager.update.call_args[0]
        self.assertEqual(call_args[0], services)
        self.assertEqual(call_args[1], blocks)
        self.assertEqual(call_args[2], start_stop_services)
        self.assertEqual(call_args[3], delete_missing)

        # assert api response
        response_body = json.loads(response.set_body.call_args[0][0])
        self.assertDictEqual(response_body, config_manager.update.return_value)

    def test_hooks_called(self):
        # Verify hook is called when callback is executed
        self._config_change_called = False
        CoreHooks.attach("configuration_change", self._on_config_change)

        url_prefix = "url_prefix"
        instance_id = "instance_id"
        api_key = "api_key"
        handler = ConfigHandler(url_prefix, instance_id, api_key,
                                None, None, None)
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