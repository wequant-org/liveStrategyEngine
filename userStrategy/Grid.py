#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

'''
网格策略是一种旨在达到低吸高抛的策略，主要思想就是在股价比设定的基准价下跌时逐渐加仓，而上涨时逐渐减仓网格交易策略，是一种带有仓位控制的高抛低吸策略。在价格低于基准价时逐渐建仓，高于基准价时逐渐减仓。

策略实现：
本策略设置买卖价格各4档，在不同价格上设置不同的仓位，一旦价格达到某一档位，则将当前仓位调至该档位对应的预设仓位。
加入止盈和止损机制。
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
    # 底仓价格
    context.user_data.base_price = None
    # 计算移动均值所需的历史bar数目，用户自定义的变量，可以被handle_data使用
    context.user_data.sma_window_size = 20
    # 确定当前price可否作为base_price的依据就是当前price是否小于20日均线*price_to_sma_threshold
    context.user_data.price_to_sma_threshold = 0.85
    # 止损线，用户自定义的变量，可以被handle_data使用
    context.user_data.portfolio_stop_loss = 0.75
    # 用户自定义变量，记录下是否已经触发止损
    context.user_data.stop_loss_triggered = False
    # 止盈线，用户自定义的变量，可以被handle_data使用
    context.user_data.portfolio_stop_win = 1.5
    # 用户自定义变量，记录下是否已经触发止盈
    context.user_data.stop_win_triggered = False
    # 设置网格的4个档位的买入价格（相对于基础价的百分比）
    context.user_data.buy4, context.user_data.buy3, context.user_data.buy2, context.user_data.buy1 = 0.88, 0.91, 0.94, 0.97
    # 设置网格的4个档位的卖出价格（相对于基础价的百分比）
    context.user_data.sell4, context.user_data.sell3, context.user_data.sell2, context.user_data.sell1 = 1.2, 1.15, 1.1, 1.05


'''
================================================================================
开始回测
================================================================================
'''


# 计算为达到目标仓位所需要购买的金额
def cash_to_spent_fn(net_asset, target_ratio, available_cny):
    return available_cny - net_asset * (1 - target_ratio)


# 根据设定的context.frequency每个时间单位调用一次
def handle_data(context):
    if context.user_data.stop_loss_triggered:
        context.log.warn("已触发止损线, 此bar不会有任何指令 ... ")
        return

    if context.user_data.stop_win_triggered:
        context.log.info("已触发止盈线, 此bar不会有任何指令 ... ")
        return

    # 检查是否到达止损线或者止盈线，如果是，强制平仓，并结束所有操作
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

        # 有止盈/止损，且当前有仓位，则强平所有仓位
        if getattr(context.account, context.security) > 0:
            context.log.info("正在卖出 %s" % context.security)
            context.order.sell(context.security, quantity=str(getattr(context.account, context.security)))
        return

    # 获取当前价格
    price = context.data.get_current_price(context.security)

    # 设置网格策略基础价格（base_price)
    if context.user_data.base_price is None:
        # 获取历史数据, 取后sma_window_size根bar
        hist = context.data.get_price(context.security, count=context.user_data.sma_window_size, frequency="1d")
        if len(hist.index) < context.user_data.sma_window_size:
            context.log.warn("bar的数量不足, 等待下一根bar...")
            return
        # 计算sma均线值
        sma = np.mean(hist['close'][-1 * context.user_data.sma_window_size:])
        # 若当前价格满足条件，则设置当前价格为基础价
        if price < context.user_data.price_to_sma_threshold * sma and context.user_data.base_price is None:
            context.user_data.base_price = price

    # 还没有找到base_price，则继续找，不着急建仓
    if context.user_data.base_price is None:
        return

    cash_to_spent = 0

    # 计算为达到目标仓位需要买入/卖出的金额
    # 价格低于buy4所对应的价格时，仓位调至100%
    if price / context.user_data.base_price < context.user_data.buy4:
        cash_to_spent = cash_to_spent_fn(context.account.huobi_cny_net, 1, context.account.huobi_cny_cash)
    # 价格大于等于buy4对应的价格，低于buy3所对应的价格时，仓位调至90%
    elif price / context.user_data.base_price < context.user_data.buy3:
        cash_to_spent = cash_to_spent_fn(context.account.huobi_cny_net, 0.9, context.account.huobi_cny_cash)
    # 价格大于等于buy3对应的价格，低于buy2所对应的价格时，仓位调至70%
    elif price / context.user_data.base_price < context.user_data.buy2:
        cash_to_spent = cash_to_spent_fn(context.account.huobi_cny_net, 0.7, context.account.huobi_cny_cash)
    # 价格大于等于buy2对应的价格，低于buy1所对应的价格时，仓位调至40%
    elif price / context.user_data.base_price < context.user_data.buy1:
        cash_to_spent = cash_to_spent_fn(context.account.huobi_cny_net, 0.4, context.account.huobi_cny_cash)
    # 价格大于sell4对应的价格，仓位调至0%
    elif price / context.user_data.base_price > context.user_data.sell4:
        cash_to_spent = cash_to_spent_fn(context.account.huobi_cny_net, 0, context.account.huobi_cny_cash)
    # 价格小于等于sell4对应的价格，大于sell3所对应的价格时，仓位调至10%
    elif price / context.user_data.base_price > context.user_data.sell3:
        cash_to_spent = cash_to_spent_fn(context.account.huobi_cny_net, 0.1, context.account.huobi_cny_cash)
    # 价格小于等于sell3对应的价格，大于sell2所对应的价格时，仓位调至30%
    elif price / context.user_data.base_price > context.user_data.sell2:
        cash_to_spent = cash_to_spent_fn(context.account.huobi_cny_net, 0.3, context.account.huobi_cny_cash)
    # 价格小于等于sell2对应的价格，大于sell1所对应的价格时，仓位调至60%
    elif price / context.user_data.base_price > context.user_data.sell1:
        cash_to_spent = cash_to_spent_fn(context.account.huobi_cny_net, 0.6, context.account.huobi_cny_cash)


    # 根据策略调整仓位
    if cash_to_spent > 0:
        #  市价单买入一定金额
        context.log.info("正在买入 %s" % context.security)
        context.order.buy(context.security, cash_amount=str(cash_to_spent))
    elif cash_to_spent < 0:
        #  计算需要卖出的数量，并已市价单卖出
        quantity = min(getattr(context.account, context.security), -1 * cash_to_spent / price)
        context.log.info("正在卖出 %s" % context.security)
        context.order.sell(context.security, quantity=str(quantity))
