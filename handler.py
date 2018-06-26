"""

   Configuration Handler

"""
import json

from nio.util.logging import get_nio_logger
from niocore.configuration import CfgType
from nio.modules.security.access import ensure_access
from niocore.core.hooks import CoreHooks
from nio.modules.web import RESTHandler
from .proxy import ConfigurationProxy


class ConfigHandler(RESTHandler):

    """ Handler for config component
    """

    def __init__(self, product_api_url_prefix, instance_api_key, instance_id,
                 configuration_manager, start_stop_services, delete_missing):
        super().__init__('/config/')

        self.logger = get_nio_logger("ConfigHandler")
        self._product_api_url_prefix = product_api_url_prefix
        self._instance_api_key = instance_api_key
        self._instance_id = instance_id
        self._configuration_manager = configuration_manager
        self._start_stop_services = start_stop_services
        self._delete_missing = delete_missing
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
        self.logger.debug("on_put, params: {}".format(params))

        if request.get_identifier() != 'update':
             msg = "Invalid parameters: {0} in 'config': {0}".format(params)
             self.logger.warning(msg)
             raise ValueError(msg)

        body = request.get_body()
        self.logger.debug("on_put, body: {}".format(body))

        # allow to override gathered settings
        url_prefix = body.get('url', self._product_api_url_prefix)
        instance_configuration_id = body.get('instance_configuration_id', None)
        instance_configuration_version_id =\
            body.get('instance_configuration_version_id', None)

        if instance_configuration_id is None:
            msg = "Invalid body: Body must contain an instance_configuration_id"
            self.logger.warning(msg)
            raise ValueError(msg)

        elif instance_configuration_version_id is None:
            msg = "Invalid body: " \
                  "Body must contain an instance_configuration_version_id"
            self.logger.warning(msg)
            raise ValueError(msg)

        url = "{}/instance_configurations/{}/versions/{}"\
            .format(url_prefix,
                    instance_configuration_id,
                    instance_configuration_version_id)

        # get configuration and update running instance
        result = self._update_configuration( url, self._instance_api_key)
        # provide response
        response.set_header('Content-Type', 'application/json')
        response.set_body(json.dumps(result))

    def _update_configuration(self, url, apikey):

        configuration = self._proxy.load_configuration(url, apikey) or {}
        if "configuration_data" not in configuration:
            msg = "configuration_data entry missing in nio API return"
            self.logger.error(msg)
            raise RuntimeError(msg)

        configuration_data = configuration["configuration_data"]
        services = configuration_data.get("services", {})
        blocks = configuration_data.get("blocks", {})
        return self._configuration_manager.update(
            services, blocks, self._start_stop_services, self._delete_missing)

    def _trigger_config_change_hook(self, cfg_type):
        """ Executes hook indicating configuration changes
        """
        self.logger.debug("Triggering configuration change hook")
        CoreHooks.run('configuration_change', cfg_type)
