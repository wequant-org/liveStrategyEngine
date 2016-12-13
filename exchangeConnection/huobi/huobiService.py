#!/usr/bin/env python
# -*- coding: utf-8 -*-

from exchangeConnection.huobi.util import *
from utils.helper import *

'''
获取账号详情
'''


def getAccountInfo(market, method):
    params = {"method": method}
    extra = {}
    extra['market'] = market
    res = send2api(params, extra)
    return res


'''
获取所有正在进行的委托
'''


def getOrders(coinType, market, method):
    params = {"method": method}
    params['coin_type'] = coinType
    extra = {}
    extra['market'] = market
    res = send2api(params, extra)
    return res


'''
获取订单详情
@param coinType
@param id
'''


def getOrderInfo(coinType, id, market, method):
    params = {"method": method}
    params['coin_type'] = coinType
    params['id'] = id
    extra = {}
    extra['market'] = market
    res = send2api(params, extra)
    return res


'''
限价买入
@param coinType
@param price
@param amount
@param tradePassword
@param tradeid
@param method
'''


def buy(coinType, price, amount, tradePassword, tradeid, market, method):
    params = {"method": method}
    params['coin_type'] = coinType
    params['price'] = price
    params['amount'] = amount
    extra = {}
    extra['trade_password'] = tradePassword
    extra['trade_id'] = tradeid
    extra['market'] = market
    res = send2api(params, extra)
    return res


'''
限价卖出
@param coinType
@param price
@param amount
@param tradePassword
@param tradeid
'''


def sell(coinType, price, amount, tradePassword, tradeid, market, method):
    params = {"method": method}
    params['coin_type'] = coinType
    params['price'] = price
    params['amount'] = amount
    extra = {}
    extra['trade_password'] = tradePassword
    extra['trade_id'] = tradeid
    extra['market'] = market
    res = send2api(params, extra)
    return res


'''
市价买
@param coinType
@param amount
@param tradePassword
@param tradeid
'''


def buyMarket(coinType, amount, tradePassword, tradeid, market, method):
    params = {"method": method}
    params['coin_type'] = coinType
    params['amount'] = amount
    extra = {}
    extra['trade_password'] = tradePassword
    extra['trade_id'] = tradeid
    extra['market'] = market
    res = send2api(params, extra)
    return res


'''
市价卖出
@param coinType
@param amount
@param tradePassword
@param tradeid
'''


def sellMarket(coinType, amount, tradePassword, tradeid, market, method):
    params = {"method": method}
    params['coin_type'] = coinType
    params['amount'] = amount
    extra = {}
    extra['trade_password'] = tradePassword
    extra['trade_id'] = tradeid
    extra['market'] = market
    res = send2api(params, extra)
    return res


'''
查询个人最新10条成交订单
@param coinType
'''


def getNewDealOrders(coinType, market, method):
    params = {"method": method}
    params['coin_type'] = coinType
    extra = {}
    extra['market'] = market
    res = send2api(params, extra)
    return res


'''
根据trade_id查询oder_id
@param coinType
@param tradeid
'''


def getOrderIdByTradeId(coinType, tradeid, market, method):
    params = {"method": method}
    params['coin_type'] = coinType
    params['trade_id'] = tradeid
    extra = {}
    extra['market'] = market
    res = send2api(params, extra)
    return res


'''
撤销订单
@param coinType
@param id
'''


def cancelOrder(coinType, id, market, method):
    params = {"method": method}
    params['coin_type'] = coinType
    params['id'] = id
    extra = {}
    extra['market'] = market
    res = send2api(params, extra)
    return res


'''
获取实时行情
@param coinType #币种 1 比特币 2 莱特币
'''


def getTicker(coinType, market):
    if market == COIN_TYPE_CNY:
        if coinType == HUOBI_COIN_TYPE_BTC:
            url = "http://api.huobi.com/staticmarket/ticker_btc_json.js"
        else:
            url = "http://api.huobi.com/staticmarket/ticker_ltc_json.js"
    elif market == COIN_TYPE_USD:
        if coinType == HUOBI_COIN_TYPE_BTC:
            url = "http://api.huobi.com/usdmarket/ticker_btc_json.js"
        else:
            raise ValueError("invalid coinType %d for market %s" % (coinType, market))
    else:
        raise ValueError("invalid market %s" % market)
    return httpRequest(url, {})


'''
获取实时行情
@param coinType:币种 1 比特币 2 莱特币
@param depth_size:指定深度
'''


def getDepth(coinType, market, depth_size=5):
    if market == COIN_TYPE_CNY:
        if coinType == HUOBI_COIN_TYPE_BTC:
            url = "http://api.huobi.com/staticmarket/depth_btc_" + str(depth_size) + ".js"
        else:
            url = "http://api.huobi.com/staticmarket/depth_ltc_" + str(depth_size) + ".js"
    elif market == COIN_TYPE_USD:
        if coinType == HUOBI_COIN_TYPE_BTC:
            url = "http://api.huobi.com/usdmarket/depth_btc_" + str(depth_size) + ".js"
        else:
            raise ValueError("invalid coinType %d for market %s" % (coinType, market))
    else:
        raise ValueError("invalid market %s" % market)
    return httpRequest(url, {})


'''
获取最少订单数量
@param coinType:币种 1 比特币 2 莱特币
火币上比特币交易及莱特币交易都是0.0001的整数倍
比特币最小交易数量：0.001,莱特币最小交易数量：0.01
'''


def getMinimumOrderQty(coinType):
    if coinType == HUOBI_COIN_TYPE_BTC:
        return 0.001
    else:
        return 0.01


'''
获取最少交易金额
火币上比特币交易及莱特币交易金额都是0.01的整数倍
最小交易金额：1
'''


def getMinimumOrderCashAmount():
    return 1
