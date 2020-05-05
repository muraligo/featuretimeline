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
