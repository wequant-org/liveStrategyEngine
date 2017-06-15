#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2017-05-16 15:29:19
# @Author  : Ryan (tech@huobi.com)
# @Link    : https://www.huobi.com
# @Version : $Id$

from utilETH import *
import huobiServiceETH

if __name__ == '__main__':
    # print("获取1分钟线")
    # print(huobiServiceETH.get_kline('ethcny', '1min'))
    # print("获取合并深度为1的盘口")
    # print(huobiServiceETH.get_depth('ethcny', 'step1'))
    # print("获取Trade Detail")
    # print(huobiServiceETH.get_trade('ethcny'))
    # print("获取 Market Detail 24小时成交量数据")
    # print(huobiServiceETH.get_detail('ethcny'))
    print("获取当前账户资产")
    print(huobiServiceETH.get_balance())
    # print('下单')
    # print(huobiServiceETH.orders(1, 'api', 'ethcny', 'buy-limit', 12))
    # print('执行订单')
    # print(huobiServiceETH.place_order('58840'))
    # print('撤销订单')
    # print(huobiServiceETH.cancel_order('58840'))
    # print('查询某个订单')
    # print(huobiServiceETH.order_info('58840'))
    # print('查询某个订单的成交明细')
    # print(huobiServiceETH.order_matchresults('45421'))
    # print('查询当前委托、历史委托')
    # print(huobiServiceETH.orders_list('ethcny', 'submitted'))
    # print('查询当前成交、历史成交')
    # print(huobiServiceETH.orders_matchresults('ethcny'))
    # print('查询虚拟币提币地址')
    # print(huobiServiceETH.get_withdraw_address('eth'))


