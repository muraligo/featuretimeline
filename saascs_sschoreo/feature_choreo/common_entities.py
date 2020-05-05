#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 09 15:44:40 2020

@author: mugopala

Various entities common to many projects
"""

from abc import ABC, abstractmethod

class AbstractSaasCsLocation(ABC):
 
    def __init__(self, locspec):
        self.specification = locspec
        super().__init__()

    @abstractmethod
    def read_content(self):
        pass

    @abstractmethod
    def byte_content(self):
        pass

    @abstractmethod
    def string_content(self):
        pass

    @abstractmethod
    def parsed_content(self):
        pass


class SaasCsChoreographyException(Exception):
    """
    Base class for exceptions in this module
    """
    def __init__(self):
        self.prefix = 'SaaS Cloud Service Choreographer: '


class SaasCsGeneralChoreographyException(SaasCsChoreographyException):
    """
    Any exceptional condition relating to SaaS Cloud Service Choreographer.

    Attributes:
        message -- explanation of why the specific transition is not allowed
    """
    def __init__(self, message):
        super().__init__()
        self.caller_message = message

    def __str__(self):
        return super.__str__ + "%sGeneral Error %s" % (self.prefix, self.caller_message)


class SaasCsReferenceDataException(SaasCsChoreographyException):
    """
    Any exceptional condition relating to Reference Data required 
    for SaaS Cloud Service Choreographer.

    Attributes:
        refdataname -- name of the kind of reference data
        message -- explanation of why the specific transition is not allowed
    """
    def __init__(self, refdataname, message):
        super().__init__()
        self.reference_data_name = refdataname
        self.caller_message = message

    def __str__(self):
        return "%sReference Data [%s] %s" % (self.prefix, self.reference_data_name, self.caller_message)


class SaasCsTextFileLocation(AbstractSaasCsLocation):

    def __init__(self, config, locspec):
        super().__init__(locspec)
        self.basepath = config['BASEPATH'] if 'BASEPATH' in config else None
        print("Basepath is %s" % self.basepath)
        self.locationpath = locspec['target']
        self.textdata = None

    def read_content(self):
        super().read_content()
        _fullpath = None
        if self.basepath is None:
            _fullpath = './{}'.format(self.locationpath)
        else:
            _fullpath = '{}/{}'.format(self.basepath, self.locationpath)
        try:
            with open(_fullpath, 'r') as f:
                self.textdata = f.read().strip()
        except Exception as err:
            raise SaasCsGeneralChoreographyException('Could not read {}'.format(_fullpath)).with_traceback(err.__traceback__)

    def byte_content(self):
        pass # as this is for text one

    def string_content(self):
        return self.textdata

    def parsed_content(self):
        pass # as this is a general one


class SaasCsTextOSSLocation(AbstractSaasCsLocation):

    def __init__(self, myapihandler, config, locspec):
        if 'OSS_CONFIG' not in config:
            raise ValueError('Location in Object Store cannot be determined if Object Store base URL is missing from Configuration')
        super().__init__(locspec)
        _ossccfg = config['OSS_CONFIG']
        # TODO Get a well-known named bucket and replace mitch-7262 below with it
        self.basepath = "{base_url}/n/{csrb_namespace}/b/mitch-7262/o/".format(
            base_url=_ossccfg['base_url'],
            csrb_namespace=_ossccfg['namespace']
        )
        self.locationpath = "{target}?compartmentId={compartment_id}".format(
            target=locspec['target'],
            compartment_id=_ossccfg['compartmentId'].replace(":", "%3A")
        )
        self.textdata = None
        self.apihandler = myapihandler

    def read_content(self):
        super().read_content()
        # 1: basepath cannot be None in this case 
        #    so we just construct the full path
        _fullpath = "{base_url}{resource_n_params}".format(
            base_url=self.basepath,
            resource_n_params=self.locationpath
        )
        # 2: download the resource contents from Object Store
        try:
            _result = self.apihandler.handle_get(_fullpath)
            if _result is not None and _result.status_code == 200:
                self.textdata = _result.text
        except Exception as err:
            raise SaasCsGeneralChoreographyException('Could not read {}'.format(_fullpath)).with_traceback(err.__traceback__)

    def byte_content(self):
        pass # as this is for text one

    def string_content(self):
        return self.textdata

    def parsed_content(self):
        pass # as this is a general one


