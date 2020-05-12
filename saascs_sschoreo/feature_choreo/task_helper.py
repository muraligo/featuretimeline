#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 09 15:44:40 2020

@author: mugopala

Helper functions for tasks
"""

import os
import stat
import json
import threading
import time
import queue as stdq
import csv
from io import StringIO
from .helpers import file_reader
from . import task_consts, common_entities
from fabric2.tasks import task
from fabric2 import Connection


global _unqid
_unqid = int(1)

global _FILEPERMS
_FILEPERMS = int(0)
_FILEPERMS = stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH | stat.S_IXGRP | stat.S_IXOTH


@task
def perform_jira(conn, lggr, tskspec):
    lggr.debug("    %s" % tskspec)

@task
def perform_shell(conn, lggr, tskspec):
    global _unqid
    global _FILEPERMS
    result = None
    lggr.debug("    %s" % tskspec)
    if tskspec.locatespec['type'] == 'NONE':
        pass
    else:
        tskspec.location.read_content()
        lggr.debug("    %s" % tskspec.location.textdata)
        scrptspath = "/Users/mugopala/tmp/script%d.sh" % _unqid
        _unqid = _unqid + 1
        with open(scrptspath, 'w') as scrptf:
            scrptf.write(tskspec.location.textdata)
            scrptf.close()
        # make this file executable
        os.chmod(scrptspath, _FILEPERMS)

        result = conn.run(scrptspath)
        if result.failed:
            raise common_entities.M3GeneralChoreographyException('Execution of task {} failed with {}'.format(tskspec.location, result.stderr))
        else:
            return result.stdout

@task
def perform_chef(conn, lggr, tskspec):
    lggr.debug("    %s" % tskspec)

@task
def perform_terraform(conn, lggr, tskspec):
    lggr.debug("    %s" % tskspec)


class M3TaskPerformer(threading.Thread):

    def __init__(self, task_queue, result_queue, lggr, appconfig):
        super(M3TaskPerformer, self).__init__()
        if appconfig['ENVNAME'] == 'local':
            self.host = 'mugopala@localhost'
        else:
            self.host = None
        self.logger = lggr
        self.conn = Connection(self.host)
        # TODO implement any other environment initialization
        self.task_queue = task_queue
        self.result_queue = result_queue

    def run(self):
        proc_name = self.name
        while True:
            taskval = self.task_queue.get()
            if taskval is None:
                # Poison pill means shutdown
                self.logger.debug('{}: Exiting'.format(proc_name))
                # ensure producer also ends
                self.result_queue.put(None)
                self.task_queue.task_done()
                break
            self.logger.debug('{}: Performing {}'.format(proc_name, taskval))
            # TODO make task something that is executable by including a __call__ method in there
#             answer = next_task()
            # for now execute in traditional way
            if taskval.executor == task_consts.M3TaskExecutor.MANUAL:
                perform_jira(self.conn, self.logger, taskval.specification)
            if taskval.executor == task_consts.M3TaskExecutor.SHELL:
                perform_shell(self.conn, self.logger, taskval.specification)
            if taskval.executor == task_consts.M3TaskExecutor.CHEF:
                perform_chef(self.conn, self.logger, taskval.specification)
            if taskval.executor == task_consts.M3TaskExecutor.TERRAFORM:
                perform_terraform(self.conn, self.logger, taskval.specification)
            self.task_queue.task_done()
            # if it gets here without an exception that means it is successful
            self.result_queue.put(taskval)


class M3TaskStateManager(threading.Thread):

    def __init__(self, task_queue, result_queue, lggr, tskstage, firsttask, appconfig):
        super(M3TaskStateManager, self).__init__()
        # TODO implement any environment initialization
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.stage = tskstage
        self.tasksinstage = {}
        self.logger = lggr
        q = stdq.SimpleQueue()
        q.put(firsttask)
        while (not q.empty):
            taskval = q.get()
            taskval.state = task_consts.M3TaskState.READY
            self.tasksinstage[taskval.name] = taskval
            for tskinst in taskval.successors:
                q.put(tskinst)
        print("%s initialized" % self.getName())

    def run(self):
        proc_name = self.name
        while True:
            taskval = self.result_queue.get()
            if taskval is None:
                # Poison pill means shutdown
                self.logger.debug('{}: Exiting'.format(proc_name))
                break
            self.logger.debug('{}: Completing {}'.format(proc_name, taskval))
            taskval.state = task_consts.M3TaskState.DONE
            _alldone = True
            if len(taskval.successors) <= 0:
                for tsknm in self.tasksinstage:
                    if self.tasksinstage[tsknm].state == task_consts.M3TaskState.DONE:
                        continue
                    else:
                        _alldone = False
                        break
                if _alldone == True:
                    # inject poison pill
                    self.task_queue.put(None)
                continue
            for tskinst in taskval.successors:
                _tskready = True
                if len(tskinst.predecessors) > 0:
                    for tskpred in tskinst.predecessors:
                        if tskpred.state == task_consts.M3TaskState.DONE:
                            continue
                        _tskready = False
                        break
                if _tskready == True:
                    tskinst.state = task_consts.M3TaskState.RUNNING
                    self.task_queue.put(tskinst)



def cs_load_tasks(lggr, myapihandler, config, filename='tasks2.json', basepath=None):
    _fullpath = './input/{}'.format(filename) if basepath is None else '{}/input/{}'.format(basepath, filename)
    lggr.debug(_fullpath)
    jshash = json.loads(file_reader(_fullpath))
    if jshash and 'tasks' in jshash and len(jshash['tasks']) > 0:
        stages = { task_consts.M3TaskStage.FOUNDATION:None, 
                    task_consts.M3TaskStage.PRIMORDIAL:None,
                    task_consts.M3TaskStage.CORE:None,
                    task_consts.M3TaskStage.HIGHER:None
                }
        _alltasks = {}
        for tskdict in jshash['tasks']:
            tsknote = tskdict['note'] if 'note' in tskdict else None
            tskname = None
            tskexec = None
            tsktype = None
            tskexekey = None
            tskstage = None
            tskteam = None
            tskfailure = None
            if 'type' not in tskdict:
                raise common_entities.M3GeneralChoreographyException('Missing vital property in task specification')
            else:
                tsktype = task_consts.M3TaskType.from_name(tskdict['type'])
            if 'stage' not in tskdict:
                raise common_entities.M3GeneralChoreographyException('Missing vital property in task specification')
            else:
                tskstage = task_consts.M3TaskStage.from_name(tskdict['stage'])
            if 'team' not in tskdict:
                raise common_entities.M3GeneralChoreographyException('Missing vital property in task specification')
            else:
                tskteam = tskdict['team']
            if 'name' not in tskdict:
                raise common_entities.M3GeneralChoreographyException('Missing vital property in task specification')
            else:
                tskname = tskdict['name']
            if 'failure' in tskdict:
                tskfailure = task_consts.M3TaskExecutor.from_name(tskdict['failure'])
            else:
                tskfailure = task_consts.M3TaskExecutor.MANUAL
            if tsktype == task_consts.M3TaskType.CHECK:
                tskexec = task_consts.M3TaskExecutor.CHECK
            else:
                if 'mode' not in tskdict:
                    raise common_entities.M3GeneralChoreographyException('Missing vital property in task specification')
                else:
                    tskexec = task_consts.M3TaskExecutor.from_name(tskdict['mode'])
            tskexekey = tskexec.section_name
            taskval = None
            if tsknote is None:
                taskval = task_consts.M3FlatTask(tskname, tsktype, tskexec, tskexekey, 
                                tskteam, tskfailure, tskdict[tskexekey])
            else:
                taskval = task_consts.M3FlatTask(tskname, tsktype, tskexec, tskexekey, 
                                tskteam, tskfailure, tskdict[tskexekey], tsknote)
            if tskexekey == 'scriptspec':
                taskval.specification.resolve_location(myapihandler, config)
            if stages[tskstage] is None:
                stages[tskstage] = taskval
            _prival = 0
            if len(tskdict['predecessor']) > 0:
                for tskpred in tskdict['predecessor']:
                    taskval.predecessors.append(_alltasks[tskpred])
                    _alltasks[tskpred].successors.append(taskval)
                    if _alltasks[tskpred].priority > _prival:
                        _prival = _alltasks[tskpred].priority
            _prival = _prival + 1
            taskval.priority = _prival
            _alltasks[tskname] = taskval
        return stages
    else:
        raise common_entities.M3ReferenceDataException('Tasks', 'Empty')


def cs_parse_json_task(lggr, myapihandler, config, tskdict):
    tsknote = tskdict['note'] if 'note' in tskdict else None
    tskgrpstr = None
    tskname = None
    tsktext = None
    tskexec = None
    tsktype = None
    tskexekey = None
    tskstage = None
    tskteam = None
    tskfailure = None
    tskarea = None
    if 'type' not in tskdict:
        raise common_entities.M3GeneralChoreographyException('Missing vital property in task specification')
    else:
        tsktype = task_consts.M3TaskType.from_name(tskdict['type'])
    if 'stage' not in tskdict:
        raise common_entities.M3GeneralChoreographyException('Missing vital property in task specification')
    else:
        tskstage = task_consts.M3TaskStage.from_name(tskdict['stage'])
    if 'team' not in tskdict:
        raise common_entities.M3GeneralChoreographyException('Missing vital property in task specification')
    else:
        tskteam = tskdict['team']
    if 'name' not in tskdict:
        raise common_entities.M3GeneralChoreographyException('Missing vital property in task specification')
    else:
        tskname = tskdict['name']
    if 'group' not in tskdict:
        raise common_entities.M3GeneralChoreographyException('Missing vital property in task specification')
    else:
        tskgrpstr = tskdict['group']
    if 'description' not in tskdict:
        raise common_entities.M3GeneralChoreographyException('Missing vital property in task specification')
    else:
        tsktext = tskdict['description']
    if 'failure' in tskdict:
        tskfailure = task_consts.M3TaskExecutor.from_name(tskdict['failure'])
    else:
        tskfailure = task_consts.M3TaskExecutor.MANUAL
    if tsktype == task_consts.M3TaskType.CHECK:
        tskexec = task_consts.M3TaskExecutor.CHECK
    else:
        if 'mode' not in tskdict:
            raise common_entities.M3GeneralChoreographyException('Missing vital property in task specification')
        else:
            tskexec = task_consts.M3TaskExecutor.from_name(tskdict['mode'])
    tskexekey = tskexec.section_name
    if 'area' in tskdict:
        tskarea = task_consts.M3TaskArea.from_name(tskdict['area'])
    taskval = None
    if tsknote is None:
        taskval = task_consts.M3Task(tskname, tsktype, tskexec, tskexekey, 
                                tskteam, tskfailure, tskdict[tskexekey])
    else:
        taskval = task_consts.M3Task(tskname, tsktype, tskexec, tskexekey, 
                                tskteam, tskfailure, tskdict[tskexekey], tsknote)
    if tskexekey == 'scriptspec':
        taskval.specification.resolve_location(myapihandler, config)
    return (tskgrpstr, tskstage, tskarea, tskteam, taskval)


def create_task_group(tskstage, lggr, tskdict):
    tskarea = None
    tskteam = None
    _tskgrpstr = tskdict['Task Name'].strip()
    if 'Team' not in tskdict:
        raise common_entities.M3GeneralChoreographyException('Missing vital property in task specification')
    else:
        tskteam = tskdict['Team']
        if tskteam.isspace():
            tskteam = None
    if tskteam is None:
        raise common_entities.M3GeneralChoreographyException('Missing vital property in task specification')
    _tskarestr = None
    if 'Area' in tskdict:
        _tskarestr = tskdict['Area']
        if _tskarestr.isspace():
            _tskarestr = None
    if _tskarestr is None:
        tskarea = task_consts.M3TaskArea.BUILD
    else:
        tskarea = task_consts.M3TaskArea.from_name(_tskarestr.strip())
    return task_consts.M3TaskSet(_tskgrpstr, tskarea, tskstage, tskteam)


"""
Fields in export of MPP into Excel
- ID
- Project (Env - Region)
- Task Name (Task outline Level is 3, outline level of 4 are steps within a Check Spec, 
		outline level 2 is a TaskSet, outline level 1 is a stage if followed by other outlines,
		otherwise generate a name from ID and use the name as the text)
