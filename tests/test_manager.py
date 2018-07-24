import json
from unittest.mock import MagicMock, patch

from nio.modules.web import RESTHandler
from niocore.core.context import CoreContext

from ..manager import DeploymentManager


# noinspection PyProtectedMember
from nio.testing.test_case import NIOTestCase


class TestDeploymentManager(NIOTestCase):

    def test_start_stop(self):
        # Test a handler is created and passed to REST Manager on start

        rest_manager = MagicMock()
        rest_manager.add_web_handler = MagicMock()
        context = CoreContext([], [])

        manager = DeploymentManager()
        manager.get_dependency = MagicMock(return_value=rest_manager)

        with patch("nio.modules.settings.Settings.get"):
            manager.configure(context)

        manager.start()
        rest_manager.add_web_handler.\
            assert_called_with(manager._config_handler)
        self.assertEqual(2, len(rest_manager.add_web_handler.call_args))
        self.assertTrue(
            isinstance(rest_manager.add_web_handler.call_args[0][0],
                       RESTHandler))
        manager.stop()
        rest_manager.remove_web_handler.\
            assert_called_with(manager._config_handler)

    def test_update_with_latest_version(self):
        manager = DeploymentManager()

        manager.api_key = "apikey"
        manager.config_api_url_prefix = "api"
        manager.config_id = "cfg_id"
        manager.config_version_id = "cfg_version_id"
        manager._api_proxy = MagicMock()
        manager.update_configuration = MagicMock()

        # Test that update isn't called when latest route fails
        manager._api_proxy.get_version.return_value = None

        with self.assertRaises(RuntimeError):
            manager._run_config_update()
            self.assertEqual(manager._api_proxy.get_version.call_count, 1)
            self.assertEqual(manager.update_configuration.call_count, 0)
        
        manager._api_proxy.reset_mock()
        # Test that update isn't called with the same version id
        manager._api_proxy.get_version.return_value = {
            "instance_configuration_version_id": "cfg_version_id"
        }

        manager._run_config_update()
        self.assertEqual(manager._api_proxy.get_version.call_count, 1)
        manager._api_proxy.get_version.\
            assert_called_once_with("api", "cfg_id", "apikey")
        self.assertEqual(manager.update_configuration.call_count, 0)

        manager._api_proxy.reset_mock()
        # Test update called with a new config version id
        manager._api_proxy.get_version.return_value = {
            "instance_configuration_version_id": "new_cfg_version_id"
        }
        manager._run_config_update()
        self.assertEqual(manager.update_configuration.call_count, 1)
        manager.update_configuration.\
            assert_called_once_with("api", "cfg_id", "new_cfg_version_id")

    def test_update_config(self):

        manager = DeploymentManager()

        # Set variables
        manager._start_stop_services = True
        manager._delete_missing = False
        manager.config_api_url_prefix = "api"
        manager.config_id = "cfg_id"
        manager.config_version_id = "cfg_version_id_1"
        
        # Mock methods/dependencies
        manager._api_proxy = MagicMock()
        manager._configuration_manager = MagicMock()

        configuration = {
            "blocks": {},
            "services": {},
            "blockTypes": {},
            "any_other_data": {}
        }
        manager._api_proxy.load_configuration.return_value = {
            "configuration_data": json.dumps(configuration)
        }
        manager._run_config_update()
        self.assertEqual(manager._configuration_manager.update.call_count, 1)
        call_args = manager._configuration_manager.update.call_args[0]
        self.assertDictEqual(call_args[0], configuration)
        self.assertEqual(call_args[1], True)
        self.assertEqual(call_args[2], False)

        # show that component is not tied to any configuration data fields other
        # than expecting a 'configuration_data' entry
        manager._api_proxy.load_configuration.return_value = {
            "a_field": "a_field_data"
        }
        manager.config_version_id = "cfg_version_id_2"
        with self.assertRaises(RuntimeError):
            manager._run_config_update()
            # assert update was not called since incoming data was not valid
        self.assertEqual(manager._configuration_manager.update.call_count, 1)

        manager._api_proxy.load_configuration.return_value = {
            "configuration_data": json.dumps({})
        }
        manager.config_version_id = "cfg_version_id_3"
        manager._run_config_update()
        self.assertEqual(manager._configuration_manager.update.call_count, 2)
