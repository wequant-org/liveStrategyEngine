#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################
#   获取更多免费策略，请加入WeQuant比特币量化策略交流QQ群：519538535
#   群主邮箱：lanjason@foxmail.com，群主微信/QQ：64008672
#   沉迷量化，无法自拔
###############################################################

import json
import math

COIN_TYPE_BTC_CNY = "btc_cny"
COIN_TYPE_LTC_CNY = "ltc_cny"
HUOBI_COIN_TYPE_BTC = 1
HUOBI_COIN_TYPE_LTC = 2

coinTypeStructure = {
    COIN_TYPE_BTC_CNY : {
        "huobi" : {
            "coin_type" : HUOBI_COIN_TYPE_BTC,
            "market"    : "cny",
            "coin_str"  : "huobi_cny_btc",
            "market_str" : "huobi_cny_cash"
        },
        "okcoin" : {
            "coin_type" : COIN_TYPE_BTC_CNY,
            "market"    : "cny",
            "coin_str"  : "okcoin_cny_btc",
            "market_str" : "okcoin_cny_cash"
        }
    },
    COIN_TYPE_LTC_CNY : {
        "huobi" : {
            "coin_type" : HUOBI_COIN_TYPE_LTC,
            "market"    : "cny",
            "coin_str"  : "huobi_cny_ltc",
            "market_str" : "huobi_cny_cash"
        },
        "okcoin" : {
            "coin_type" : COIN_TYPE_LTC_CNY,
            "market"    : "cny",
            "coin_str"  : "okcoin_cny_ltc",
            "market_str" : "okcoin_cny_cash"
        }
    }
}


def getDictFromJSONString(str):
    return json.loads(str)

def getRoundedQuantity(qty, coin_type):
    if coin_type == COIN_TYPE_BTC_CNY:
        #按照okcoin的下单规则，比特币都是0.01 btc的整数倍，取下限
        return int(qty*100)/100
    elif coin_type == COIN_TYPE_LTC_CNY:
        #按照okcoin的下单规则，莱特币都是0.1 ltc的整数倍，取下限
        return int(qty*10)/10
    else:
        raise ValueError( "invalid coin type %s" % coin_type)


def myRound(qty, decimal_places=4):
    return int(qty * math.pow(10, decimal_places))/int(math.pow(10,decimal_places))

