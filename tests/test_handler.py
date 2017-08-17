from threading import Event

from nio.testing.condition import ConditionWaiter
from niocore.configuration import CfgType
from niocore.core.hooks import CoreHooks

from ..handler import ConfigHandler


# noinspection PyProtectedMember
from nio.testing.test_case import NIOTestCase


class TestConfigHandler(NIOTestCase):

    def test_hooks_called(self):
        # Verify hook is called when callback is executed

        self._config_change_called = False
        CoreHooks.attach("configuration_change", self._on_config_change)

        url_prefix = "url_prefix"
        instance_id = "instance_id"
        handler = ConfigHandler(url_prefix, instance_id)
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