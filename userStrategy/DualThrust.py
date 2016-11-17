#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

'''
追涨杀跌策略: Dual Thrust 此策略是一种典型的趋势策略，基本思路是，短期内，价格突破一定的上限后，我们认为形成了一个上升趋势，价格短时间内会继续往上走；相反，短时间内，价格跌破一定的下限后，我们认为形成了一个下跌趋势，价格短时间内会继续往下走。

策略实现：
根据一段时间内的最高价，最低价和收盘价，计算出一个价格上下限。
当前价格突破上限时，全仓买入；当价格突破下线时，全仓卖出。
加入了止盈止损机制。
'''

'''
================================================================================
总体回测前
================================================================================
'''

# 回测阶段的策略配置，跑实盘的时候，所有Params中的配置都会被覆盖
PARAMS = {
    "start_time": "2016-09-20 00:00:00",  # 回测起始时间
    "end_time": "2016-10-21 00:00:00",  # 回测结束时间
    "slippage": 0.02,  # 设置滑点
    "account_initial": {"huobi_cny_cash": 10000,
                        "huobi_cny_btc": 3},  # 设置账户初始状态
}


# 初始化回测设置
def initialize(context):
    # 以日为单位进行回测
    context.frequency = "1d"
    # 设定以比特币为基准
    context.benchmark = "huobi_cny_btc"
    # 设定操作的标的为比特币
    context.security = "huobi_cny_btc"

    # 设置策略参数
    # 计算HH,HC,LC,LL所需的历史bar数目，用户自定义的变量，可以被handle_data使用;如果只需要看之前1根bar，则定义window_size=1
    context.user_data.window_size = 1
    # 用户自定义的变量，可以被handle_data使用，触发多头的range
    context.user_data.K1 = 1.2
    # 用户自定义的变量，可以被handle_data使用，触发空头的range.当K1<K2时，多头相对容易被触发,当K1>K2时，空头相对容易被触发
    context.user_data.K2 = 1.1
    # 止损线，用户自定义的变量，可以被handle_data使用
    context.user_data.portfolio_stop_loss = 0.75
    # 用户自定义变量，记录下是否已经触发止损
    context.user_data.stop_loss_triggered = False
    # 止盈线，用户自定义的变量，可以被handle_data使用
    context.user_data.portfolio_stop_win = 1.5
    # 用户自定义变量，记录下是否已经触发止盈
    context.user_data.stop_win_triggered = False


'''
================================================================================
开始回测
================================================================================
'''


# 根据设定的context.frequency每个时间单位调用一次
def handle_data(context):
    # 若已触发止盈/止损线，不会有任何操作
    if context.user_data.stop_loss_triggered:
        context.log.warn("已触发止损线, 此bar不会有任何指令 ... ")
        return
    if context.user_data.stop_win_triggered:
        context.log.info("已触发止盈线, 此bar不会有任何指令 ... ")
        return

    # 检查是否到达止损线或者止盈线
    if context.account.huobi_cny_net < context.user_data.portfolio_stop_loss * context.account_initial.huobi_cny_net or context.account.huobi_cny_net > context.user_data.portfolio_stop_win * context.account_initial.huobi_cny_net:
        should_stopped = True
    else:
        should_stopped = False

    # 如果有止盈/止损信号，则强制平仓，并结束所有操作
    if should_stopped:
        # 低于止损线，需要止损
        if context.account.huobi_cny_net < context.user_data.portfolio_stop_loss * context.account_initial.huobi_cny_net:
            context.log.warn(
                "当前净资产:%.2f 位于止损线下方 (%f), 初始资产:%.2f, 触发止损动作",
                context.account.huobi_cny_net, context.user_data.portfolio_stop_loss,
                context.account_initial.huobi_cny_net)
            context.user_data.stop_loss_triggered = True
        # 高于止盈线，需要止盈
        else:
            context.log.warn(
                "当前净资产:%.2f 位于止盈线上方 (%f), 初始资产:%.2f, 触发止盈动作",
                context.account.huobi_cny_net, context.user_data.portfolio_stop_win,
                context.account_initial.huobi_cny_net)
            context.user_data.stop_win_triggered = True

        if context.user_data.stop_loss_triggered:
            context.log.info("设置 stop_loss_triggered（已触发止损信号）为真")
        else:
            context.log.info("设置 stop_win_triggered （已触发止损信号）为真")

        # 需要止盈/止损，卖出全部持仓
        if getattr(context.account, context.security) > 0:
            # 卖出时，全仓清空
            context.log.info("正在卖出 %s" % context.security)
            context.order.sell(context.security, quantity=str(getattr(context.account, context.security)))
        return

    # 获取历史数据, 取后window_size+1根bar
    hist = context.data.get_price(context.security, count=context.user_data.window_size + 1, frequency=context.frequency)
    # 判断读取数量是否正确
    if len(hist.index) < (context.user_data.window_size + 1):
        context.log.warn("bar的数量不足, 等待下一根bar...")
        return

    # 取得最近1 根 bar的close价格
    latest_close_price = context.data.get_current_price(context.security).iloc[0]['price']

    # 开始计算N日最高价的最高价HH，N日收盘价的最高价HC，N日收盘价的最低价LC，N日最低价的最低价LL
    hh = np.max(hist['high'][-1 * (context.user_data.window_size + 1):-1])
    hc = np.max(hist['close'][-1 * (context.user_data.window_size + 1):-1])
    lc = np.min(hist['close'][-1 * (context.user_data.window_size + 1):-1])
    ll = np.min(hist['low'][-1 * (context.user_data.window_size + 1):-1])
    price_range = max(hh - lc, hc - ll)

    # 取得倒数第二根bar的close, 并计算上下界限
    up_bound = hist['close'][-2] + context.user_data.K1 * price_range
    low_bound = hist['close'][-2] - context.user_data.K2 * price_range

    # 产生买入卖出信号，并执行操作
    if latest_close_price > up_bound:
        if context.account.huobi_cny_cash > 0:
            # 有买入信号，且持有现金，则市价单全仓买入
            context.log.info("正在买入 %s" % context.security)
            context.order.buy(context.security, cash_amount=str(context.account.huobi_cny_cash))
    elif latest_close_price < low_bound:
        if getattr(context.account, context.security) > 0:
            # 有卖出信号，且持有仓位，则市价单全仓卖出
            context.log.info("正在卖出 %s" % context.security)
            context.order.sell(context.security, quantity=str(getattr(context.account, context.security)))
