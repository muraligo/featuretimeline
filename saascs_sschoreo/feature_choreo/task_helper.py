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


class M3TaskSetStateManager(threading.Thread):

    def __init__(self, task_queue, result_queue, lggr, tskstage, firsttaskset, appconfig):
        super(M3TaskSetStateManager, self).__init__()
        # TODO implement any environment initialization
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.stage = tskstage
        self.tasksetsinstage = {}
        self.taskorderinsets = {}
        self.tasksinsets = {}
        self.logger = lggr
        q = stdq.SimpleQueue()
        q.put(firsttaskset)
        while (not q.empty()):
            tasksetval = q.get()
            tasksetval.state = task_consts.M3TaskState.READY
            self.tasksetsinstage[tasksetval.name] = tasksetval
            _tsksinset = {}
            for _ix in range(len(tasksetval.tasks)):
                _tsksinset[tasksetval.tasks[_ix].name] = _ix
                self.tasksinsets[tasksetval.tasks[_ix].name] = tasksetval
            self.taskorderinsets[tasksetval.name] = _tsksinset
            for tsksetinst in tasksetval.successors:
                q.put(tsksetinst)
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
            _tskset = self.tasksinsets[taskval.name]
            if not _tskset.alldone():
                # while tasks in current set are NOT DONE, keep rolling through them
                _tsksinset = self.taskorderinsets[_tskset.name]
                _ix1tsk = _tsksinset[taskval.name]
                _ix1tsk += 1
                if _ix1tsk < len(_tskset.tasks):
                    _tskset.tasks[_ix1tsk].state = task_consts.M3TaskState.RUNNING
                    self.task_queue.put(_tskset.tasks[_ix1tsk])
                continue
            _alldone = True
            # task set done, look at successors
            _tskset.state = task_consts.M3TaskState.DONE
            if len(_tskset.successors) <= 0:
                # if we reach a tail task set, check if all task sets are DONE
                # if so, inject a poison pill
                for tsksetnm in self.tasksetsinstage:
                    if self.tasksetsinstage[tsksetnm].state == task_consts.M3TaskState.DONE:
                        continue
                    else:
                        _alldone = False
                        break
                if _alldone == True:
                    # inject poison pill
                    self.task_queue.put(None)
                continue
            # loop thru successors adding any whose predecessors are all done
            for tsksetinst in _tskset.successors:
                _tskready = True
                if len(tsksetinst.predecessors) > 0:
                    for tskpred in tsksetinst.predecessors:
                        if tskpred.state == task_consts.M3TaskState.DONE:
                            continue
                        _tskready = False
                        break
                if _tskready == True:
                    tsksetinst.state = task_consts.M3TaskState.RUNNING
                    tskinst = tsksetinst.tasks[0]
                    tskinst.state = task_consts.M3TaskState.RUNNING
                    self.task_queue.put(tskinst)


def cs_parse_json_task(lggr, myapihandler, config, tskdict):
    tsknote = tskdict['note'] if 'note' in tskdict else None
    tskname = None
    tsktext = None
    tskexec = None
    tsktype = None
    tskexekey = None
    tskteam = None
    tskfailure = None
    if 'name' not in tskdict:
        raise common_entities.M3GeneralChoreographyException('Missing vital property in task specification')
    else:
        tskname = tskdict['name']
    if 'type' not in tskdict:
        raise common_entities.M3GeneralChoreographyException('Missing vital property in task specification')
    else:
        tsktype = task_consts.M3TaskType.from_name(tskdict['type'])
    if 'team' not in tskdict:
        raise common_entities.M3GeneralChoreographyException('Missing vital property in task specification')
    else:
        tskteam = tskdict['team']
    if 'text' not in tskdict:
        raise common_entities.M3GeneralChoreographyException('Missing vital property in task specification')
    else:
        tsktext = tskdict['text']
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
        taskval = task_consts.M3Task(tskname, tsktype, tskteam, tskexec, tskexekey, 
                                tsktext, tskfailure, tskdict[tskexekey])
    else:
        taskval = task_consts.M3Task(tskname, tsktype, tskteam, tskexec, tskexekey, 
                                tsktext, tskfailure, tskdict[tskexekey], tsknote)
    if tskexekey == 'scriptspec':
        taskval.specification.resolve_location(myapihandler, config)
    return taskval


