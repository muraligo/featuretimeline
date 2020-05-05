#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 09 15:44:40 2020

@author: mugopala

Constants, types, etc for task and related objects
"""

from enum import Enum, unique
from .common_entities import SaasCsReferenceDataException, \
    SaasCsTextFileLocation, SaasCsTextOSSLocation

@unique
class SaasCsTaskType(Enum):
    PERFORM = ('perform', 1)
    CHECK = ('check', 2)
    LINK = ('link', 3)

    def __init__(self, datname, intval):
        self.dataname = datname
        self.intvalue = intval

    @staticmethod
    def from_name(datname):
        for name, member in SaasCsTaskType.__members__.items():
            if datname == member.dataname:
                return member
        raise ValueError("Unknown task type value [%s]." % datname)


@unique
class SaasCsTaskStage(Enum):
    FOUNDATION = ('foundation', 1)
    PRIMORDIAL = ('primordial', 2)
    CORE = ('core', 3)
    HIGHER = ('higher', 4)

    def __init__(self, datname, intval):
        self.dataname = datname
        self.order = intval

    @staticmethod
    def from_name(datname):
        for name, member in SaasCsTaskStage.__members__.items():
            if datname == member.dataname:
                return member
        raise ValueError("Unknown stage value [%s]." % datname)


@unique
class SaasCsTaskExecutor(Enum):
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
        for name, member in SaasCsTaskExecutor.__members__.items():
            if datname == member.dataname:
                return member
        raise ValueError("Unknown executor value [%s]." % datname)


@unique
class SaasCsTaskState(Enum):
    NEW = ('new', 1)
    READY = ('ready', 2)
    RUNNING = ('running', 3)
    DONE = ('done', 4)

    def __init__(self, datname, intval):
        self.dataname = datname
        self.intvalue = intval

    @staticmethod
    def from_name(datname):
        for name, member in SaasCsTaskState.__members__.items():
            if datname == member.dataname:
                return member
        raise ValueError("Unknown state value [%s]." % datname)


class SaasCsSpecification:

    def __init__(self):
        pass

    def resolve_location(self, myapihandler, config):
        pass

class SaasCsTerraformSpecification(SaasCsSpecification):

    def __init__(self, tflocation):
        self.location = tflocation

    def __str__(self):
        return 'Terraform{at %s}' % (self.location)

    @staticmethod
    def from_kvstruct(tskspecval):
        return SaasCsTerraformSpecification(tskspecval['location'])


class SaasCsChefSpecification(SaasCsSpecification):

    def __init__(self, recipelocation):
        self.location = recipelocation

    def __str__(self):
        return 'Chef{at %s}' % (self.location)

    @staticmethod
    def from_kvstruct(tskspecval):
        return SaasCsChefSpecification(tskspecval['location'])


class SaasCsScriptSpecification(SaasCsSpecification):

    def __init__(self, scriptlocation):
        self.locatespec = scriptlocation
        self.location = None

    def resolve_location(self, myapihandler, config):
        print("resolve location called for spec %s" % self.locatespec)
        if self.locatespec['type'] == 'file':
            self.location = SaasCsTextFileLocation(config, self.locatespec)
        elif self.locatespec['type'] == 'object':
            self.location = SaasCsTextOSSLocation(myapihandler, config, self.locatespec)

    def __str__(self):
        return 'Shell{at %s}' % (self.locatespec)

    @staticmethod
    def from_kvstruct(tskspecval):
        return SaasCsScriptSpecification(tskspecval['location'])


class SaasCsJiraSpecification(SaasCsSpecification):

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
        return SaasCsJiraSpecification(tskspecval['project'], tskspecval['issuetype'], 
                isslabels=tskspecval['labels'], isscomponents=tskspecval['components'], 
                parentisstype=parent_type, parentissid=parent_id)


class SaasCsBootstrapTask:

    def __init__(self, tskname, tsktype, tskexec, tskspectype, tskteam, tskfailact, tskspecval, tsknote=None):
        self.name = tskname
        self.task_type = tsktype
        self.successors = []
        self.predecessors = []
        self.executor = tskexec
        self.team = tskteam
        self.onfailure = tskfailact
        self.priority = 1
        self.state = SaasCsTaskState.NEW
        if tskspectype == 'jiraspec':
            self.specification = SaasCsJiraSpecification.from_kvstruct(tskspecval)
        elif tskspectype == 'terraformspec':
            self.specification = SaasCsTerraformSpecification.from_kvstruct(tskspecval)
        elif tskspectype == 'scriptspec':
            self.specification = SaasCsScriptSpecification.from_kvstruct(tskspecval)
        else:
            self.specification = None
        if tsknote:
            self.note = tsknote

    def __str__(self):
        return 'Task{[%s] of type %s and executor %s at priority %02d}' % (self.name, self.task_type, self.executor, self.priority)

