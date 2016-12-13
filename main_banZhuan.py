#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################
#   获取更多免费策略，请加入WeQuant比特币量化策略交流QQ群：519538535
#   群主邮箱：lanjason@foxmail.com，群主微信/QQ：64008672
#   沉迷量化，无法自拔
###############################################################

from banZhuan.fixedSpreadArbStrategy import *
from utils.helper import *

if __name__ == "__main__":
    strat = FixedSpreadSignalGenerator(datetime.datetime.now(), 0.8, 1, 0.1, 60, helper.COIN_TYPE_BTC_CNY, 0.003, 0.001,
                                       maximum_qty_multiplier=3)

    # LTC
    # strat = FixedSpreadSignalGenerator(datetime.datetime.now(), 0.8, 1, 0.1, 60, helper.COIN_TYPE_LTC_CNY, 0.003, 0.001,
    #                                   maximum_qty_multiplier=3)

    start_strat(strat)
