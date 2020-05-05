#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 26 16:32:07 2020

@author: mugopala
"""

import os
import errno
import codecs
import uuid
from itsdangerous import json


def file_reader(filename):
    try:
        with open(filename, 'r') as f:
            return f.read().strip()
    except Exception:
        print('Could not read {}'.format(filename))


def get_secret(envname, path, basepath=None, version='latest'):
    _fullpath = None
    if basepath is None:
        _fullpath = './dev_secrets/{}'.format(path)
    else:
        _fullpath = '{}/dev_secrets/{}'.format(basepath, path)

    # TODO: Ideally this should only be if envname == 'local' or envname == 'dev'
    # TODO: For other environments, there should be a SecretService API
    return file_reader(_fullpath)


class _JSONEncoder(json.JSONEncoder):
    """The default JSON encoder.  This one extends the default simplejson
    encoder by also supporting ``UUID`` objects.  
    In order to support more data types override the
    :meth:`default` method.
    """

    def default(self, o):
        """Implement this method in a subclass such that it returns a
        serializable object for ``o``, or calls the base implementation (to
        raise a :exc:`TypeError`).

        For example, to support arbitrary iterators, you could implement
        default like this::

            def default(self, o):
                try:
                    iterable = iter(o)
                except TypeError:
                    pass
                else:
                    return list(iterable)
                return JSONEncoder.default(self, o)
        """
        if isinstance(o, uuid.UUID):
            return str(o)
        return json.JSONEncoder.default(self, o)


class _JSONDecoder(json.JSONDecoder):
    """The default JSON decoder.  This one does not change the behavior from
    the default simplejson decoder.
    """



def _detect_encoding(data):
    """Detect which UTF codec was used to encode the given bytes.

    The latest JSON standard (:rfc:`8259`) suggests that only UTF-8 is
    accepted. Older documents allowed 8, 16, or 32. 16 and 32 can be big
    or little endian. Some editors or libraries may prepend a BOM.

    :param data: Bytes in unknown UTF encoding.
    :return: UTF encoding name
    """
    head = data[:4]

    if head[:3] == codecs.BOM_UTF8:
        return 'utf-8-sig'

    if b'\x00' not in head:
        return 'utf-8'

    if head in (codecs.BOM_UTF32_BE, codecs.BOM_UTF32_LE):
        return 'utf-32'

    if head[:2] in (codecs.BOM_UTF16_BE, codecs.BOM_UTF16_LE):
        return 'utf-16'

    if len(head) == 4:
        if head[:3] == b'\x00\x00\x00':
            return 'utf-32-be'

        if head[::2] == b'\x00\x00':
            return 'utf-16-be'

        if head[1:] == b'\x00\x00\x00':
            return 'utf-32-le'

        if head[1::2] == b'\x00\x00':
            return 'utf-16-le'

    if len(head) == 2:
        return 'utf-16-be' if head.startswith(b'\x00') else 'utf-16-le'

    return 'utf-8'


def jsonloads(s, **kwargs):
    """Unserialize a JSON object from a string ``s`` by using the
    configured decoder.
    """
    kwargs.setdefault('cls', _JSONDecoder)
    if isinstance(s, bytes):
        encoding = kwargs.pop('encoding', None)
        if encoding is None:
            encoding = _detect_encoding(s)
        s = s.decode(encoding)
    return json.loads(s, **kwargs)


def _from_mapping(*mapping, **kwargs):
    mappings = []
    if len(mapping) == 1:
        if hasattr(mapping[0], 'items'):
            mappings.append(mapping[0].items())
        else:
            mappings.append(mapping[0])
    elif len(mapping) > 1:
        raise TypeError('expected at most 1 positional argument, got %d' % len(mapping))
    mappings.append(kwargs.items())
    retval = dict()
    for mapping in mappings:
        for (key, value) in mapping:
            if key.isupper():
                retval[key] = value
    return retval

def from_json(filename, root_path, silent=False):
    """Updates the values in the config from a JSON file. This function
    behaves as if the JSON object was a dictionary and passed to the
    :meth:`from_mapping` function.

    :param filename: the filename of the JSON file.  This can either be an
                     absolute filename or a filename relative to the root path.
    :param rootpath: the root path for the application.
    :param silent: set to ``True`` if you want silent failure for missing files.
    :return: dict. populated dict if able to load config, ``None`` otherwise.
    """
    filename = os.path.join(root_path, filename)

    try:
        with open(filename) as json_file:
            obj = jsonloads(json_file.read())
    except IOError as e:
        if silent and e.errno in (errno.ENOENT, errno.EISDIR):
            return False
        e.strerror = 'Unable to load configuration file (%s)' % e.strerror
        raise
    return _from_mapping(obj)

def from_envvar(variable_name, silent=False):
    """Loads a configuration from an environment variable pointing to
    a configuration file.  This is basically just a shortcut with nicer
    error messages for this line of code::

        from_json(os.environ['YOURAPPLICATION_SETTINGS'])

    :param variable_name: name of the environment variable
    :param silent: set to ``True`` if you want silent failure for missing files.
    :return: dict. populated dict if able to load config, ``None`` otherwise.
    """
    rv = os.environ.get(variable_name)
    if not rv:
        if silent:
            return None
        raise RuntimeError('The environment variable %r is not set and as such '
                           'configuration could not be loaded.  Set this variable '
                           'and make it point to a configuration file' %
                            variable_name)
    cbase = os.environ.get('CONFIG_BASE_PATH')
    if not cbase:
        return from_json(rv, '', silent=silent)
    else:
        return from_json(rv, cbase, silent=silent)

