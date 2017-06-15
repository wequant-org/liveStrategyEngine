#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2017-05-16 15:40:03
# @Author  : Ryan (tech@huobi.com)
# @Link    : https://www.huobi.com
# @Version : $Id$

from utilETH import *

'''
Market data API
'''


# 获取KLine
def get_kline(symbol, period, long_polling=None):
    """
    :param symbol: 可选值：{ ethcny }
    :param period: 可选值：{1min, 5min, 15min, 30min, 60min, 1day, 1mon, 1week, 1year }
    :param long_polling: 可选值： { true, false }
    :return:
    """
    params = {'symbol': symbol,
              'period': period}

    if long_polling:
        params['long-polling'] = long_polling
    url = MARKET_URL + '/market/kline'
    return http_get_request(url, params)


# 获取marketdepth
def get_depth(symbol, type, long_polling=None):
    """
    :param symbol: 可选值：{ ethcny }
    :param type: 可选值：{ percent10, step0, step1, step2, step3, step4, step5 }
    :param long_polling: 可选值： { true, false }
    :return:
    """
    params = {'symbol': symbol,
              'type': type}

    if long_polling:
        params['long-polling'] = long_polling
    url = MARKET_URL + '/market/depth'
    return http_get_request(url, params)


# 获取tradedetail
def get_trade(symbol, long_polling=None):
    """
    :param symbol: 可选值：{ ethcny }
    :param long_polling: 可选值： { true, false }
    :return:
    """
    params = {'symbol': symbol}
    if long_polling:
        params['long-polling'] = long_polling
    url = MARKET_URL + '/market/trade'
    return http_get_request(url, params)


# 获取 Market Detail 24小时成交量数据
def get_detail(symbol, long_polling=None):
    """
    :param symbol: 可选值：{ ethcny }
    :param long_polling: 可选值： { true, false }
    :return:
    """
    params = {'symbol': symbol}
    if long_polling:
        params['long-polling'] = long_polling
    url = MARKET_URL + '/market/detail'
    return http_get_request(url, params)

'''
Trade/Account API
'''


def get_accounts():
    """
    :return: 
    """
    path = "/v1/account/accounts"
    params = {}
    return api_key_get(params, path)


# 获取当前账户资产
def get_balance(acct_id=None):
    """
    :param acct_id
    :return:
    """

    if not acct_id:
        accounts = get_accounts()
        acct_id = accounts['data'][0]['id'];

    url = "/v1/account/accounts/{0}/balance".format(acct_id)
    params = {"account-id": acct_id}
    return api_key_get(params, url)


# 下单
def orders(amount, source, symbol, _type, price=0):
    """
    
    :param amount: 
    :param source: 
    :param symbol: 
    :param _type: 可选值 {buy-market：市价买, sell-market：市价卖, buy-limit：限价买, sell-limit：限价卖}
    :param price: 
    :return: 
    """
    accounts = get_accounts()
    acct_id = accounts['data'][0]['id'];

    params = {"account-id": acct_id,
              "amount": amount,
              "symbol": symbol,
              "type": _type,
              "source": source}
    if price:
        params["price"] = price

    url = "/v1/order/orders"
    return api_key_post(params, url)


# 执行订单
def place_order(order_id):
    """
    
    :param order_id: 
    :return: 
    """
    params = {}
    url = "/v1/order/orders/{0}/place".format(order_id)
    return api_key_post(params, url)


# 撤销订单
def cancel_order(order_id):
    """
    
    :param order_id: 
    :return: 
    """
    params = {}
    url = "/v1/order/orders/{0}/submitcancel".format(order_id)
    return api_key_post(params, url)


# 查询某个订单
def order_info(order_id):
    """
    
    :param order_id: 
    :return: 
    """
    params = {}
    url = "/v1/order/orders/{0}".format(order_id)
    return api_key_get(params, url)


# 查询某个订单的成交明细
def order_matchresults(order_id):
    """
    
    :param order_id: 
    :return: 
    """
    params = {}
    url = "/v1/order/orders/{0}/matchresults".format(order_id)
    return api_key_get(params, url)


# 查询当前委托、历史委托
def orders_list(symbol, states, types=None, start_date=None, end_date=None, _from=None, direct=None, size=None):
    """
    
    :param symbol: 
    :param states: 可选值 {pre-submitted 准备提交, submitted 已提交, partial-filled 部分成交, partial-canceled 部分成交撤销, filled 完全成交, canceled 已撤销}
    :param types: 可选值 {buy-market：市价买, sell-market：市价卖, buy-limit：限价买, sell-limit：限价卖}
    :param start_date: 
    :param end_date: 
    :param _from: 
    :param direct: 可选值{prev 向前，next 向后}
    :param size: 
    :return: 
    """
    params = {'symbol': symbol,
              'states': states}

    if types:
        params[types] = types
    if start_date:
        params['start-date'] = start_date
    if end_date:
        params['end-date'] = end_date
    if _from:
        params['from'] = _from
    if direct:
        params['direct'] = direct
    if size:
        params['size'] = size
    url = '/v1/order/orders'
    return api_key_get(params, url)


# 查询当前成交、历史成交
def orders_matchresults(symbol, types=None, start_date=None, end_date=None, _from=None, direct=None, size=None):
    """
    
    :param symbol: 
    :param types: 可选值 {buy-market：市价买, sell-market：市价卖, buy-limit：限价买, sell-limit：限价卖}
    :param start_date: 
    :param end_date: 
    :param _from: 
    :param direct: 可选值{prev 向前，next 向后}
    :param size: 
    :return: 
    """
    params = {'symbol': symbol}

    if types:
        params[types] = types
    if start_date:
        params['start-date'] = start_date
    if end_date:
        params['end-date'] = end_date
    if _from:
        params['from'] = _from
    if direct:
        params['direct'] = direct
    if size:
        params['size'] = size
    url = '/v1/order/matchresults'
    return api_key_get(params, url)


# 查询虚拟币提现地址
def get_withdraw_address(currency):
    """
    
    :param currency: 
    :return: 
    """
    params = {'currency': currency}
    url = '/v1/dw/withdraw-virtual/addresses'
    return api_key_get(params, url)


# 申请提现虚拟币
def withdraw(address_id, amount):
    """
    
    :param address_id: 
    :param amount: 
    :return: 
    """
    params = {'address-id': address_id,
              'amount': amount}
    url = '/v1/dw/withdraw-virtual/create'
    return api_key_post(params, url)


# 确认申请虚拟币提现
def place_withdraw(address_id):
    """
    
    :param address_id: 
    :return: 
    """
    params = {}
    url = '/v1/dw/withdraw-virtual/{0}/place'.format(address_id)
    return api_key_post(params, url)


# 申请取消提现虚拟币
def cancel_withdraw(address_id):
    """
    
    :param address_id: 
    :return: 
    """
    params = {}
    url = '/v1/dw/withdraw-virtual/{0}/cancel'.format(address_id)
    return api_key_post(params, url)
