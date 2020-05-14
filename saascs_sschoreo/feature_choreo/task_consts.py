#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 09 15:44:40 2020

@author: mugopala

Constants, types, etc for task and related objects
"""

from enum import Enum, unique
from .common_entities import M3TextFileLocation, M3TextOSSLocation

@unique
class M3TaskType(Enum):
    PERFORM = ('perform', 1)
    CHECK = ('check', 2)
    LINK = ('link', 3)

    def __init__(self, datname, intval):
        self.dataname = datname
        self.intvalue = intval

    @staticmethod
    def from_name(datname):
        for name, member in M3TaskType.__members__.items():
            if datname == member.dataname:
                return member
        raise ValueError("Unknown task type value [%s]." % datname)


@unique
class M3TaskStage(Enum):
    FOUNDATION = ('foundation', 1)
    PRIMORDIAL = ('primordial', 2)
    CORE = ('core', 3)
    HIGHER = ('higher', 4)

    def __init__(self, datname, intval):
        self.dataname = datname
        self.order = intval

    @staticmethod
    def from_name(datname):
        for name, member in M3TaskStage.__members__.items():
            if datname == member.dataname:
                return member
        raise ValueError("Unknown stage value [%s]." % datname)


@unique
class M3TaskExecutor(Enum):
    MANUAL = ('manual', 'jiraspec', 1)
    SHELL = ('shell', 'scriptspec', 2)
    TERRAFORM = ('terraform', 'terraformspec', 3)
    CHEF = ('chef', 'chefspec', 4)
    CHECK = ('check', 'checkspec', 5)

    def __init__(self, datname, sectname, intval):
        self.dataname = datname
        self.section_name = sectname
        self.intvalue = intval

    @staticmethod
    def from_name(datname):
        for name, member in M3TaskExecutor.__members__.items():
            if datname == member.dataname:
                return member
        raise ValueError("Unknown executor value [%s]." % datname)


@unique
class M3TaskState(Enum):
    NEW = ('new', 1)
    READY = ('ready', 2)
    RUNNING = ('running', 3)
    DONE = ('done', 4)

    def __init__(self, datname, intval):
        self.dataname = datname
        self.intvalue = intval

    @staticmethod
    def from_name(datname):
        for name, member in M3TaskState.__members__.items():
            if datname == member.dataname:
                return member
        raise ValueError("Unknown state value [%s]." % datname)


@unique
class M3TaskArea(Enum):
    BUILD = ('build', 1)
    ARCHITECTURE = ('architecture', 2)
    SECURITY = ('security', 3)
    COMPLIANCE = ('compliance', 4)

    def __init__(self, datname, intval):
        self.dataname = datname
        self.intvalue = intval

    @staticmethod
    def from_name(datname):
        for name, member in M3TaskArea.__members__.items():
            if datname == member.dataname:
                return member
        raise ValueError("Unknown area value [%s]." % datname)


class M3Specification:

    def __init__(self):
        pass

    def resolve_location(self, myapihandler, config):
        pass

class M3TerraformSpecification(M3Specification):

    def __init__(self, tflocation):
        self.location = tflocation

    def __str__(self):
        return 'Terraform{at %s}' % (self.location)

    @staticmethod
    def from_kvstruct(tskspecval):
        return M3TerraformSpecification(tskspecval['location'])


class M3ChefSpecification(M3Specification):

    def __init__(self, recipelocation):
        self.location = recipelocation

    def __str__(self):
        return 'Chef{at %s}' % (self.location)

    @staticmethod
    def from_kvstruct(tskspecval):
        return M3ChefSpecification(tskspecval['location'])


class M3ScriptSpecification(M3Specification):

    def __init__(self, scriptlocation):
        self.locatespec = scriptlocation
        self.location = None

    def resolve_location(self, myapihandler, config):
        print("resolve location called for spec %s" % self.locatespec)
        if self.locatespec['type'] == 'file':
            self.location = M3TextFileLocation(config, self.locatespec)
        elif self.locatespec['type'] == 'object':
            self.location = M3TextOSSLocation(myapihandler, config, self.locatespec)

    def __str__(self):
        return 'Shell{at %s}' % (self.locatespec)

    @staticmethod
    def from_kvstruct(tskspecval):
        return M3ScriptSpecification(tskspecval['location'])


class M3JiraSpecification(M3Specification):

    def __init__(self, issproject, isstype, isslabels=None, isscomponents=None, 
                    parentisstype=None, parentissid=None):
        self.project = issproject
        self.issue_type = isstype
        self.labels = [] if isslabels is None else isslabels
        self.components = [] if isscomponents is None else isscomponents
        self.parent_type = parentisstype
        self.parent_id = parentissid

    def __str__(self):
        return 'JIRA{%s-%s under %s-%s}' % (self.project, self.issue_type, self.parent_type, self.parent_id)

    @staticmethod
    def from_kvstruct(tskspecval):
        parent_type = None
        parent_id = None
        if tskspecval['parent']:
            parentspec = tskspecval['parent']
            parent_type = parentspec['issuetype']
            parent_id = parentspec['issueid']
        return M3JiraSpecification(tskspecval['project'], tskspecval['issuetype'], 
                isslabels=tskspecval['labels'], isscomponents=tskspecval['components'], 
                parentisstype=parent_type, parentissid=parent_id)


class M3TaskSet:

    def __init__(self, tskname, tskarea, tskstg):
        self.name = tskname
        self.area = tskarea
        self.stage = tskstg
        self.tasks = []
        self.successors = []
        self.predecessors = []
        self.priority = 1
        self.state = M3TaskState.NEW

    def __str__(self):
        return 'TaskSet{[%s] of area %s at priority %02d}' % (self.name, self.area, self.priority)


class M3FlatTask:

    def __init__(self, tskname, tsktype, tskexec, tskspectype, tskteam, tskfailact, tskspecval, tsknote=None):
        self.name = tskname
        self.task_type = tsktype
        self.successors = []
        self.predecessors = []
        self.executor = tskexec
        self.team = tskteam
        self.onfailure = tskfailact
        self.priority = 1
        self.state = M3TaskState.NEW
        if tskspectype == 'jiraspec':
            self.specification = M3JiraSpecification.from_kvstruct(tskspecval)
        elif tskspectype == 'terraformspec':
            self.specification = M3TerraformSpecification.from_kvstruct(tskspecval)
        elif tskspectype == 'scriptspec':
            self.specification = M3ScriptSpecification.from_kvstruct(tskspecval)
        else:
            self.specification = None
        if tsknote:
            self.note = tsknote

    def __str__(self):
        return 'Task{[%s] of type %s and executor %s at priority %02d}' % (self.name, self.task_type, self.executor, self.priority)


class M3Task:

    # TODO drop successors and predecessors (infer based on order in list)
    # TODO add txtlines[] and in JSON define as a list and make name short and unique
    # TODO create a Status enum NONE, PASS, FAIL and include other fields for error details
    # TODO have a status field initialized to NONE which should be set to PASS or FAIL on exec
    def __init__(self, tskname, tsktype, tskteam, tskexec, tskspectype, tsktext, tskfailact, tskspecval, tsknote=None):
        self.name = tskname
        self.group_name = None
        self.task_type = tsktype
        self.team = tskteam
        self.successors = []
        self.predecessors = []
        self.executor = tskexec
        self.onfailure = tskfailact
        self.priority = 1
        self.state = M3TaskState.NEW
        # TODO Split text into lines of a max width
        if tskspectype == 'jiraspec':
            self.specification = M3JiraSpecification.from_kvstruct(tskspecval)
        elif tskspectype == 'terraformspec':
            self.specification = M3TerraformSpecification.from_kvstruct(tskspecval)
        elif tskspectype == 'scriptspec':
            self.specification = M3ScriptSpecification.from_kvstruct(tskspecval)
        else:
            self.specification = None
        if tsknote:
            self.note = tsknote

    def __str__(self):
        return 'Task{[%s] of type %s and executor %s at priority %02d}' % (self.name, self.task_type, self.executor, self.priority)


