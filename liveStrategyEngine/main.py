#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import userStrategy.SimpleMA as SimpleMA
from liveStrategyEngine.BaseLiveStrategyEngine import BaseLiveStrategyEngine

if __name__ == "__main__":
    '''
    # btc
    strat = BanzhuanStrategy(datetime.datetime.now(), 0.8, 1, 0.1, 30, helper.COIN_TYPE_BTC_CNY, dailyExitTime="23:30:00")
    strat.go()
    '''

    '''
    # ltc
    strat = BanzhuanStrategy(datetime.datetime.now(), 0.8, 1, 0.1, 30, helper.COIN_TYPE_LTC_CNY, dailyExitTime="23:30:00")
    strat.go()
    '''

    #simpleMA
    strat = BaseLiveStrategyEngine( SimpleMA,datetime.datetime.now(), 0.1, 30, dailyExitTime="23:30:00")
    strat.go()

