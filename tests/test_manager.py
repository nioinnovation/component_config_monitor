from unittest.mock import MagicMock, ANY, patch

from nio.modules.web import RESTHandler
from niocore.core.context import CoreContext

from ..manager import ConfigManager


# noinspection PyProtectedMember
from nio.testing.test_case import NIOTestCase


class TestConfigManager(NIOTestCase):

    def test_start(self):
        # Test a handler is created and passed to REST Manager on start

        rest_manager = MagicMock()
        rest_manager.add_web_handler = MagicMock()
        context = CoreContext([], [])

        manager = ConfigManager()
        manager.get_dependency = MagicMock(return_value=rest_manager)

        with patch("nio.modules.settings.Settings.get"):
            manager.configure(context)

        manager.start()
        rest_manager.add_web_handler.assert_called_with(ANY)
        self.assertEqual(2, len(rest_manager.add_web_handler.call_args))
        self.assertTrue(
            isinstance(rest_manager.add_web_handler.call_args[0][0],
                       RESTHandler))
