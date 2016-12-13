#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
本程序在 Python 3.3.0 环境下测试成功
使用方法：python testHuobi.py
'''

import exchangeConnection.huobi.huobiService as HuobiService
from exchangeConnection.huobi.util import *
from utils.helper import *

if __name__ == "__main__":
    print("获取账号详情")
    print(HuobiService.getAccountInfo("cny", ACCOUNT_INFO))

    print(HuobiService.getAccountInfo("usd", ACCOUNT_INFO))

    print("real time market")
    t = HuobiService.getTicker(HUOBI_COIN_TYPE_BTC, "cny")
    print(t)
    # t.json()
    # print (t.ticker.buy)
    # print (t['ticker']['sell'])

    print("get depth")
    print(HuobiService.getDepth(HUOBI_COIN_TYPE_BTC, "cny", depth_size=1))

    print('order execution status')
    print(HuobiService.getOrderInfo(HUOBI_COIN_TYPE_LTC, 326711967, "cny", ORDER_INFO))

    '''
    print ("获取所有正在进行的委托")
    print (HuobiService.getOrders(1,GET_ORDERS))
    print ("获取订单详情")
    print (HuobiService.getOrderInfo(1,68278313,ORDER_INFO))
    print ("限价买入")
    print (HuobiService.buy(1,"1","0.01",None,None,BUY))
    print ("限价卖出")
    print (HuobiService.sell(2,"100","0.2",None,None,SELL))
    print ("市价买入")
    print (HuobiService.buyMarket(2,"30",None,None,BUY_MARKET))
    print ("市价卖出")
    print (HuobiService.sellMarket(2,"1.3452",None,None,SELL_MARKET))
    print ("查询个人最新10条成交订单")
    print (HuobiService.getNewDealOrders(1,NEW_DEAL_ORDERS))
    print ("根据trade_id查询order_id")
    print (HuobiService.getOrderIdByTradeId(1,274424,ORDER_ID_BY_TRADE_ID))
    print ("取消订单接口")
    print (HuobiService.cancelOrder(1,68278313,CANCEL_ORDER))
    '''
