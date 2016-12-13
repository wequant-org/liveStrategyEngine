#!/usr/bin/env python
# -*- coding: utf-8 -*-

class WQLogger(object):
    def __init__(self, timeLogger):
        self.timeLogger = timeLogger

    def set_level(self, level):
        self.timeLogger.setLevel(level)

    def info(self, message):
        self.timeLogger.info(message)

    def warn(self, message):
        self.timeLogger.warn(message)

    def error(self, message):
        self.timeLogger.error(message)

    def debug(self, message):
        self.timeLogger.debug(message)
