"""

   Configuration Manager

"""
from nio.util.versioning.dependency import DependsOn
from nio import discoverable
from nio.modules.settings import Settings

from nio.modules.persistence import Persistence
from niocore.util.environment import NIOEnvironment

from niocore.core.component import CoreComponent

from .handler import ConfigHandler

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

        self._product_api_url_prefix = None
        self._instance_api_key = None
        self._instance_id = None

        self._configuration_manager = None
        self._start_stop_services = None
        self._delete_missing = None

    def configure(self, context):
        """ Configures component

        Establish dependency to RESTManager
        Fetches settings and instantiates ConfigHandler

        Args:
            context (CoreContext): component initialization context

        """

        super().configure(context)

        # Register dependency to rest manager
        self._rest_manager = self.get_dependency('RESTManager')
        self._configuration_manager = \
            self.get_dependency('ConfigurationManager')
        self.logger.info('REST Manager set to {}'.format(self._rest_manager))

        # fetch component settings
        self._product_api_url_prefix = \
            Settings.get("configuration", "product_api_url_prefix",
                         fallback="https://api.nio.works/v1")

        default = Persistence().load("api_key", default=None)
        self._instance_api_key = \
            NIOEnvironment.get_variable('API_KEY', default=default)

        self._instance_id = Settings.get("configuration", "instance_id")
       
        self._start_stop_services = Settings.getboolean(
            "configuration", "start_stop_services", fallback=True)
        self._delete_missing = Settings.getboolean(
            "configuration", "delete_missing", fallback=False)

        # TODO in NIO-1141: Pull config settings for autonomy

    def start(self):
        """ Starts component

        Register a REST handler that handles configuration updates
        """
        super().start()
        self._config_handler = ConfigHandler(self._product_api_url_prefix,
                                             self._instance_api_key,
                                             self._instance_id,
                                             self._configuration_manager,
                                             self._start_stop_services,
                                             self._delete_missing)

        self._rest_manager.add_web_handler(self._config_handler)

    def stop(self):
        """ Stops component
        """
        self._rest_manager.remove_web_handler(self._config_handler)
        
        # TODO in NIO-1141: Persist instance config id, instance config version id
        
        super().stop()