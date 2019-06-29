import json
from unittest.mock import MagicMock, patch, ANY

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

    def test_update_with_version(self):
        manager = DeploymentManager()
        manager._configuration_manager = MagicMock()
        core_updater = manager._configuration_manager.update

        cfg_id = "cfg_id"
        cfg_version_id = "cfg_version_id"
        deployment_id = "dep_id"

        manager._config_api_url_prefix = "api_url_prefix"
        manager._config_id = cfg_id
        manager._config_version_id = cfg_version_id
        manager._api_proxy = MagicMock()

        failed_resource_properties = {
            "id": "resource id",
            "name": "resource name",
            "prop": "prop value",
            "failed_prop": "failed prop value"
        }
        update_result = {
            "services": {
                "started": [],
                "stopped": [],
                "added": [],
                "modified": [],
                "ignored": [],
                "missing": [],
                "error": [
                    failed_resource_properties
                ]
            },
            "blocks": {
            },
            "blockTypes": {
                "error": [
                    "Failed to load dependency for block X"
                ]
            }
        }
        core_updater.return_value = update_result
        manager._api_proxy.get_configuration.return_value = {
            "configuration_data": json.dumps({
                "blocks": {},
                "services": {},
                "blockTypes": {},
            })
        }

        # Test that update isn't called when latest route fails
        manager._api_proxy.get_instance_config_ids.return_value = None

        manager._run_config_update()
        self.assertEqual(
            manager._api_proxy.get_instance_config_ids.call_count, 1)
        self.assertEqual(core_updater.call_count, 0)

        manager._api_proxy.reset_mock()
        # Test that update isn't called with the same version id
        manager._api_proxy.get_instance_config_ids.return_value = {
            "instance_configuration_id": cfg_id,
            "instance_configuration_version_id": cfg_version_id,
            "deployment_id": deployment_id
        }

        manager._run_config_update()
        self.assertEqual(
            manager._api_proxy.get_instance_config_ids.call_count, 1)
        manager._api_proxy.get_instance_config_ids.assert_called_once_with()
        self.assertEqual(core_updater.call_count, 0)

        manager._api_proxy.reset_mock()
        # Test update called with a new config version id
        cfg_version_id = "cfg_version_id1"
        manager._api_proxy.get_instance_config_ids.return_value = {
            "instance_configuration_id": cfg_id,
            "instance_configuration_version_id": cfg_version_id,
            "deployment_id": deployment_id
        }
        # run an update that reports an error
        manager._run_config_update()
        self.assertEqual(core_updater.call_count, 1)
        manager._api_proxy.set_reported_configuration.assert_called_with(
            cfg_id, cfg_version_id, deployment_id,
            DeploymentManager.Status.failure.name,
            ANY)

        # clear out errors
        update_result["services"]["error"] = []
        update_result["blockTypes"]["error"] = []
        # pretend a new version is being fetched
        cfg_version_id = "cfg_version_id2"
        manager._api_proxy.get_instance_config_ids.return_value = {
            "instance_configuration_id": cfg_id,
            "instance_configuration_version_id": cfg_version_id,
            "deployment_id": deployment_id
        }
        # run an update with no error
        manager._run_config_update()
        self.assertEqual(core_updater.call_count, 2)
        manager._api_proxy.set_reported_configuration.assert_any_call(
            cfg_id, cfg_version_id, deployment_id,
            DeploymentManager.Status.success.name,
            ANY
        )

    def test_update_config(self):

        manager = DeploymentManager()

        # Set variables
        manager._start_stop_services = True
        manager._delete_missing = False
        manager._config_id = "cfg_id"
        manager._config_version_id = "cfg_version_id_1"

        # Mock methods/dependencies
        manager._api_proxy = MagicMock()
        manager._configuration_manager = MagicMock()

        configuration = {
            "blocks": {},
            "services": {},
            "blockTypes": {}
        }
        manager._api_proxy.get_configuration.return_value = {
            "configuration_data": json.dumps(configuration)
        }
        manager._run_config_update()
        self.assertEqual(manager._configuration_manager.update.call_count, 1)
        call_args = manager._configuration_manager.update.call_args[0]
        self.assertDictEqual(call_args[0], configuration)
        self.assertEqual(call_args[1], True)
        self.assertEqual(call_args[2], False)

        # show that component is not tied to any configuration data fields
        # other than expecting a 'configuration_data' entry
        manager._api_proxy.get_configuration.return_value = {
            "a_field": "a_field_data"
        }
        manager.config_version_id = "cfg_version_id_2"
        with self.assertRaises(RuntimeError):
            manager._run_config_update()
            # assert update was not called since incoming data was not valid
        self.assertEqual(manager._configuration_manager.update.call_count, 1)

        manager._api_proxy.get_configuration.return_value = {
            "configuration_data": json.dumps({})
        }
        manager.config_version_id = "cfg_version_id_3"
        manager._run_config_update()
        self.assertEqual(manager._configuration_manager.update.call_count, 2)

    def test_polling(self):
        """ Assert polling is setup upon start and cleaned up upon stop
        """
        manager = DeploymentManager()

        manager._poll_interval = 1
        rest_manager = MagicMock()
        rest_manager.add_web_handler = MagicMock()
        manager._rest_manager = rest_manager

        self.assertIsNone(manager._poll_job)
        manager.start()
        self.assertIsNotNone(manager._poll_job)
        manager.stop()
        self.assertIsNone(manager._poll_job)

    def test_poll_on_start(self):
        """ Test optional polling on start
        """
        rest_manager = MagicMock()
        manager = DeploymentManager()
        manager.get_dependency = MagicMock(return_value=rest_manager)

        rest_manager = MagicMock()
        rest_manager.add_web_handler = MagicMock()
        manager._rest_manager = rest_manager

        context = CoreContext([], [])
        with patch("nio.modules.settings.Settings.get"):
            manager.configure(context)
            manager._poll_on_start = True

        with patch(manager.__module__ + '.DeploymentProxy') as mock_api:
            configuration = {
                "blocks": {},
                "services": {},
                "blockTypes": {},
            }
            mock_api.return_value.get_configuration.return_value = {
                "configuration_data": json.dumps(configuration),
            }
            manager.start()
        self.assertIsNone(manager._poll_job)
        self.assertEqual(manager._configuration_manager.update.call_count, 1)
        manager.stop()
