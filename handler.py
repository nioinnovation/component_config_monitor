"""

   Deployment API Handler

"""
import json

from nio.util.logging import get_nio_logger
from nio.modules.security.access import ensure_access
from nio.modules.web import RESTHandler


class DeploymentHandler(RESTHandler):

    """ Handler for issuing direct deployments to an instance """

    def __init__(self, manager):
        super().__init__('/config/')

        self._manager = manager
        self.logger = get_nio_logger("DeploymentManager")

    def on_get(self, request, response, *args, **kwargs):
        raise NotImplementedError

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

        instance_configuration_id = body.get('instance_configuration_id')
        instance_configuration_version_id = body.get(
            'instance_configuration_version_id')
        deployment_id = body.get('deployment_id')

        if not (instance_configuration_id and
                instance_configuration_version_id and
                deployment_id):
            msg = ("Invalid body: configuration ID, version ID, and deployment"
                   " ID are all required")
            self.logger.error(msg)
            raise ValueError(msg)

        # get configuration and update running instance
        result = self._manager.update_configuration(
            instance_configuration_id,
            instance_configuration_version_id,
            deployment_id,
        )

        # provide response
        response.set_header('Content-Type', 'application/json')
        response.set_body(json.dumps(result))
