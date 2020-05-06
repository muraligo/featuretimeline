# All TODO items

## Refactor items

1. Redo task plan definition and exec configs to refer to a Location object config. **DONE**
2. Create Location classes for various types and instantiate on loading tasks **DONE**
3. During execution use information from Location instance to locate or download and execute the script for script types **DONE**
4. Convert to predecessor successor graph instead of predefined priorities **DONE**
5. Convert to producer consumer execution to ensure wait for dependencies **DONE**
6. Be able to use multiple thread Consumers to handle parallel processing of tasks
7. Convert all prints to logging **DONE**

## Further items

1. Make it a Flask service
2. Dockerize and deploy to DEVCORP and trigger via service API
3. Generate input definitions from CSV export of Microsoft Project file from Kevin
4. Complete executions for Terraform, Chef, and Jira
5. Complete executions for Jira with waits for JIRA completion
6. Get actual data for the Terraform, Script, Chef, Jira from project teams

### Location

type is file or object or ocir
target is a path to where it is in reference to a base for that type

## Differences between Timeline and Choreo

| Feature Timeline                              | Choreo                                        |
| :-------------------------------------------- | :-------------------------------------------- |
|                                               |                                               |
| TaskSet                                       | TaskSet *NEED TO HAVE*                        |
| - name (direct from JSON)                     | - name (direct from JSON)                     |
| - kind (direct from JSON)                     |                                               |
| 		{build,architecture,security,compliance}  |                                               |
| *NICE TO HAVE*                                | - stage {foundation,primordial,core,higher} (direct from JSON) |
| - tasks = [] (built from JSON)                | *NEED TO HAVE*                                |
| *NICE TO HAVE*                                | - team (direct from JSON)                     |
| - predecessors = [] (built from JSON)         | - predecessors = [] (built from JSON)         |
| *NICE TO HAVE*                                | - successors = [] (set on build)              |
| - timeline_text (direct from JSON)            |                                               |
| - myrow (direct from JSON)                    |                                               |
| - start_x (set on build)                      |                                               |
| - start_y (derived)                           |                                               |
| - arrow_y (derived)                           |                                               |
| - timeline_y (derived)                        |                                               |
| - maxtxtlen (derived)                         |                                               |
| - end_x (set on build)                        |                                               |
| - end_y (set on build)                        |                                               |
|                                               |                                               |
| Task                                          | Task                                          |
| - name (direct from JSON)                     | - name (direct from JSON)                     |
| - txtlines = [] (direct from JSON)            | *NEED TO CHANGE*                              |
| *NEED TO HAVE*                                | - type {perform,check,configure,link} (direct from JSON) |
| *NEED TO HAVE*                                | - executor (built from exec_type in JSON {manual,shell,terraform,chef,check} and specification) |
| *NEED TO HAVE*                                | - specification (direct from JSON; based on executor) |
| *NICE TO HAVE*                                | - onfailure (direct from JSON)                |
| *NEED TO HAVE*                                | - note (Optional) (direct from JSON)          |
| - start_x (set on build)                      |                                               |
| - start_y (derived)                           |                                               |
| - maxwidth (derived)                          |                                               |
| - height (derived)                            |                                               |
| *NICE TO HAVE*                                | - successors (set on build)                   |
| *NEED TO HAVE*                                | - status (set on exec)                        |

