"""

   Configuration Manager

"""
from nio.util.versioning.dependency import DependsOn
from nio import discoverable
from nio.modules.settings import Settings

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
        self.logger.info('REST Manager set to {}'.format(self._rest_manager))

        # fetch component settings
        product_api_url_prefix = \
            Settings.get("configuration", "product_api_url_prefix",
                         fallback="https://api.nio.works/v1")
        instance_id = Settings.get("configuration", "instance_id")

        self._config_handler = ConfigHandler(product_api_url_prefix,
                                             instance_id)

    def start(self):
        """ Starts component

        Register a REST handler that handles configuration updates
        """
        super().start()
        self._rest_manager.add_web_handler(self._config_handler)
