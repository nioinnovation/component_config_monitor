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