def load_tasks_fromjson(lggr, myapihandler, config, filename='tasks3.json', basepath=None):
    _fullpath = './input/{}'.format(filename) if basepath is None else '{}/input/{}'.format(basepath, filename)
    lggr.debug(_fullpath)
    jshash = json.loads(file_reader(_fullpath))
    if jshash and 'tasksets' in jshash and len(jshash['tasksets']) > 0:
        stages = { task_consts.M3TaskStage.FOUNDATION:None, 
                    task_consts.M3TaskStage.PRIMORDIAL:None,
                    task_consts.M3TaskStage.CORE:None,
                    task_consts.M3TaskStage.HIGHER:None
                }
        _allsets = {}
        for tsksetdict in jshash['tasksets']:
            tsksetname = None
            tsksetarea = None
            tsksetstage = None
            if 'name' not in tsksetdict:
                raise common_entities.M3GeneralChoreographyException('Missing vital property in task specification')
            else:
                tsksetname = tsksetdict['name']
            if 'stage' not in tsksetdict:
                raise common_entities.M3GeneralChoreographyException('Missing vital property in task specification')
            else:
                tsksetstage = task_consts.M3TaskStage.from_name(tsksetdict['stage'])
            if 'area' not in tsksetdict:
                raise common_entities.M3GeneralChoreographyException('Missing vital property in task specification')
            else:
                tsksetarea = task_consts.M3TaskArea.from_name(tsksetdict['area'])
            tsksetval = task_consts.M3TaskSet(tsksetname, tsksetarea, tsksetstage)
            _setprival = 0
            for tskdict in tsksetdict['tasks']:
                taskval = cs_parse_json_task(lggr, myapihandler, config, tskdict)
                _prival = _setprival
                if 'predecessor' in tskdict and len(tskdict['predecessor']) > 0:
                    for tskpred in tskdict['predecessor']:
                        if (_allsets[tskpred] not in tsksetval.predecessors):
                            tsksetval.predecessors.append(_allsets[tskpred])
                            _allsets[tskpred].successors.append(tsksetval)
                        if _allsets[tskpred].priority > _prival:
                            _prival = _allsets[tskpred].priority
                _prival = _prival + 1
                taskval.priority = _prival
                tsksetval.priority = _prival
                _setprival = _prival
                tsksetval.tasks.append(taskval)
            if stages[tsksetstage] is None:
                stages[tsksetstage] = tsksetval
            _allsets[tsksetname] = tsksetval
        return stages
    else:
        raise common_entities.M3ReferenceDataException('Tasks', 'Empty')


