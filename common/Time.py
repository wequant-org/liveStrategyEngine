#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################
#   获取更多免费策略，请加入WeQuant比特币量化策略交流QQ群：519538535
#   群主邮箱：lanjason@foxmail.com，群主微信/QQ：64008672
#   沉迷量化，无法自拔
###############################################################

import datetime


class Time(object):
    def __init__(self, startRunningTime):
        self.startRunningTime = startRunningTime

    def get_current_time(self):
        return datetime.datetime.now()

    def get_current_bar_time(self):
        # TODO：to implement the accurate get_current_bar_time function
        return self.get_current_time()

    def get_start_time(self):
        # TODO：to implement the accurate get_start_time function
        return self.startRunningTime

    def get_start_bar_time(self):
        # TODO：to implement the accurate get_start_bar_time function
        return self.get_start_time()
