"""

   Configuration Handler

"""
import json

from nio.util.logging import get_nio_logger
from niocore.configuration import CfgType
from nio.modules.security.access import ensure_access
from nio.modules.web import RESTHandler


class ConfigHandler(RESTHandler):

    """ Handler for config component
    """

    def __init__(self, manager):
        super().__init__('/config/')

        self._manager = manager
        self.logger = get_nio_logger("ConfigHandler")

    def on_get(self, request, response, *args, **kwargs):
        """ API endpoint for configuration component

        Example:
            http://[host]:[port]/config/refresh

        """
        # Ensure instance "execute" access
        ensure_access("instance", "execute")

        params = request.get_params()
        self.logger.debug("on_get, params: {0}".format(params))

        if request.get_identifier() != 'refresh':
             msg = "Invalid parameters: {0} in 'config': {0}".format(params)
             self.logger.warning(msg)
             raise ValueError(msg)

        cfg_type = params.get('cfg_type', CfgType.all.name)

        for current_enum in CfgType:
            if current_enum.name == cfg_type:
                self._manager.trigger_config_change_hook(current_enum)
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
        url_prefix = body.get('url', self._manager.config_api_url_prefix)
        instance_configuration_id = body.get('instance_configuration_id',
                                             self._manager.config_id)
        instance_configuration_version_id =\
            body.get('instance_configuration_version_id',
                      self._manager.config_version_id)

        if instance_configuration_id is None:
            msg = "Invalid body: Body must contain an instance_configuration_id"
            self.logger.warning(msg)
            raise ValueError(msg)
        elif instance_configuration_id != self._manager.config_id:
            # We should persist the new config id for this instance
            self._manager.config_id = instance_configuration_id

        if instance_configuration_version_id is None:
            msg = "Invalid body: " \
                  "Body must contain an instance_configuration_version_id"
            self.logger.warning(msg)
            raise ValueError(msg)
        elif instance_configuration_version_id != self._manager.config_version_id:
            # We should persist the new config version id for this instance
            self._manager.config_version_id = instance_configuration_version_id

        url = "{}/{}/versions/{}"\
            .format(url_prefix,
                    instance_configuration_id,
                    instance_configuration_version_id)

        # get configuration and update running instance
        result = self._manager.update_configuration(url)
        # provide response
        response.set_header('Content-Type', 'application/json')
        response.set_body(json.dumps(result))
