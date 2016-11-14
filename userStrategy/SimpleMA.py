#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

'''
简单双均线策略，通过一短一长（一快一慢）两个回看时间窗口的平均收盘价绘制两条均线，利用均线的交叉来跟踪价格的趋势。

策略实现：
short_ma: 最近5个bar的价格均线
long_ma：最近20个bar的价格均线
当 short_ma 高于 long_ma 一段比例时，全仓买入；
当 short_ma 低于 long_ma 一段比利时，全仓卖出。

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
    # 以1分钟为单位进行回测
    context.frequency = "1m"
    # 设定以比特币为基准
    context.benchmark = "huobi_cny_btc"
    # 设定操作的标的为比特币
    context.security = "huobi_cny_btc"

    # 设置策略参数
    # 计算短线所需的历史bar数目，用户自定义的变量，可以被handle_data使用
    context.user_data.window_short = 5
    # 计算长线所需的历史bar数目，用户自定义的变量，可以被handle_data使用
    context.user_data.window_long = 20
    # 入场线, 用户自定义的变量，可以被handle_data使用
    context.user_data.enter_threshold = 0.05
    # 出场线, 用户自定义的变量，可以被handle_data使用
    context.user_data.exit_threshold = -0.05

'''
================================================================================
开始回测
================================================================================
'''


# 根据设定的context.frequency每个时间单位调用一次
def handle_data(context):
    # 获取历史数据, 取后window_long根bar
    hist = context.data.get_price(context.security, count=context.user_data.window_long, frequency=context.frequency)
    if len(hist.index) < context.user_data.window_long:
        context.log.warn("bar的数量不足, 等待下一根bar...")
        return
    # 计算短均线值
    short_mean = np.mean(hist['close'][-1 * context.user_data.window_short:])
    # 计算长均线值
    long_mean = np.mean(hist['close'][-1 * context.user_data.window_long:])

    # 根据策略产生信号并买卖
    # 短期线突破长期线一定比例，产生买入信号
    if short_mean - long_mean > context.user_data.enter_threshold * long_mean:
        if context.account.huobi_cny_cash > 0:
            # 有买入信号，且持有现金，则市价单全仓买入
            context.log.info("正在买入 %s" % context.security)
            context.order.buy(context.security, cash_amount=str(context.account.huobi_cny_cash))
    # 短期线低于长期线一定比例，产生卖出信号
    elif short_mean - long_mean < context.user_data.exit_threshold * long_mean:
        if getattr(context.account, context.security) > 0:
            # 有卖出信号，且持有仓位，则市价单全仓卖出
            context.log.info("正在卖出 %s" % context.security)
            context.order.sell(context.security, quantity=str(getattr(context.account, context.security)))
