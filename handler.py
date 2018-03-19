"""

   Configuration Handler

"""
from nio.util.logging import get_nio_logger
from niocore.configuration import CfgType
from nio.modules.security.access import ensure_access
from niocore.configuration.service import ServiceConfiguration
from niocore.configuration.block import BlockConfiguration
from niocore.core.hooks import CoreHooks
from nio.modules.web import RESTHandler
from .proxy import ConfigurationProxy


class ConfigHandler(RESTHandler):

    """ Handler for config component
    """

    def __init__(self, product_api_url_prefix, instance_id):
        super().__init__('/config/')

        self.logger = get_nio_logger("ConfigHandler")
        self._product_api_url_prefix = product_api_url_prefix
        self._instance_id = instance_id
        self._proxy = ConfigurationProxy()

    def on_get(self, request, response, *args, **kwargs):
        """ API endpoint for configuration component

        Example:
            http://[host]:[port]/config/refresh
            http://[host]:[port]/config/update

        """
        # Ensure instance "execute" access
        ensure_access("instance", "execute")

        params = request.get_params()
        self.logger.debug("on_get, params: {0}".format(params))

        if params.get('identifier', '') == 'refresh':
            cfg_type = params.get('cfg_type', CfgType.all.name)

            for current_enum in CfgType:
                if current_enum.name == cfg_type:
                    self._trigger_config_change_hook(current_enum)
                    return
            msg = "Invalid 'config' refresh type: {0}".format(cfg_type)
            self.logger.warning(msg)
            raise ValueError(msg)
        elif params.get('identifier', '') == 'update':

            token = params.get('token', None)
            # allow to override gathered settings
            url_prefix = params.get('url', self._product_api_url_prefix)
            instance_id = params.get('instance_id', self._instance_id)

            url = "{}/instances/{}/config".format(url_prefix, instance_id)

            # update configurations
            self._update_configuration(
                "blocks", BlockConfiguration, url, token
            )
            self._trigger_config_change_hook(CfgType.block)

            self._update_configuration(
                "services", ServiceConfiguration, url, token
            )
            self._trigger_config_change_hook(CfgType.service)

            return

        msg = "Invalid parameters: {0} in 'config': {0}".format(params)
        self.logger.warning(msg)
        raise ValueError(msg)

    def _update_configuration(self, name, conf_class, url, token):
        configuration = conf_class(name,
                                   fetch_on_create=False,
                                   is_collection=True,
                                   substitute=False)
        # erase any existing data under this configuration
        configuration.clear()

        # load new config data and save
        configuration.data = \
            self._proxy.load_collection(name, url, token) or {}
        configuration.save()

    def _trigger_config_change_hook(self, cfg_type):
        """ Executes hook indicating configuration changes
        """
        self.logger.debug("Triggering configuration change hook")
        CoreHooks.run('configuration_change', cfg_type)
