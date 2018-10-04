"""

   Deployment API Manager

"""
import json
from datetime import timedelta
from enum import Enum

from nio.util.versioning.dependency import DependsOn
from nio import discoverable

from nio.modules.settings import Settings
from nio.modules.security import CoreServiceAccount
from nio.modules.security.access import set_user
from nio.modules.persistence import Persistence
from nio.modules.scheduler.job import Job

from niocore.core.component import CoreComponent

from .handler import DeploymentHandler
from .proxy import DeploymentProxy


@DependsOn('niocore.components.rest')
@discoverable
class DeploymentManager(CoreComponent):
    """ Handle configuration updates
    """

    class Status(Enum):
        started = 1
        accepted = 2
        in_progress = 3
        success = 4
        failed = 5

    _name = "DeploymentManager"

    def __init__(self):
        super().__init__()
        self._rest_manager = None
        self._config_handler = None
        self._api_proxy = None
        self._configuration_manager = None

        self.config_api_url_prefix = None
        self._api_key = None
        self._instance_id = None

        self._config_id = None
        self._config_version_id = None

        self._poll_job = None
        self._poll = None
        self._poll_interval = None

        self._configuration_manager = None
        self._start_stop_services = None
        self._delete_missing = None

    def configure(self, context):
        """ Configures component

        Establish dependency to RESTManager
        Fetches settings

        Args:
            context (CoreContext): component initialization context

        """

        super().configure(context)
        # Register dependency to rest manager
        self._rest_manager = self.get_dependency('RESTManager')
        self._configuration_manager = \
            self.get_dependency('ConfigurationManager')
        self._api_key_manager = self.get_dependency('APIKeyManager')

        # fetch component settings
        self.config_api_url_prefix = \
            Settings.get("configuration", "config_api_url_prefix",
                         fallback="https://api.n.io/v1")

        self._config_id = Persistence().load(
            "configuration_id",
            default=Settings.get("configuration", "config_id"))
        self._config_version_id = Persistence().load(
            "configuration_version_id",
            default=Settings.get("configuration", "config_version_id"))

        self._start_stop_services = Settings.getboolean(
            "configuration", "start_stop_services", fallback=True)
        self._delete_missing = Settings.getboolean(
            "configuration", "delete_missing", fallback=True)
        self._poll_interval = Settings.getint(
            "configuration", "config_poll_interval", fallback=0)

    def start(self):
        """ Starts component

        Instantiates DeploymentHandler and DeploymentProxy
        Begins polling job if it is set
        """
        super().start()
        self._api_proxy = DeploymentProxy(self.config_api_url_prefix, self)
        self._config_handler = DeploymentHandler(self)
        self._rest_manager.add_web_handler(self._config_handler)

        if self._poll_interval:
            self._poll_job = Job(self._run_config_update,
                                 timedelta(seconds=self._poll_interval),
                                 True)

    def stop(self):
        """ Stops component
        """
        self._rest_manager.remove_web_handler(self._config_handler)

        if self._poll_job:
            self._poll_job.cancel()
            self._poll_job = None

        super().stop()

    @property
    def api_key(self):
        return self._api_key_manager.api_key

    @property
    def instance_id(self):
        return self._api_key_manager.instance_id

    def _run_config_update(self):
        """Callback function to run update at each polling interval """
        self.logger.debug("Checking for latest configuration")
        # Assume our current "user" is the core's service account
        set_user(CoreServiceAccount())

        # Poll the product api for config ids this instance
        # should be running
        ids = self._api_proxy.get_instance_config_ids()
        if ids is None:
            # It didn't report any IDs to update to, so ignore
            return

        self.logger.debug("Desired configuration: {}".format(ids))
        config_id = ids.get("instance_configuration_id")
        config_version_id = ids.get("instance_configuration_version_id")

        if config_id == self.config_id and \
           config_version_id == self.config_version_id:
            self.logger.debug(
                "No change detected from current version, skipping")
            return

        self.logger.info(
            "New configuration detected...updating to config ID {} "
            "version {}".format(config_id, config_version_id))
        deployment_id = ids.get("deployment_id")
        result = self.update_configuration(
            config_id, config_version_id, deployment_id)

        self.logger.info("Configuration was updated: {}".format(result))

    def update_configuration(
            self,
            config_id,
            config_version_id,
            deployment_id=None):
        """ Update this instance to a given config/version ID.

        Args:
            config_id: The ID of the instance configuration to use
            config_version_id: The version ID of the instance config
            deployment_id: The optional deployment ID to set the status for

        Returns:
            result (dict): The result of the instance update call
        """
        # grab new configuration
        configuration = self._api_proxy.get_configuration(
            config_id, config_version_id)
        if configuration is None or "configuration_data" not in configuration:
            msg = "configuration_data entry missing in nio API return"
            self.logger.error(msg)
            raise RuntimeError(msg)

        configuration_data = json.loads(configuration["configuration_data"])
        # notify configuration acceptance
        self._api_proxy.set_reported_configuration(
            config_id,
            config_version_id,
            deployment_id,
            self.Status.accepted.name,
            "Services and Blocks configuration was accepted, "
            "proceeding with update")

        # perform update
        result = self._configuration_manager.update(
            configuration_data,
            self._start_stop_services,
            self._delete_missing)

        # instance is now running this configuration so persist this fact
        self.config_id = config_id
        self.config_version_id = config_version_id

        error_messages = self._get_potential_errors_messages(result)
        if error_messages:
            # notify failure
            self._api_proxy.set_reported_configuration(
                config_id,
                config_version_id,
                deployment_id,
                self.Status.failed.name,
                "Failed to update, these errors were encountered: {}".format(
                    error_messages))
        else:
            # report success and new instance config ids
            self._api_proxy.set_reported_configuration(
                config_id,
                config_version_id,
                deployment_id,
                self.Status.success.name,
                "Successfully updated services and blocks")
            self.logger.info("Configuration was updated, {}".format(result))

        return result

    def _get_potential_errors_messages(self, result):
        """Return any error messages contained in a result"""
        messages = []
        for key in result.keys():
            errors = result.get(key, {}).get("error", [])
            if errors:
                message = "Failed to install {}".format(key)
                for error in errors:
                    if isinstance(error, dict):
                        message += ", {}".format(json.dumps(error))
                    # providing API should send errors as dicts but just in
                    # case it does not, at least attempt to convert to str
                    else:
                        message += ", " + str(error)
                messages.append(message)
                # do not let errors go unnoticed
                self.logger.error("{} error: {}".format(key, errors))

        messages = ",".join(messages)
        if messages:
            self.logger.error(
                "{} errors were encountered during update: {}".format(
                    len(messages), messages))
        return messages

    @property
    def config_id(self):
        return self._config_id

    @config_id.setter
    def config_id(self, config_id):
        if self._config_id != config_id:
            self.logger.debug("Configuration ID set to: {}".format(config_id))
            self._config_id = config_id
            # persist value so that it can be read eventually
            # when component starts again
            Persistence().save(self.config_id, "configuration_id")

    @property
    def config_version_id(self):
        return self._config_version_id

    @config_version_id.setter
    def config_version_id(self, config_version_id):
        if self._config_version_id != config_version_id:
            self.logger.debug("Configuration Version ID set to: {}".
                              format(config_version_id))
            self._config_version_id = config_version_id
            # persist value so that it can be read eventually
            # when component starts again
            Persistence().save(
                self.config_version_id, "configuration_version_id")
