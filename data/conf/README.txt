This folder contains configuration dictionaries as JSON to use for various 
environments.
Basic Properties:
    ENVNAME - Required and cannot be empty
    LOGGING - Required and cannot be empty
        'log_level'
        'log_format'
        'root_log_file' - must be an absolute path
        'app_log_file' - must be an absolute path
    JIRA_CONFIG - Required to get to JIRA
        'jira-prefix' - to use in title when creating a new JIRA ticket

These should be copied and values replaced for the appropriate region, etc.
and placed in a standard config deploy location.
The path to that location should be passed in as an env value SAASCS_RBWS_CONF_BASE
