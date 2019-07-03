# nio deployment API component

A nio component providing functionality to update and/or refresh instance configuration files


## Configuration

```
[configuration]
# url to use when requesting a configuration from the Product API
#config_api_url_prefix=

# for indirect deployments provide a polling interval
#config_poll_interval=3600

# check for indirect deployments immediately when started. If False (default)
# polling begin after a configured config_poll_interval
#config_poll_on_start=False

# specifies if modified services are to be started/stopped based on the
# auto_start flag
#start_stop_services=True

# specifies if existing blocks and services are to be deleted when not found
# in the incoming configuration
#delete_missing=True
```

## Logging

Add the following loggers to a project's `etc/logging.json` to set the log level of the component:
```
  ...,
  "loggers": {
    "main": {
      "level": "NOTSET"
    },
    ...,
    "main.DeploymentManager": {
      "level": "DEBUG"
    },
    "main.DeploymentHandler": {
      "level": "DEBUG"
    }
  }
```

## Dependencies

- None