- Duration (For timelines; 0 duration tasks are markers NEED TO IMPLEMENT CONCEPT)
- Predecessors (outside group or phase should be changed to the whole group, inside could be to omitted as it is in sequence)
- Outline Level
Add
- type
- mode (any level 3 task with level 4 is of mode CHECK and so can be left blank)
- team (only for outline level 2)
- failure
- area (only for outline level 2)
"""
def cs_parse_csv_task(lggr, myapihandler, config, tskdict):
    tsknote = tskdict['note'] if 'note' in tskdict else None
    tskname = None
    tsktext = None
    tskexec = None
    tsktype = None
    tskexekey = None
    tskfailure = None
    tsktimeline = None
    tskid = -1
    tskoutline = -1
    if 'type' not in tskdict:
        raise common_entities.M3GeneralChoreographyException('Missing vital property in task specification')
    else:
        tsktype = task_consts.M3TaskType.from_name(tskdict['type'])
    if 'Task Name' not in tskdict:
        raise common_entities.M3GeneralChoreographyException('Missing vital property in task specification')
    else:
        tskname = tskdict['Task Name'] # TODO need to generate Name from ID
        tsktext = tskdict['Task Name']
    if 'failure' in tskdict:
        tskfailure = task_consts.M3TaskExecutor.from_name(tskdict['failure'])
    else:
        tskfailure = task_consts.M3TaskExecutor.MANUAL
    if tsktype == task_consts.M3TaskType.CHECK:
        tskexec = task_consts.M3TaskExecutor.CHECK
    else:
        if 'mode' not in tskdict:
            raise common_entities.M3GeneralChoreographyException('Missing vital property in task specification')
        else:
            tskexec = task_consts.M3TaskExecutor.from_name(tskdict['mode'])
    tskexekey = tskexec.section_name
    tskid = tskdict['ID']
    tskoutline = tskdict['Outline Level']
    tsktimeline = tskdict['Duration']
    taskval = None
    if tsknote is None:
        taskval = task_consts.M3Task(tskname, tsktype, tskexec, tskexekey, tsktext, 
                                tskfailure, tskdict[tskexekey])
    else:
        taskval = task_consts.M3Task(tskname, tsktype, tskexec, tskexekey, tsktext, 
                                tskfailure, tskdict[tskexekey], tsknote)
    if tskexekey == 'scriptspec':
        taskval.specification.resolve_location(myapihandler, config)
    return (tskid, tskoutline, tsktimeline, taskval)


def write_close_task(ischecktask, tasksjson, predecessors):
    if ischecktask:
        # close out CHECK task
        tasksjson.write('] }}')
        ischecktask = False
    # TODO Close out current task
    tasksjson.write(', "failure": "manual", "predecessors": [')
    _firstpred = True
    for _predval in predecessors:
        _outstr = '{}'.format(_predval) if _firstpred else ', {}'.format(_predval)
        if _firstpred:
            _firstpred = False
        tasksjson.write(_outstr)
    tasksjson.write('] }}')
    return ischecktask


def load_convert_tasks_fromcsv(lggr, input='tasks2.csv', tmppath='/Users/mugopala/tmp', basepath=None):
    _fullpath = './input/{}'.format(input) if basepath is None else '{}/input/{}'.format(basepath, input)
    lggr.debug(_fullpath)
    _outpath = '{}_tmptasks.json'.format(tmppath) if tmppath[-1] == '/' else '{}/_tmptasks.json'.format(tmppath)
    _tsksstr = None
    with open(_fullpath, newline='') as csvfile:
        _csvrdr = csv.DictReader(csvfile)
        _tasksjson = StringIO()
        _stagerevidmap = {}
        _taskidmap = []
        _tsksetidmap = {}
        _tsksetrevidmap = {}
        _checkidmap = []
        _taskparentidmap = []
        _currstgname = None
        _currsetname = None
        _currtskname = None
        _predecessors = []
        _isnewstage = False
        _isnewtskset = False
        _ischecktask = False
        _isnewchecktask = False
        for _tskdict in _csvrdr:
            if 'Task Name' not in _tskdict:
                raise common_entities.M3GeneralChoreographyException('Missing vital property in task specification')
            if 'Outline Level' not in _tskdict:
                raise common_entities.M3GeneralChoreographyException('Missing vital property in task specification')
            # ASSUME: ID, Duration, and Predecessor exist as it is a standard MPP field
            # each output is _tasksjson.write(thestring)
            _outlinelevel = int(_tskdict['Outline Level'])
            _tskid = int(_tskdict['ID'])
            _nametext = _tskdict['Task Name'].strip()
            _outstr = None
            if _outlinelevel == 4:
                 # TODO generalize type; if type exists, create a condition spec to automatically execute check
                _outstr = '{{"name": "{}", "type": "manual"}}'.format(_nametext) if _isnewchecktask else ', {{"name": "{}", "type": "manual"}}'.format(_nametext)
                _tasksjson.write(_outstr)
                _outstr = None
                if _isnewchecktask:
                    _isnewchecktask = False
            elif _outlinelevel == 1:
                if _nametext == _tskdict['Project'].strip():
                    continue
                elif 'Foundation' in _nametext:
                    _stagerevidmap[task_consts.M3TaskStage.FOUNDATION] = _tskid
                    _isnewstage = True
                    _currstgname = task_consts.M3TaskStage.FOUNDATION.name
                elif 'Primordial' in _nametext:
                    _stagerevidmap[task_consts.M3TaskStage.PRIMORDIAL] = _tskid
                    _isnewstage = True
                    _currstgname = task_consts.M3TaskStage.PRIMORDIAL.name
                elif 'Agent Based' in _nametext:
                    _stagerevidmap[task_consts.M3TaskStage.CORE] = _tskid
                    _isnewstage = True
                    _currstgname = task_consts.M3TaskStage.CORE.name
                elif 'All Remaining' in _nametext:
                    _stagerevidmap[task_consts.M3TaskStage.HIGHER] = _tskid
                    _isnewstage = True
                    _currstgname = task_consts.M3TaskStage.HIGHER.name
                else:
                    # TODO if 0 duration task it is a check task for all
                    # TODO: else it is a link task for all
                    pass
            elif _outlinelevel == 2:
                _ischecktask = write_close_task(_ischecktask, _tasksjson, _predecessors)
                _currtskname = None
                _predecessors.clear()
                # Close out tasks in set, task set itself, then start new task set
                _tasksjson.write('] }}, {{ "name": "{}", "stage": "{}", '.format(_nametext, _currstgname))
                _currsetname = _nametext
                _tsksetidmap[_tskid] = _currsetname
                _tsksetrevidmap[_currsetname] = _tskid
                _outstr = 'BUILD' if 'Area' in _tskdict or _tskdict['Area'].isspace() else _tskdict['Area']
                _tasksjson.write(_outstr)
                _outstr = None
                _tasksjson.write('"tasks": [')
                _isnewtskset = True
            elif _outlinelevel == 3:
                _ischecktask = write_close_task(_ischecktask, _tasksjson, _predecessors)
                _predecessors.clear()
                if _isnewtskset:
                    _isnewtskset = False
                _currtskname = _nametext
                if 'Type' not in _tskdict or _tskdict['Type'].isspace():
                    raise common_entities.M3GeneralChoreographyException('Missing vital property in task specification')
                if 'Team' not in _tskdict or _tskdict['Team'].isspace():
                    raise common_entities.M3GeneralChoreographyException('Missing vital property in task specification')
                _tasksjson.write('{{ "name": "{}", "type": "{}", "team": "{}", '.format(_nametext, _tskdict['Type'].strip().lower(), _tskdict['Team'].strip().upper()))
                _tsktype = task_consts.M3TaskType.from_name(_tskdict['Type'].strip().lower())
                if _tsktype == task_consts.M3TaskType.CHECK:
                    # TODO if check task, output "checkspec": { "action": "ALL TRUE", "conditions": [ 
                    _outstr = '"mode": "check", '
                    _mode = 'check'
                    pass
                else:
                    if 'Mode' not in _tskdict or _tskdict['Mode'].isspace():
	                    # TODO c. if does not exist and type not check, set mode as 'manual' and define a standard JIRA spec for the team
                        _outstr = ''
                        raise common_entities.M3GeneralChoreographyException('Missing vital property in task specification')
                    else:
                        _mode = _tskdict['Mode'].strip().lower()
                        _outstr = '"mode": "{}", '.format(_mode)
                _tasksjson.write(_outstr)
                if _mode == 'check':
	                # TODO b. if does not exist, if it is a check type create a new check spec and add mode as 'check'
                    pass
                elif _mode == '':
	                # TODO a. look for corresponding spec and add
                    pass
                # TODO if predecessors exist, look up the id and find the nearest task set and use its name instead

        _tsksstr = _tasksjson.getvalue()

    # TODO output _tsksstr to _outpath
    return _outpath


def cs_load_tasks_fromcsv(lggr, myapihandler, config, filename='tasks2.csv', basepath=None):
    _fullpath = './input/{}'.format(filename) if basepath is None else '{}/input/{}'.format(basepath, filename)
    lggr.debug(_fullpath)
    with open(_fullpath, newline='') as csvfile:
        csvrdr = csv.DictReader(csvfile)
        stages = { task_consts.M3TaskStage.FOUNDATION:None, 
                    task_consts.M3TaskStage.PRIMORDIAL:None,
                    task_consts.M3TaskStage.CORE:None,
                    task_consts.M3TaskStage.HIGHER:None
                }
        _alltasks = []
        _allgroups = {}
        tskstage = None
        tskgroup = None
        for tskdict in csvrdr:
            tskgrpstr = None
            tskstgstr = None
            _tsknum = None
            tsktimeline = None
            _timevalue = -1 # 0 value tasks are markers
            tskchkcondstr = None
            taskval = None
            _outlinelevel = -1
            (_tsknum, _outlinelevel, tsktimeline, taskval) = cs_parse_csv_task(lggr, myapihandler, config, tskdict)
            _tskgrpcreated = False
            if _outlinelevel == 1:
                # stage if followed by other outlines
                tskstgstr = tskdict['Task Name'].strip()
                # TODO Determine when it is a stage and when it is just a level 1 task
                tskstage = task_consts.M3TaskStage.from_name(tskstgstr)
            elif _outlinelevel == 2:
                # TaskSet
                tskgrpstr = tskdict['Task Name'].strip()
                tskgroup = create_task_group(tskstage, lggr, tskdict)
                _allgroups[tskgrpstr] = tskgroup
                _tskgrpcreated = True
                if stages[tskstage] is None:
                    stages[tskstage] = tskgroup
            elif _outlinelevel == 3:
                pass # vanilla task, name is task text, task name is generated from ID
            elif _outlinelevel == 4:
                tskchkcondstr = tskdict['Task Name'].strip() # steps within a Check Spec
            else:
                raise common_entities.M3GeneralChoreographyException('Error unknown value in task specification')
            # TODO Parse and handle timelines (timeline should be for whole group)
            _prival = 0
            # Duration (For timelines; 0 duration tasks are markers NEED TO IMPLEMENT CONCEPT)
            # predecessors are task numbers or ids in MS Project exported CSV
            # Predecessors (outside group or phase should be changed to the whole group, inside could be to omitted as it is in sequence)
            if len(tskdict['predecessor']) > 0:
                for tskpred in tskdict['predecessor']:
                    _predtsk = _alltasks[tskpred]
                    _predgrp = _allgroups[_predtsk.group_name]
                    tskgroup.predecessors.append(_predgrp)
                    _predgrp.successors.append(tskgroup)
                    if _tskgrpcreated and _predgrp.priority > _prival:
                        _prival = _predgrp.priority
            if _tskgrpcreated:
                _prival = _prival + 1
                taskval.priority = _prival
            _alltasks[_tsknum] = taskval
            tskgroup.tasks.append(taskval)
            taskval.group_name = tskgroup.name
        return stages


def choreograph_tasks(lggr, tasksbystage, appcfg):
    # Establish communication queues
    exeQ = stdq.Queue()
    resultQ = stdq.Queue()

    # Start consumers
#    num_consumers = multiprocessing.cpu_count() * 2
#    print('Creating {} consumers'.format(num_consumers))
#    consumers = [
#        SaasCs2TaskPerformer(exeQ, resultQ, appcfg)
#        for i in range(num_consumers)
#    ]
#    for w in consumers:
#        w.start()
    consumer = M3TaskPerformer(exeQ, resultQ, lggr, appcfg)
    consumer.start()

    currstg = task_consts.M3TaskStage.PRIMORDIAL
    stgstr = "%s" % currstg
    print(stgstr)

    producer = M3TaskStateManager(exeQ, resultQ, lggr, currstg, tasksbystage[currstg], appcfg)
    producer.start()

    exeQ.put(tasksbystage[currstg])

global tasksinstage
tasksinstage = []

def print_task(taskval):
    global tasksinstage
    if taskval is None:
        print('    No task passed in')
    else:
        if len(tasksinstage) <= 0 or taskval.name not in tasksinstage:
            print("    %s" % taskval)
            tasksinstage.append(taskval)
        if len(taskval.successors) <= 0:
            print('    End of line')
        else:
            for tskinst in taskval.successors:
                print_task(tskinst)

