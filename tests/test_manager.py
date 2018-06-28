import json
from threading import Event
from unittest.mock import MagicMock, ANY, patch

from nio.modules.web import RESTHandler
from niocore.core.context import CoreContext
from niocore.core.hooks import CoreHooks
from nio.testing.condition import ConditionWaiter

from ..manager import ConfigManager


# noinspection PyProtectedMember
from nio.testing.test_case import NIOTestCase


class TestConfigManager(NIOTestCase):

    def test_start_stop(self):
        # Test a handler is created and passed to REST Manager on start

        rest_manager = MagicMock()
        rest_manager.add_web_handler = MagicMock()
        context = CoreContext([], [])

        manager = ConfigManager()
        manager.get_dependency = MagicMock(return_value=rest_manager)

        with patch("nio.modules.settings.Settings.get"):
            manager.configure(context)

        manager.start()
        rest_manager.add_web_handler.assert_called_with(manager._config_handler)
        self.assertEqual(2, len(rest_manager.add_web_handler.call_args))
        self.assertTrue(
            isinstance(rest_manager.add_web_handler.call_args[0][0],
                       RESTHandler))
        manager.stop()
        rest_manager.remove_web_handler.assert_called_with(manager._config_handler)

    def test_update_config(self):
        manager = ConfigManager()

        # Set variables
        manager._start_stop_services = True
        manager._delete_missing = False
        manager.config_api_url_prefix = "api"
        manager.config_id = "cfg_id"
        manager.config_version_id = "cfg_version_id"
        
        # Mock methods/dependancies
        manager._api_proxy = MagicMock()
        manager._configuration_manager = MagicMock()

        url = "api/cfg_id/versions/cfg_version_id"

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
        manager._api_proxy.load_configuration.return_value = {
            "configuration_data": {
                "blocks": blocks,
                "services": services
            }
        }
        manager._configuration_manager.update.return_value = {
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

        manager._run_config_update()
        self.assertEqual(manager._configuration_manager.update.call_count, 1)
        call_args = manager._configuration_manager.update.call_args[0]
        self.assertEqual(call_args[0], services)
        self.assertEqual(call_args[1], blocks)
        self.assertEqual(call_args[2], True)
        self.assertEqual(call_args[3], False)


    def test_hooks_called(self):
        # Verify hook is called when callback is executed
        self._config_change_called = False
        CoreHooks.attach("configuration_change", self._on_config_change)
        manager = ConfigManager()
        manager.trigger_config_change_hook('all')

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
