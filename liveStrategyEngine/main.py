#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import userStrategy.SimpleMA as SimpleMA
from liveStrategyEngine.BaseLiveStrategyEngine import BaseLiveStrategyEngine

if __name__ == "__main__":
    #simpleMA
    strat = BaseLiveStrategyEngine( SimpleMA,datetime.datetime.now(), 0.1, 30, dailyExitTime="23:30:00")
    strat.go()

