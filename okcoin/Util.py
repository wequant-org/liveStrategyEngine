#!/usr/bin/python
# -*- coding: utf-8 -*-

###############################################################
#   获取更多免费策略，请加入WeQuant比特币量化策略交流QQ群：519538535
#   群主邮箱：lanjason@foxmail.com，群主微信/QQ：64008672
#   沉迷量化，无法自拔
###############################################################

import okcoin.Config as config
from okcoin.OkcoinFutureAPI import OKCoinFuture
from okcoin.OkcoinSpotAPI import OKCoinSpot

# 初始化apikey，secretkey,url
apikey = config.apikey
secretkey = config.secretkey
okcoinRESTURL = config.okcoinRESTURL

# 现货API
def getOkcoinSpot():
    return OKCoinSpot(okcoinRESTURL, apikey, secretkey)


# 期货API
def getOkcoinFuture():
    return OKCoinFuture(okcoinRESTURL, apikey, secretkey)
