## Entities

### Task

A task represents the definition of what can be executed.

Following are the properties of a task:
- name Unique name of the task
- task_type Type of task
    1. "perform" a manual task
    2. "install" a service
    3. "configure" a service
    4. "link" 2 services or a service externally
- order a number indicating the order within the stage
- executor an executor configuration. one of
    1. "terraform" with a "terraformspec" referencing a tf definition (see below for attributes)
    2. "chef" with a "chefspec" referencing a chef recipe (see below for attributes)
    3. "shell" with a "scriptspec" referencing a shell script (see below for attributes)
    4. "jira" with a "jiraspec"  referencing a JIRA issue (see below for attributes)
- note (Optional) note describing the task some more

In addition one of the two should be provided
- service is the unique name of a service defined in a services definition. Attributes are shown below. If specified, its attributes are used instead of equivalent ones in the task.
- stage is an enumerated type. See below for values

### Service

A service represents the definition of a service that runs in the target environment and therefore needs to be deployed.

Services are named with spaces between name segments, each of which represents 
the name of a Service Group in a hierarchy. On loading, services are grouped 
in the hierarchy.

Following are the properties of a service:
- name the unique name of a service (see above for its structure)
- stage is an enumerated type. See below for values
- install_executor (Optional) the type of executor configuration to install the service
- configure_executor (Optional) the type of executor configuration to configure the service
- link_executor (Optional) the type of executor configuration to link the service to something else
- parent_service Internally used for the group hierarchy chain
- children list of children for the service group. only valid if this is a service group

### Stage

The stage at which a task is defined to be executed.
Following are the values in order of execution.

1. foundation
2. primordial
3. core
4. higher

### terraformspec

A dict with attributes to reference and characterize a .tf definition

Following are the properties of a terraformspec:
- location of the .tf definition

### chefspec

A dict with attributes to reference and characterize a chef recipe

Following are the properties of a chefspec:
- location of the chef recipe

### shell

A dict with attributes to reference and characterize a shell script

Following are the properties of a scriptspec:
- location of the shell script

### jiraspec

A dict with attributes to reference and characterize a JIRA issue.
It is assumed that the JIRA issue is located in the GBUJIRA instance.

Following are the properties of a jiraspec:
- project the issue needs to be created in
- issuetype which is one of the types of JIRA issues of EPIC, STORY, SUBTASK
- components is a list of components (should be valid in the project)
- labels to better classifiy and identify the task
- parent task (that should exist) that this task should be created under
    1. issuetype of the parent task
    2. issueid of the parent task
