"""

   Deployment API Manager

"""
import json
from datetime import timedelta
from nio.util.versioning.dependency import DependsOn
from nio import discoverable

from nio.modules.settings import Settings
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

    _name = "DeploymentManager"

    def __init__(self):
        super().__init__()
        self._rest_manager = None
        self._config_handler = None
        self._api_proxy = None
        self._configuration_manager = None

        self._config_api_url_prefix = None
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

        # fetch component settings
        self._config_api_url_prefix = \
            Settings.get("configuration", "config_api_url_prefix",
                         fallback="https://api.n.io/v1/instance_configurations")

        self._config_id = Persistence().load(
            "configuration_id",
            default=Settings.get("configuration", "config_id"))
        self._config_version_id = Persistence().load(
            "configuration_version_id",
            default=Settings.get("configuration", "config_version_id"))

        self._start_stop_services = Settings.getboolean(
            "configuration", "start_stop_services", fallback=True)
        self._delete_missing = Settings.getboolean(
            "configuration", "delete_missing", fallback=False)

        # fetch instance specific settings
        self._api_key = Persistence().load(
            "api_key",
            default=Settings.get("configuration", "instance_api_key"))
        self._instance_id = Persistence().load(
            "instance_id",
            default=Settings.get("configuration", "instance_id"))

        # config autonomy specific settings
        self._poll_interval = Settings.getint("configuration",
                                              "config_poll_interval",
                                              fallback=0)

    def start(self):
        """ Starts component

        Instantiates DeploymentHandler and DeploymentProxy
        Begins polling job if it is set
        """
        super().start()
        self._api_proxy = DeploymentProxy()
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
        
        if self._poll_interval:
            self._poll_job.cancel()
        
        super().stop()

    def _run_config_update(self):
        # Callback function to run update at the end of each polling interval

        # Poll the product api for config ids this instance
        # should be running
        ids = self._api_proxy.get_instance_config_ids(
            self._config_api_url_prefix, self._instance_id, self._api_key)
        if ids is None:
            msg = "Failure to retrieve expected instance version " \
                  "from nio API return"
            self.logger.error(msg)
            raise RuntimeError(msg)

        config_id = ids.get("instance_configuration_id")
        config_version_id = ids.get("instance_configuration_version_id")
        # Update instance if versions differ
        if config_id != self.config_id or \
           config_version_id != self.config_version_id:
            result = self.update_configuration(config_id,
                                               config_version_id)
            self.logger.info("Configuration was updated, {}".format(result))

            # persist new ids
            self.config_id = config_id
            self.config_version_id = config_version_id

            # notify product api about new instance config ids
            self._api_proxy.notify_instance_config_ids(
                self._config_api_url_prefix, self._instance_id,
                config_id, config_version_id, self._api_key)

    def update_configuration(self, config_id, config_version_id):
        configuration = \
            self._api_proxy.get_configuration(self._config_api_url_prefix,
                                              config_id,
                                              config_version_id,
                                              self._api_key)
        if configuration is None or "configuration_data" not in configuration:
            msg = "configuration_data entry missing in nio API return"
            self.logger.error(msg)
            raise RuntimeError(msg)

        configuration_data = json.loads(configuration["configuration_data"])
        return self._configuration_manager.update(
            configuration_data, self._start_stop_services, self._delete_missing)

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
            Persistence().save(self.config_id,
                               "configuration_id")

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
            Persistence().save(self.config_version_id,
                               "configuration_version_id")
