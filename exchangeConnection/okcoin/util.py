#!/usr/bin/env python
# -*- coding: utf-8 -*-

import accountConfig
from exchangeConnection.okcoin.okcoinFutureAPI import OKCoinFuture
from exchangeConnection.okcoin.okcoinSpotAPI import OKCoinSpot

# 初始化ACCESS_KEY, SECRET_KEY, SERVICE_API
ACCESS_KEY = accountConfig.OKCOIN["CNY_1"]["ACCESS_KEY"]
SECRET_KEY = accountConfig.OKCOIN["CNY_1"]["SECRET_KEY"]
SERVICE_API = accountConfig.OKCOIN["CNY_1"]["SERVICE_API"]


# 现货API
def getOkcoinSpot():
    return OKCoinSpot(SERVICE_API, ACCESS_KEY, SECRET_KEY)


# 期货API
def getOkcoinFuture():
    return OKCoinFuture(SERVICE_API, ACCESS_KEY, SECRET_KEY)
