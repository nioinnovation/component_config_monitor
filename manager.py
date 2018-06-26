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
from niocore.configuration.configuration import Configuration
from niocore.configuration import CfgType

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

        self.config_api_url_prefix = None
        self.api_key = None
        self.instance_id = None
        self._config_id = None
        self._config_version_id = None

        self._poll_job = None
        self._poll = None
        self._poll_interval = None

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
        self.logger.info('REST Manager set to {}'.format(self._rest_manager))

        # fetch component settings
        self.config_api_url_prefix = \
            Settings.get("configuration", "config_api_url_prefix",
                fallback="https://api.nio.works/v1/instance_configurations")

        default = Persistence().load("api_key", default=None)
        self.api_key = NIOEnvironment.get_variable('API_KEY', 
                                                   default=default)

        self.instance_id = Settings.get("configuration", "instance_id")

        # config autonomy spcific settings
        self._poll = Settings.getboolean("configuration", "config_polling",
                                         fallback=False)
                                         
        self._poll_interval = Settings.getint("configuration",
                                              "config_poll_interval",
                                              fallback=86400)

        self.config_id = Persistence().load("configuration_id", 
                                            default=None)
        self.config_version_id = Persistence().\
            load("configuration_version_id", default=None)

    def start(self):
        """ Starts component

        Instantiates ConfigHandler and ConfigProxy
        Begins polling job if it is set
        """
        super().start()
        self._api_proxy = ConfigProxy()
        self._config_handler = ConfigHandler(self)
        self._rest_manager.add_web_handler(self._config_handler)
    
        if self._poll:
            self._poll_job = Job(self._run_config_update,
                                 timedelta(seconds=self._poll_interval),
                                 True)

    def stop(self):
        """ Stops component
        """
        self._rest_manager.remove_web_handler(self._config_handler)
        
        if self._poll:
            self._poll_job.cancel()
        
        super().stop()

    def _run_config_update(self):
        # Callback function to run update at the end of each polling interval

        # TODO: In NIO-1142, this should first get the newest config version 
        # from the product api before triggering an update
        url = "{}/{}/versions/{}".format(self.config_api_url_prefix,
                                         self.config_id,
                                         self.config_version_id)
        self.update_configuration(url)
        self.trigger_config_change_hook(CfgType.all.name)

    def update_configuration(self, url):
        configuration = Configuration(CfgType.all.name,
                                      fetch_on_create=False,
                                      is_collection=True,
                                      substitute=False)
        # erase any existing data under this configuration
        configuration.clear()
        # load new config data and save
        configuration.data = \
            self._api_proxy.load_configuration(url, self.api_key) or {}
        configuration.save()

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