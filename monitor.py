"""

   Configuration Monitor

"""
from nio.util.versioning.dependency import DependsOn
from niocore.configuration import CfgType
from nio.modules.security.decorator import protected_access
from niocore.core.component import CoreComponent
from niocore.core.hooks import CoreHooks
from nio.modules.web import RESTHandler
from nio import discoverable


class ConfigMonitorHandler(RESTHandler):

    """ Handler for config/refresh method

     Executes a callback passed when a HTTP request is done
    """

    def __init__(self, callback, logger):
        super().__init__('/config/')
        self._callback = callback
        self.logger = logger

    @protected_access("config.refresh")
    def on_get(self, request, response, *args, **kwargs):
        """ API endpoint to refresh current configuration

        Example:
            http://[host]:[port]/config/refresh

        """
        params = request.get_params()
        self.logger.debug("on_get, params: {0}".format(params))

        if params.get('identifier', '') == 'refresh':
            cfg_type = params.get('cfg_type', CfgType.all.name)

            for current_enum in CfgType:
                if current_enum.name == cfg_type:
                    self._callback(current_enum)
                    return
            msg = "Invalid 'config' refresh type: {0}".format(cfg_type)
            self.logger.warning(msg)
            raise ValueError(msg)

        msg = "Invalid parameters: {0} in 'config': {0}".format(params)
        self.logger.warning(msg)
        raise ValueError(msg)


@DependsOn('niocore.components.rest')
@discoverable
class ConfigMonitor(CoreComponent):

    """ Monitors configuration files

    Register a handler with REST component and run configuration changes
    hooks when a request is made

    """

    _name = "ConfigMonitor"

    def __init__(self):
        super().__init__()
        self._rest_manager = None

    def _trigger_hooks(self, cfg_type):
        """ Executes hook indicating configuration changes
        """
        self.logger.debug("Triggering configuration changes hooks")
        # Allow all components to handle configuration has changed
        CoreHooks.run('configuration_change', cfg_type)

    def start(self):
        """ Starts Configuration Monitor

        Register a REST handler that triggers the system hooks indicating
        configuration changes
        """
        super().start()

        # Create handler and register with REST component
        self._rest_manager = self.get_dependency('RESTManager')
        self.logger.info('REST Manager set to %s' % self._rest_manager)

        # Register with REST Manager if found
        self._rest_manager.add_web_handler(
            ConfigMonitorHandler(self._trigger_hooks, self.logger))
