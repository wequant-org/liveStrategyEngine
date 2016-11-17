#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
#import userStrategy.SimpleMA as SimpleMA
#import userStrategy.SeaTurtle as SeaTurtle
#import userStrategy.Grid as Grid
#import userStrategy.FixedPosValueGrowth as FixedPosValueGrowth
import userStrategy.DualThrust as DualThrust
from liveStrategyEngine.BaseLiveStrategyEngine import BaseLiveStrategyEngine

if __name__ == "__main__":

    '''
    #simpleMA
    strat = BaseLiveStrategyEngine( SimpleMA,datetime.datetime.now(), 0.1, 30, dailyExitTime="23:30:00")
    strat.go()
    '''

    '''
    #SeaTurtle
    strat = BaseLiveStrategyEngine( SeaTurtle,datetime.datetime.now(), 0.1, 30, dailyExitTime="23:30:00")
    strat.go()
    '''

    '''
    #网格策略
    strat = BaseLiveStrategyEngine( Grid,datetime.datetime.now(), 0.1, 30, dailyExitTime="23:30:00")
    strat.go()
    '''

    '''
    #价值定投策略
    strat = BaseLiveStrategyEngine( FixedPosValueGrowth,datetime.datetime.now(), 0.1, 30, dailyExitTime="23:30:00")
    strat.go()
    '''

    # DualThrust追涨杀跌策略
    strat = BaseLiveStrategyEngine(DualThrust, datetime.datetime.now(), 0.1, 30, dailyExitTime="23:30:00")
    strat.go()







