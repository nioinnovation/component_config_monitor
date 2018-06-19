"""

   Configuration Handler

"""
from nio.util.logging import get_nio_logger
from niocore.configuration import CfgType
from nio.modules.security.access import ensure_access
from niocore.configuration.configuration import Configuration
from niocore.core.hooks import CoreHooks
from nio.modules.web import RESTHandler
from .proxy import ConfigurationProxy


class ConfigHandler(RESTHandler):

    """ Handler for config component
    """

    def __init__(self, product_api_url_prefix, instance_api_key, instance_id):
        super().__init__('/config/')

        self.logger = get_nio_logger("ConfigHandler")
        self._product_api_url_prefix = product_api_url_prefix
        self._instance_api_key = instance_api_key
        self._instance_id = instance_id
        self._proxy = ConfigurationProxy()

    def on_get(self, request, response, *args, **kwargs):
        """ API endpoint for configuration component

        Example:
            http://[host]:[port]/config/refresh

        """
        # Ensure instance "execute" access
        ensure_access("instance", "execute")

        params = request.get_params()
        self.logger.debug("on_get, params: {0}".format(params))

        if params.get('identifier', '') != 'refresh':
             msg = "Invalid parameters: {0} in 'config': {0}".format(params)
             self.logger.warning(msg)
             raise ValueError(msg)

        cfg_type = params.get('cfg_type', CfgType.all.name)

        for current_enum in CfgType:
            if current_enum.name == cfg_type:
                self._trigger_config_change_hook(current_enum)
                return
        msg = "Invalid 'config' refresh type: {0}".format(cfg_type)
        self.logger.warning(msg)
        raise ValueError(msg) 

    def on_put(self, request, response, *args, **kwargs):
        """ API endpoint for configuration component

        Example:
            http://[host]:[port]/config/update

        """
         # Ensure instance "execute" access
        ensure_access("instance", "execute")

        params = request.get_params()
        self.logger.debug("on_put, params: {0}".format(params))

        if params.get('identifier', '') != 'update':
             msg = "Invalid parameters: {0} in 'config': {0}".format(params)
             self.logger.warning(msg)
             raise ValueError(msg)

        token = params.get('token', self._instance_api_key)

        # allow to override gathered settings
        url_prefix = params.get('url', self._product_api_url_prefix)
        instance_configuration_id = params.get('instance_configuration_id', None)
        instance_configuration_version_id =\
            params.get('instance_configuration_version_id', None)

        org_id = params.get('nio-organization', None)

        url = "{}/instance_configurations/{}/versions/{}"\
            .format(url_prefix,
                    instance_configuration_id,
                    instance_configuration_version_id)


        # get and update configuration
        self._update_configuration(all, Configuration, url, token, org_id)
        self._trigger_config_change_hook(CfgType.all)

        return

    def _update_configuration(self, name, conf_class, url, token, org_id):
        configuration = conf_class(name,
                                   fetch_on_create=False,
                                   is_collection=True,
                                   substitute=False)
        # erase any existing data under this configuration
        configuration.clear()

        # load new config data and save
        configuration.data = \
            self._proxy.load_configuration(url, token, org_id) or {}
        configuration.save()

    def _trigger_config_change_hook(self, cfg_type):
        """ Executes hook indicating configuration changes
        """
        self.logger.debug("Triggering configuration change hook")
        CoreHooks.run('configuration_change', cfg_type)
