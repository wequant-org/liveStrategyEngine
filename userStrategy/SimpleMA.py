#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
import common.helper as helper

# 回测阶段的策略配置，跑实盘的时候，所有Params中的配置都会被覆盖
Params = {
    "startTime": "2016-09-20 00:00:00",  # 回测起始时间
    "endTime": "2016-10-21 00:00:00",  # 回测结束时间
    "commission": {"buycost": 0, "sellcost": 0},  # 目前火币上数字货币的交易佣金为0
    "slippage": 0.02,  # 考虑滑点, 买入的交易价格调整为 S × (1 + value)，卖出的交易价格调整为 S × (1 - value)，其中S表示当前实际价格
    "initialPortfolio": {"cny": 10000, "huobi-cnybtc": 3},  # 初始账户状态
}

def initialize(context):  # 初始化虚拟账户状态
    context.frequency = "1m"  # 强制性变量，策略类型，'d'表示策略使用日线回测，'h'表示策略使用小时线回测，'m'表示策略使用分钟线回测
    # 可选列表 [ 1m, 5m, 15m, 30m, 60m, 1d, 1w, 1M, 1y ]
    context.benchmark = "huobi-cnybtc"  # 强制性变量
    context.security_name = "huobi-cnybtc"  # 用户自定义变量，想操作的security name
    context.user_data.window_short = 5  # 计算短线所需的历史bar数目，用户自定义的变量，可以被handle_data使用
    context.user_data.window_long = 20  # 计算长线所需的历史bar数目，用户自定义的变量，可以被handle_data使用
    context.user_data.enter_threshold = 0.05  # 入场线, 用户自定义的变量，可以被handle_data使用
    context.user_data.exit_threshold = -0.05  # 出场线, 用户自定义的变量，可以被handle_data使用

def handle_data(context):  # 每个frequency的买入卖出指令
    hist = context.data.get_price(context.security_name, count= context.user_data.window_long, frequency=context.frequency)  # 获取历史数据, 取后window_long根bar
    hist = hist[hist.security == context.security_name]  # 只取context.security_name的数据
    if (len(hist.index) < context.user_data.window_long):
        context.log.warn("bar number is not enough, waiting for the next bar...")
        return

    short_mean = np.mean(hist['close'][-1 * context.user_data.window_short:])  # 计算短均线值
    long_mean = np.mean(hist['close'][-1 * context.user_data.window_long:])  # 计算长均线值
    context.log.info("numpy result:short_mean:%f, long_mean:%f"%(short_mean,long_mean))

    #pd_short_mean = pd.rolling_mean(hist['close'],context.user_data.window_short).iloc[-1]
    pd_short_mean = pd.Series.rolling(hist['close'],center=False,window=context.user_data.window_short).mean()[-1]
    #pd_long_mean  = pd.rolling_mean(hist['close'],context.user_data.window_long).iloc[-1]
    pd_long_mean = pd.Series.rolling(hist['close'],center=False,window=context.user_data.window_long).mean()[-1]
    context.log.info("pandas result:short_mean:%f, long_mean:%f"%(pd_short_mean,pd_long_mean))

    # 计算买入卖出信号
    if short_mean - long_mean > context.user_data.enter_threshold * long_mean:
        if context.account.huobi_cny > 0:
            # 空仓时全仓买入
            context.order.buy(context.security_name, cash_amount=str(context.account.huobi_cny))  # marketOrder
            context.log.info("Buying %s"%context.security_name)
    elif short_mean - long_mean < context.user_data.exit_threshold * long_mean:
        if context.account.__getattribute__(helper.getCoinStrFromPricerStr(context.security_name)) > 0:
            # 卖出时，全仓清空
            context.order.sell(context.security_name, quantity=str(context.account.__getattribute__(helper.getCoinStrFromPricerStr(context.security_name))))  # marketOrder
            context.log.info("Selling %s"%context.security_name)

