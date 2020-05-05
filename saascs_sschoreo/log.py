#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 26 17:52:42 2020

@author: mugopala
"""

import logging
import logging.handlers
import sys


root_logger = None

def _setup_debug_logging(appcfg):
    """Set up logging for debug.

    All logs goes to the root logger, which output to stdout.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(appcfg['log_level'])
    root_logger.handlers = []
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(appcfg['log_level'])
    formatter = logging.Formatter(appcfg['log_format'],
                                  datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    _app_logger = logging.getLogger('saascs_choreographer')
    _app_logger.setLevel(appcfg['log_level'])
    _app_logger.handlers = []

    return _app_logger



def _setup_prod_logging(appcfg):
    """Set up logging for production.

    Following logs are produced:
    1. root log: all logs will go to here.
    2. application log: application specific logs.
    """
    logging.basicConfig(level=appcfg['log_level'],
                        format=appcfg['log_format'],
                        )

    # Files are rotated by the SaaScs_rbws log rotation script.

    # Set up root logger.
    root_logger = logging.getLogger()
    root_logger.setLevel(appcfg['log_level'])

    root_logger.handlers = []
    root_handler = _create_handler(
        appcfg['root_log_file'], appcfg, appcfg['log_format'],
        logging.handlers.WatchedFileHandler)
    root_logger.addHandler(root_handler)

    # Set up application logger.
    _app_logger = logging.getLogger('saascs_choreographer')
    _app_logger.setLevel(appcfg['log_level'])
    _app_handler = _create_handler(
        appcfg['app_log_file'], appcfg, appcfg['log_format'])
    _app_logger.handlers = []
    _app_logger.addHandler(_app_handler)
    return _app_logger


def _create_handler(filename, config, format=None, cls=logging.FileHandler):
    handler = cls(filename)
    handler.setLevel(config['log_level'])
    formatter = logging.Formatter(format, datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    return handler


def setup_logging(appcfg, isdebug=False):
    """Setup logging for debug and production"""
    if isdebug:
        return _setup_debug_logging(appcfg)
    else:
        return _setup_prod_logging(appcfg)