# !/usr/bin/env python
# -*- coding: utf-8 -*-


import userStrategy.DualThrust as DualThrust
from liveStrategyEngine.BaseLiveStrategyEngine import BaseLiveStrategyEngine
from utils.helper import *

if __name__ == "__main__":
    '''
    #simpleMA
    strat = BaseLiveStrategyEngine( SimpleMA,datetime.datetime.now(), 0.1, 30, dailyExitTime="23:30:00")
    '''

    '''
    #SeaTurtle
    strat = BaseLiveStrategyEngine( SeaTurtle,datetime.datetime.now(), 0.1, 30, dailyExitTime="23:30:00")
    '''

    '''
    #网格策略
    strat = BaseLiveStrategyEngine( Grid,datetime.datetime.now(), 0.1, 30, dailyExitTime="23:30:00")
    '''

    '''
    #价值定投策略
    strat = BaseLiveStrategyEngine( FixedPosValueGrowth,datetime.datetime.now(), 0.1, 30, dailyExitTime="23:30:00")
    '''

    # DualThrust追涨杀跌策略
    strat = BaseLiveStrategyEngine(DualThrust, datetime.datetime.now(), 0.1, 30, dailyExitTime="23:30:00")

    start_strat(strat)