def write_close_task(ischecktask, tasksjson, predecessors):
    if ischecktask:
        # close out CHECK task
        tasksjson.write('] }}')
        ischecktask = False
    # Close out current task
    tasksjson.write(', "failure": "manual", "predecessors": [')
    _outstr = ','.join(predecessors)
    tasksjson.write(_outstr)
    tasksjson.write('] }}')
    return ischecktask


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
        _taskparentidmap = {}
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
                _outstr = 'BUILD' if 'Area' not in _tskdict or _tskdict['Area'].isspace() else _tskdict['Area']
                _tasksjson.write('"area": "{}", '.format(_outstr))
                _outstr = None
                _tasksjson.write('"tasks": [')
                _isnewtskset = True
                _taskparentidmap[_tskid] = _tskid # put self also in there
            elif _outlinelevel == 3:
                _ischecktask = write_close_task(_ischecktask, _tasksjson, _predecessors)
                _predecessors.clear()
                if _isnewtskset:
                    _isnewtskset = False
                _currtskname = 'Task{}'.format(_tskid)
                if 'Type' not in _tskdict or _tskdict['Type'].isspace():
                    raise common_entities.M3GeneralChoreographyException('Missing vital property in task specification')
                if 'Team' not in _tskdict or _tskdict['Team'].isspace():
                    raise common_entities.M3GeneralChoreographyException('Missing vital property in task specification')
                _tasksjson.write('{{ "name": "{}", "type": "{}", "team": "{}", "text": "{}", '.format(_currtskname, _tskdict['Type'].strip().lower(), _tskdict['Team'].strip().upper(), _nametext))
                _tsktype = task_consts.M3TaskType.from_name(_tskdict['Type'].strip().lower())
                _tsktarget = None
                if _tsktype == task_consts.M3TaskType.CHECK:
                    _outstr = '"mode": "check", '
                    _mode = 'check'
                    pass
                else:
                    if 'Mode' not in _tskdict or _tskdict['Mode'].isspace():
	                    # TODO c. if does not exist and type not check, set mode as 'manual' and define a standard JIRA spec for the team
                        _outstr = ''
                        raise common_entities.M3GeneralChoreographyException('Missing vital property in task specification')
                    else:
                        if 'Target' not in _tskdict or _tskdict['Target'].isspace():
                            raise common_entities.M3GeneralChoreographyException('Missing vital property in task specification')
                        else:
                            _tsktarget = _tskdict['Target'].strip()
                        _mode = _tskdict['Mode'].strip().lower()
                        _outstr = '"mode": "{}", '.format(_mode)
                _tasksjson.write(_outstr)
                _outstr = None
                _taskparentidmap[_tskid] = _tsksetrevidmap[_currsetname]
                if _mode == 'check':
                    _outstr = '"checkspec": {{ "action": "ALL TRUE", "conditions": [ '
                elif _mode == 'terraform':
	                _outstr = '"terraformspec": {{ "location": {{ "type": "object", "target": "{}"'.format(_tsktarget)
                elif _mode == 'chef':
	                _outstr = '"chefspec": {{ "location": {{ "type": "object", "target": "{}"'.format(_tsktarget)
                elif _mode == 'shell':
	                _outstr = '"scriptspec": {{ "location": {{ "type": "object", "target": "{}"'.format(_tsktarget)
                elif _mode == 'manual':
                    _tgtparts = _tsktarget.split('.')
                    _outstr = '"jiraspec": {{ "project": "{}", "issuetype": "STORY", "components": ["{}"], "labels": ["{}"], "parent": {{ "issuetype": "EPIC", "issueid": "{}" }} }}'.format(_tgtparts[0], _tgtparts[2], _tgtparts[1], _tgtparts[3])
                _tasksjson.write(_outstr)
                _tgtparts = None
                # if predecessors exist, look up the id and find the nearest task set and use its name instead
                if 'Predecessors' in _tskdict and not _tskdict['Predecessors'].isspace():
                    _tgtparts = _tskdict['Predecessors'].split(',')
                    _predecessors = [_tsksetidmap[_taskparentidmap[_tgtprt]] for _tgtprt in _tgtparts]
            else:
                pass # invalid outline level

        _tsksstr = _tasksjson.getvalue()

    # TODO output _tsksstr to _outpath
    return _outpath


def choreograph_tasksets(lggr, tasksbystage, appcfg):
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

    producer = M3TaskSetStateManager(exeQ, resultQ, lggr, currstg, tasksbystage[currstg], appcfg)
    producer.start()

    exeQ.put(tasksbystage[currstg].tasks[0])


global tasksinstage
tasksinstage = []


def print_task_set(tsksetval):
    global tasksinstage
    if tsksetval is None:
        print('    No task passed in')
    else:
        if len(tasksinstage) <= 0 or tsksetval.name not in tasksinstage:
            print("    %s" % tsksetval)
            tasksinstage.append(tsksetval)
        if len(tsksetval.successors) <= 0:
            print('    End of line')
        else:
            for tskinst in tsksetval.successors:
                print_task_set(tskinst)

