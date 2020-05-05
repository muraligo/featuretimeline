#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 26 16:11:20 2020

@author: mugopala

initalized with Jira.initforenv(appconfig['ENVNAME'], appconfig['JIRA_CONFIG'], applogger)
called as Jira('gbucs')
"""

import sys
from .helpers import get_secret
from jira import JIRA
from http import client as httpclient, HTTPStatus
from html.parser import HTMLParser
from html.entities import name2codepoint


def initforenv(envnm, appcfg, basepth, apploggr):
    print('In JIRA environment initialization')
    global config
    global envname
    global basepath
    global ticket_prefix
    global logger
    config = appcfg
    envname = envnm
    basepath = basepth
    ticket_prefix = config['jira-prefix']
    logger = apploggr
    if envname == 'local':
        logger.debug('Jira initialized for env {}, basepath {}. Issue prefix is {}'.format(
                    envname, basepath, ticket_prefix))
        print('Jira initialized for env {}, basepath {}. Issue prefix is {}'.format(
                    envname, basepath, ticket_prefix))

class Jira:
    __instance = None
    __connection = None
    __ssoconnection = None
    __ssoproto = None
    __ssourl = None
    __ssopath = None

    def __init__(self, jiratype):
        self.url = None
        self.username = None
        self.password = None
        print('Env {}, basepath {}. Issue prefix is {}'.format(
                    envname, basepath, ticket_prefix))
        if jiratype == 'gbucs':
            _propurl = config['jira-gbucs']
            _unloc = config['gbucs_username']
            _pwloc = config['gbucs_password']
            if _propurl.startswith("http"):
                _protoix = _propurl.find('://')
                if _protoix > 0: # it should be
                    self.protocol = _propurl[0:_protoix]
                    self.url = _propurl[_protoix+3:]
                else:
                    pass # should not happen
            else:
                self.protocol = None
                self.url = _propurl
            
            if envname == 'local':
                print("Handling LOCAL env")
                self.username = get_secret(envname, _unloc, basepath=basepath)
                self.password = get_secret(envname, _pwloc, basepath=basepath)
            else:
                print("Handling OTHER env")
                self.username = get_secret(envname, _unloc)
                self.password = get_secret(envname, _pwloc)
        else:
            raise Exception('Invalid JIRA option: {} not in ["gbucs"]'
                            .format(type))

        self.__connection = httpclient.HTTPSConnection(self.url, 443)
        self.__connection.set_debuglevel(3)
#        self.__connection = self.__jira_connect()
        self._formparser = _OraSSOFormParser()


    def __jira_connect(self):
        options_dict = {
            'server': self.url,
            'verify': False
        }
        return JIRA(
          options=options_dict,
          basic_auth=(self.username, self.password),
          proxies=None,
          timeout=20,
          max_retries=0
        )


    def get_issue(self, issue):
        return self.__connection.issue(issue)

    def search(self, jql, json=True):
        return self.__connection.search_issues(
            jql_str=jql,
            json_result=json,
            maxResults=-1,
        )

    def change_status(self, issue, status, addtionalParams):
        return self.__connection.transition_issue(issue,
                                                  status,
                                                  fields=addtionalParams)

    def add_comment(self, issue, body):
        return self.__connection.add_comment(issue=issue, body=body)

    def get_issue_metadata(self, issue):
        return self.__connection.editmeta(issue=issue)

    def get_create_issue_metadata(self, projectKey):
        return self.__connection.createmeta(projectKeys=[projectKey],
                                            expand="projects.issuetypes.fields"
                                            )

    def get_issue_transitions(self, issue):
        return self.__connection.transitions(issue=issue)

    def update_issue(self, issue, body):
        return self.__connection.issue(issue).update(fields=body)

    def projects(self):
        return self.__connection.projects()

    def create_issue(self, body):
        return self.__connection.create_issue(fields=body)

    def create_issue_link(self, link_type, inward_issue, outward_issue, comment=None):
        return self.__connection.create_issue_link(link_type, inward_issue, outward_issue, comment)

    def attach_file(self, issue, attachment, filename):
        return self.__connection.add_attachment(
            issue=issue,
            attachment=attachment,
            filename=filename
        )

    def getrequest(self, resource, path):
        return self.__request_get(resource, path)

    def __request_get(self, resource, path):
        # do the headers
        fullpath = "/rest/api/2/" + resource + path
        print("Full path is:", fullpath)
        try:
            self.__connection.request("GET", fullpath)
        except:
            print("Request Error is:", sys.exc_info()[0])
            raise
        httpresp = None
        try:
            httpresp = self.__connection.getresponse()
        except:
            print("Response Read Error is:", sys.exc_info()[0])
            raise
        if httpresp is None:
            return None
        if httpresp.getcode() != 200:
            while httpresp and httpresp.getcode() == 302:
                # do a redirect
                httpresp = self._doredirect(httpresp)
            else:
                return httpresp
        data1 = httpresp.read()
        print('Response is 200 and body is: ', data1)

        print('Non-empty response with status:', httpresp.getcode())
        thestr1 = data1.decode('UTF-8')
        self._formparser.feed(thestr1)
        # if empty response or status != 200 or status 200 and sso login form
        # perform a Form read and post our sso creds

    def _doredirect(self, httpresp):
        redirectloc = httpresp.getheader('Location')
        cookies = httpresp.getheader('Set-Cookie')
        data1 = httpresp.read()
        print('Response is 302 and body is: ', data1)
        remainloc = None
        if redirectloc.startswith("http"):
            _protoix = redirectloc.find('://')
            if _protoix > 0: # it should be
                self.__ssoproto = redirectloc[0:_protoix]
                remainloc = redirectloc[_protoix+3:]
            else:
                pass # should not happen
        else:
            self.__ssoproto = None
            remainloc = redirectloc
        _pathix = remainloc.find('/')
        if _pathix > 0: # it should be
            self.__ssopath = remainloc[_pathix:]
            if remainloc.find(':') > 0:
                _pathix = remainloc.find(':')
            self.__ssourl = remainloc[0:_pathix]
        else:
            self.__ssourl = remainloc
            self.__ssopath = ''
        self.__ssoconnection = httpclient.HTTPSConnection(self.__ssourl, 443)
        self.__ssoconnection.set_debuglevel(3)
        ssoheaders = {}
        ssoheaders['Set-Cookie'] = cookies
        try:
            self.__ssoconnection.request('GET', self.__ssourl, headers=ssoheaders)
        except:
            print("Request Error is:", sys.exc_info()[0])
            raise
        httpresp = None
        try:
            httpresp = self.__ssoconnection.getresponse()
        except:
            print("Response Read Error is:", sys.exc_info()[0])
            raise
        if httpresp is None:
            return None
        return httpresp


class _OraSSOFormParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        print("Start tag: {}".format(tag))
        for attr in attrs:
            print("     attr: {}".format(attr))

    def handle_endtag(self, tag):
        print("End tag: {}".format(tag))

    def handle_data(self, data):
        print("Data: {}".format(data))

    def handle_comment(self, data):
        print("Comment: {}".format(data))

    def handle_entityref(self, name):
        c = chr(name2codepoint[name])
        print("Named entity: {}".format(c))

    def handle_charref(self, name):
        if name.startswith('x'):
            c = chr(int(name[1:], 16))
        else:
            c = chr(int(name))
        print("Number entity: {}".format(c))

    def handle_decl(self, data):
        print("Declaration: {}".format(data))


