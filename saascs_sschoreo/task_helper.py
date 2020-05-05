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
        # TODO make this file executable
        os.chmod(scrptspath, _FILEPERMS)

        result = conn.run(scrptspath)
        if result.failed:
            raise common_entities.SaasCsGeneralChoreographyException('Execution of task {} failed with {}'.format(tskspec.location, result.stderr))
        else:
            return result.stdout

@task
def perform_chef(conn, lggr, tskspec):
    lggr.debug("    %s" % tskspec)

@task
def perform_terraform(conn, lggr, tskspec):
    lggr.debug("    %s" % tskspec)


class SaasCsTaskPerformer(threading.Thread):

    def __init__(self, task_queue, result_queue, lggr, appconfig):
        super(SaasCsTaskPerformer, self).__init__()
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
            if taskval.executor == task_consts.SaasCsTaskExecutor.MANUAL:
                perform_jira(self.conn, self.logger, taskval.specification)
            if taskval.executor == task_consts.SaasCsTaskExecutor.SHELL:
                perform_shell(self.conn, self.logger, taskval.specification)
            if taskval.executor == task_consts.SaasCsTaskExecutor.CHEF:
                perform_chef(self.conn, self.logger, taskval.specification)
            if taskval.executor == task_consts.SaasCsTaskExecutor.TERRAFORM:
                perform_terraform(self.conn, self.logger, taskval.specification)
            self.task_queue.task_done()
            # if it gets here without an exception that means it is successful
            self.result_queue.put(taskval)


class SaasCsTaskStateManager(threading.Thread):

    def __init__(self, task_queue, result_queue, lggr, tskstage, firsttask, appconfig):
        super(SaasCsTaskStateManager, self).__init__()
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
            taskval.state = task_consts.SaasCsTaskState.READY
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
            taskval.state = task_consts.SaasCsTaskState.DONE
            _alldone = True
            if len(taskval.successors) <= 0:
                for tsknm in self.tasksinstage:
                    if self.tasksinstage[tsknm].state == task_consts.SaasCsTaskState.DONE:
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
                        if tskpred.state == task_consts.SaasCsTaskState.DONE:
                            continue
                        _tskready = False
                        break
                if _tskready == True:
                    tskinst.state = task_consts.SaasCsTaskState.RUNNING
                    self.task_queue.put(tskinst)



def cs_load_tasks(lggr, myapihandler, config, filename='tasks2.json', basepath=None):
    _fullpath = './input/{}'.format(filename) if basepath is None else '{}/input/{}'.format(basepath, filename)
    lggr.debug(_fullpath)
    jshash = json.loads(file_reader(_fullpath))
    if jshash and 'tasks' in jshash and len(jshash['tasks']) > 0:
        stages = { task_consts.SaasCsTaskStage.FOUNDATION:None, 
                    task_consts.SaasCsTaskStage.PRIMORDIAL:None,
                    task_consts.SaasCsTaskStage.CORE:None,
                    task_consts.SaasCsTaskStage.HIGHER:None
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
                raise common_entities.SaasCsGeneralChoreographyException('Missing vital property in task specification')
            else:
                tsktype = task_consts.SaasCsTaskType.from_name(tskdict['type'])
            if 'stage' not in tskdict:
                raise common_entities.SaasCsGeneralChoreographyException('Missing vital property in task specification')
            else:
                tskstage = task_consts.SaasCsTaskStage.from_name(tskdict['stage'])
            if 'team' not in tskdict:
                raise common_entities.SaasCsGeneralChoreographyException('Missing vital property in task specification')
            else:
                tskteam = tskdict['team']
            if 'name' not in tskdict:
                raise common_entities.SaasCsGeneralChoreographyException('Missing vital property in task specification')
            else:
                tskname = tskdict['name']
            if 'failure' in tskdict:
                tskfailure = task_consts.SaasCsTaskExecutor.from_name(tskdict['failure'])
            else:
                tskfailure = task_consts.SaasCsTaskExecutor.MANUAL
            if tsktype == task_consts.SaasCsTaskType.CHECK:
                tskexec = task_consts.SaasCsTaskExecutor.CHECK
            else:
                if 'mode' not in tskdict:
                    raise common_entities.SaasCsGeneralChoreographyException('Missing vital property in task specification')
                else:
                    tskexec = task_consts.SaasCsTaskExecutor.from_name(tskdict['mode'])
            tskexekey = tskexec.section_name
            taskval = None
            if tsknote is None:
                taskval = task_consts.SaasCsBootstrapTask(tskname, tsktype, tskexec, tskexekey, 
                                tskteam, tskfailure, tskdict[tskexekey])
            else:
                taskval = task_consts.SaasCsBootstrapTask(tskname, tsktype, tskexec, tskexekey, 
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
        raise common_entities.SaasCsReferenceDataException('Tasks', 'Empty')

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
    consumer = SaasCsTaskPerformer(exeQ, resultQ, lggr, appcfg)
    consumer.start()

    currstg = task_consts.SaasCsTaskStage.PRIMORDIAL
    stgstr = "%s" % currstg
    print(stgstr)

    producer = SaasCsTaskStateManager(exeQ, resultQ, lggr, currstg, tasksbystage[currstg], appcfg)
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

