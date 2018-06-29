"""

   Configuration Manager

"""
from datetime import timedelta
from nio.util.versioning.dependency import DependsOn
from nio import discoverable

from nio.modules.settings import Settings
from nio.modules.persistence import Persistence
from nio.modules.scheduler.job import Job

from niocore.util.environment import NIOEnvironment

from niocore.core.hooks import CoreHooks
from niocore.core.component import CoreComponent

from .handler import ConfigHandler
from .proxy import ConfigProxy

@DependsOn('niocore.components.rest')
@discoverable
class ConfigManager(CoreComponent):
    """ Handle configuration updates
    """

    _name = "ConfigManager"

    def __init__(self):
        super().__init__()
        self._rest_manager = None
        self._config_handler = None
        self._api_proxy = None
        self._configuration_manager = None

        self.config_api_url_prefix = None
        self.api_key = None
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
        self.config_api_url_prefix = \
            Settings.get("configuration", "config_api_url_prefix",
                fallback="https://api.nio.works/v1/instance_configurations")

        setting_config_id = Settings.get("configuration", "config_id",
            fallback=None)
        self._config_id = Persistence().load("configuration_id",
                                            default=setting_config_id)
        setting_config_version_id = \
            Settings.get("configuration", "config_version_id",
                fallback=None)
        self._config_version_id = Persistence().\
            load("configuration_version_id", default=setting_config_version_id)
        
        self._start_stop_services = Settings.getboolean(
            "configuration", "start_stop_services", fallback=True)
        self._delete_missing = Settings.getboolean(
            "configuration", "delete_missing", fallback=False)

        # fetch instance specific settings
        default = Persistence().load("api_key", default=None)
        self.api_key = NIOEnvironment.get_variable('API_KEY', 
                                                   default=default)

        # config autonomy spcific settings
        self._poll_interval = Settings.getint("configuration",
                                              "config_poll_interval",
                                              fallback=0)

    def start(self):
        """ Starts component

        Instantiates ConfigHandler and ConfigProxy
        Begins polling job if it is set
        """
        super().start()
        self._api_proxy = ConfigProxy()
        self._config_handler = ConfigHandler(self)
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

        # Poll the product api for the latest config version id
        latest_version_id = \
            self._api_proxy.get_version(self.config_api_url_prefix,
                                        self.config_id,
                                        self.api_key)
        config_version_id = \
            latest_version_id.get("instance_configuration_version_id")
        # Update instance with new config version id
        if config_version_id != self.config_version_id:
            self.config_version_id = config_version_id
            result = self.update_configuration(self.config_api_url_prefix,
                                               self.config_id,
                                               self.config_version_id)
            self.logger.info("Configuration was updated, {}".format(result))

    def update_configuration(self, url_prefix, config_id, config_version_id):
        configuration = \
            self._api_proxy.load_configuration(url_prefix,
                                               config_id,
                                               config_version_id,
                                               self.api_key) or {}
        if "configuration_data" not in configuration:
            msg = "configuration_data entry missing in nio API return"
            self.logger.error(msg)
            raise RuntimeError(msg)

        configuration_data = configuration["configuration_data"]
        services = configuration_data.get("services", {})
        blocks = configuration_data.get("blocks", {})
        return self._configuration_manager.update(
            services, blocks, self._start_stop_services, self._delete_missing)

    def trigger_config_change_hook(self, cfg_type):
        """ Executes hook indicating configuration changes
        """
        self.logger.debug("Triggering configuration change hook")
        CoreHooks.run('configuration_change', cfg_type)

    @property
    def config_id(self):
        return self._config_id

    @config_id.setter
    def config_id(self, config_id):
        self.logger.debug("Configuration ID set to: {}"\
            .format(config_id))
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
        self.logger.debug("Configuration Version ID set to: {}"\
            .format(config_version_id))
        self._config_version_id = config_version_id
        # persist value so that it can be read eventually
        # when component starts again
        Persistence().save(self.config_version_id,
                           "configuration_version_id")