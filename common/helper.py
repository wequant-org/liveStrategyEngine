#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################
#   获取更多免费策略，请加入WeQuant比特币量化策略交流QQ群：519538535
#   群主邮箱：lanjason@foxmail.com，群主微信/QQ：64008672
#   沉迷量化，无法自拔
###############################################################

import json
import math

coinTypeStructure = {
    "btc_cny" : {
        "huobi" : {
            "coin_type" : 1,
            "market"    : "cny",
            "coin_str"  : "huobi_btc",
            "market_str" : "huobi_cny",
            "pricer_str" : "huobi-cnybtc"
        },
        "okcoin" : {
            "coin_type" : "btc_cny",
            "market"    : "cny",
            "coin_str"  : "okcoin_btc",
            "market_str" : "okcoin_cny",
        }
    },
    "ltc_cny" : {
        "huobi" : {
            "coin_type" : 2,
            "market"    : "cny",
            "coin_str"  : "huobi_ltc",
            "market_str" : "huobi_cny",
            "pricer_str" : "huobi-cnyltc"
        },
        "okcoin" : {
            "coin_type" : "ltc_cny",
            "market"    : "cny",
            "coin_str"  : "okcoin_ltc",
            "market_str" : "okcoin_cny",
        }
    }
}

COIN_TYPE_BTC_CNY = "btc_cny"
COIN_TYPE_LTC_CNY = "ltc_cny"

def getDictFromJSONString(str):
    return json.loads(str)

def getRoundedQuantity(qty, coin_type):
    if coin_type == COIN_TYPE_BTC_CNY:
        #按照okcoin的下单规则，比特币都是0.01btc的整数倍，取下限
        return int(qty*100)/100
    elif coin_type == COIN_TYPE_LTC_CNY:
        #按照okcoin的下单规则，莱特币都是0.1ltc的整数倍，取下限
        return int(qty*10)/10
    else:
        raise ValueError( "invalid coin type %s" % coin_type)


def myRound(qty, decimal_places=4):
    return int(qty * math.pow(10, decimal_places))/int(math.pow(10,decimal_places))
