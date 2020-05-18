# Feature Release Process

This service builds a task list to build and deploy a feature. It is more like a graph with dependencies.

It also builds a task list to deploy all services into a new region.

It allows for the visualization of the task graphs along with timelines.

## Task Graph Entities

### Task Set

An ordered list of tasks.

Following are the properties of a Task Set:

- name Unique descriptive summary of the purpose of the task set
- area The organizational area that is responsible
    1. "build" a regular task set; responsibility of the service owning team
    2. "architecture" controls task set
    3. "security" controls task set
    4. "compliance" task set
- stage is an enumerated type. See below for values
- tasks is an ordered list of tasks in this set
- predecessors list of task sets this task set depends on
- successors (derived) list of task sets that are dependent on this task set. Primarily to trigger waiting task sets



### Task

A task represents the definition of what can be executed.

Following are the properties of a task:

- name Unique name of the task
- task_type Type of task
    1. "perform" a manual task
    2. "check" status of specified actions
    3. "configure" a service
    4. "link" 2 services or a service externally
- executor an executor configuration. one of
    1. "manual" with a "jiraspec"  referencing a JIRA issue (see below for attributes)
    2. "shell" with a "scriptspec" referencing a shell script (see below for attributes)
    3. "terraform" with a "terraformspec" referencing a tf definition (see below for attributes)
    4. "chef" with a "chefspec" referencing a chef recipe (see below for attributes)
    5. "check" with a "check spec" with a set of check actions each referencing how to check (see below for attributes)
- specification to go with the executor
- team is the name of the team assigned to the task
- description brief, to describe what the task does
- onfailure action to be taken if the task fails. See below for values
- note (Optional) note describing the task some more



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

### shell scriptspec

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

### location

Comprises of a type and a location specification. The location specification depends on the type. Currently supported types are:

- file referring to a file on the local file system where the choreographer is running
- object referring to an object store service, the bucket, and the object

## Capabilities

1. Graph has Task Sets that have an ordered list of tasks
2. Only predecessors need to be specified; graph is derived from that.
3. Links are only between Task Sets
4. Tasks with specification or script files have a *Location* specification as defined above
5. Microsoft Projects exported to MS Excel and with some additional fields can also be taken as specifications
