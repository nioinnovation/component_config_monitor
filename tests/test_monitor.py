from unittest.mock import MagicMock, ANY
from niocore.configuration import CfgType
from niocore.core.context import CoreContext
from niocore.core.hooks import CoreHooks
from nio.modules.web import RESTHandler
from niocore.testing.fast_tests import sleeping_test

from ..monitor import ConfigMonitor


# noinspection PyProtectedMember
from niocore.testing.test_case import NIOCoreTestCase


class TestConfigMonitor(NIOCoreTestCase):

    def test_start(self):
        # Test a handler is created and passed to REST Manager on start
        rest_manager = MagicMock()
        rest_manager.add_web_handler = MagicMock()

        context = CoreContext([], [])
        monitor = ConfigMonitor()
        monitor.get_dependency = MagicMock(return_value=rest_manager)
        monitor.configure(context)

        monitor.start()
        rest_manager.add_web_handler.assert_called_with(ANY)
        self.assertEqual(2, len(rest_manager.add_web_handler.call_args))
        self.assertTrue(
            isinstance(rest_manager.add_web_handler.call_args[0][0],
                       RESTHandler))

    @sleeping_test
    def test_hooks_called(self):
        # Verify hook is called when callback is executed
        context = CoreContext([], [])
        self._config_change_called = False
        CoreHooks.attach("configuration_change", self._on_config_change)
        monitor = ConfigMonitor()
        monitor.configure(context)
        monitor._trigger_hooks(CfgType.all)
        # allow time for thread execution
        from time import sleep
        sleep(0.05)
        self.assertTrue(self._config_change_called)

    def _on_config_change(self, cfg_type):
        self._config_change_called = True
