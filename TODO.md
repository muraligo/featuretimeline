# All TODO items

## Refactor items

1. [x] Make predecessors and successors be between task sets, not tasks.
2. [x] Change execution to be for a task set at a time and successors handled at the end of a task set.
3. [ ] Make variable _taskgraph_ a parameter to drawTaskGraph.
4. [ ] Rename init and have it take a parameter of the JSON file name to load.
5. [ ] Make tabs with actions to call the renamed init function with appropriate JSON file.
6. [ ] Complete execution for Jira.
7. [ ] Complete waits for JIRA completion.
8. [x] Merge visualization spec and execution spec.
9. [ ] Be able to use multiple thread Consumers to handle parallel processing of tasks.

## Further items

1. Make it a Flask service
2. Dockerize and deploy to DEVCORP and trigger via service API
3. Use OJET for UI
4. Complete executions for Terraform and Chef
5. Get actual data for the Terraform, Script, Chef, Jira from project teams

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

