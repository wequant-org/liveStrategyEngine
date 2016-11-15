#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

'''
海龟交易策略，利用唐安奇通道来跟踪趋势产生买卖信号，利用ATR（真实波幅均值）分批加仓或者减仓，并且动态进行止盈和止损。海龟交易策略是一套完整且成熟的交易系统，是程序化交易的经典案例。
海龟交易系统本质上是一个趋势跟随的系统,但是最值得我们学习的,是资金管理尤其是分批建仓及动态止损的部分
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


# 自定义函数，用于初始化一些用户数据
def init_local_context(context):
    # 上一次买入价
    context.user_data.last_buy_price = 0
    # 是否持有头寸标志
    context.user_data.hold_flag = False
    # 限制最多买入的单元数
    context.user_data.limit_unit = 4
    # 现在买入1单元的security数目
    context.user_data.unit = 0
    # 买入次数
    context.user_data.add_time = 0


# 初始化回测设置
def initialize(context):
    # 以30分钟为单位进行回测
    context.frequency = "30m"
    # 设定以比特币为基准
    context.benchmark = "huobi_cny_btc"
    # 设定操作的标的为比特币
    context.security = "huobi_cny_btc"

    # 设置策略的参数
    # 回看20日的ATR
    context.user_data.T = 20
    # 自定义的初始化函数
    init_local_context(context)
    # 记录入场、离常、止损点、持仓比、ATR
    context.user_data.record = {'break_up': {}, 'break_down': {}, 'stop_loss': {}, 'position': {},
                                'ATR': {}}

'''
================================================================================
开始回测
================================================================================
'''


# 用户自定义的函数，可以被handle_data调用: 唐奇安通道计算及判断入场离场
# data是日线级别的历史数据，price是当前分钟线数据（用来获取当前行情），T代表需要多少根日线
def in_or_out(data, price, T):
    up = np.max(data['high'].iloc[-T:])
    # 这里是10日唐奇安下沿，在向下突破10日唐奇安下沿卖出而不是在向下突破20日唐奇安下沿卖出，这是为了及时止损
    down = np.min(data['low'].iloc[-int(T / 2):])
    # 当前价格升破20日唐奇安上沿，产生入场信号
    if price > up:
        return 1
    # 当前价格跌破10日唐奇安下沿，产生出场信号
    elif price < down:
        return -1
    # 未产生有效信号
    else:
        return 0


# 用户自定义的函数，可以被handle_data调用：ATR值计算
def calc_atr(data):  # data是日线级别的历史数据
    tr_list = []
    for i in range(1, 21):
        tr = max(data['high'].iloc[i] - data['low'].iloc[i], data['high'].iloc[i] - data['close'].iloc[i - 1],
                 data['close'].iloc[i - 1] - data['low'].iloc[i])
        tr_list.append(tr)
    atr = np.array(tr_list).mean()
    return atr


# 用户自定义的函数，可以被handle_data调用
# 计算unit
def calc_unit(per_value, atr):
    return per_value / atr


# 用户自定义的函数，可以被handle_data调用
# 判断是否加仓或止损:当价格相对上个买入价上涨 0.5ATR时，再买入一个unit; 当价格相对上个买入价下跌 2ATR时，清仓
def add_or_stop(price, lastprice, atr):
    if price >= lastprice + 0.5 * atr:
        return 1
    elif price <= lastprice - 2 * atr:
        return -1
    else:
        return 0


# 根据设定的context.frequency每个时间单位调用一次
def handle_data(context):
    # 下面两行的逻辑是从当前时刻返回当前日期的String format
    today = context.time.get_current_time().strftime("%Y-%m-%d")

    # 计算持仓比例
    ratio = 1 - context.account.huobi_cny_cash / context.account.huobi_cny_net
    context.user_data.record['position'].update({today: ratio})  # 虽然每分钟重算，但因为key是日期，最后覆盖为当日最终持仓比

    # 将调仓记录输出到log中
    context.log.info(context.user_data.record)

    # 拿日级别的数据
    hist = context.data.get_price(context.security, count=context.user_data.T + 1, frequency="1d")  # 获取日级别历史数据
    if len(hist.index) < (context.user_data.T + 1):
        context.log.warn("bar的数量不足, 等待下一根bar...")
        return

    # 拿分钟级别的数据，作为当前行情
    price = context.data.get_current_price(context.security).iloc[0]['price']

    # 1 计算ATR
    atr = calc_atr(hist)
    context.user_data.record['ATR'].update({today: atr})

    # 2 判断加仓或止损
    if context.user_data.hold_flag is True and getattr(context.account, context.security) > 0:  # 先判断是否持仓
        temp = add_or_stop(price, context.user_data.last_buy_price, atr)
        if temp == 1 and context.user_data.add_time < context.user_data.limit_unit:  # 判断加仓
            cash_amount = min(context.account.huobi_cny_cash, context.user_data.unit * price)  # 不够1 unit时买入剩下全部
            context.user_data.last_buy_price = price
            context.user_data.add_time += 1
            context.log.info("正在买入 %s" % context.security)
            context.order.buy(context.security, cash_amount=str(cash_amount))
        elif temp == -1:  # 判断止损
            context.log.info("正在卖出 %s" % context.security)
            # 重新初始化参数！重新初始化参数！重新初始化参数！非常重要！
            init_local_context(context)
            context.user_data.record['stop_loss'].update({today: price})
            context.order.sell(context.security, quantity=str(getattr(context.account, context.security)))
    else:
        # 3 判断入场离场
        out = in_or_out(hist, price, context.user_data.T)
        if out == 1 and context.user_data.hold_flag is False:  # 入场
            value = min(context.account.huobi_cny_net * 0.01, context.account.huobi_cny_cash)
            context.user_data.unit = calc_unit(value, atr)
            context.log.info("正在买入 %s" % context.security)
            context.user_data.add_time = 1
            context.user_data.hold_flag = True
            context.user_data.last_buy_price = price
            context.user_data.record['break_up'].update({today: price})
            context.order.buy(context.security, cash_amount=str(context.user_data.unit * price))  # marketOrder
        elif out == -1 and context.user_data.hold_flag is True:  # 离场
            if getattr(context.account, context.security) > 0:
                # 重新初始化参数！重新初始化参数！重新初始化参数！非常重要！
                init_local_context(context)
                context.user_data.record['break_down'].update({today: price})
                # 有卖出信号，且持有仓位，则市价单全仓卖出
                context.log.info("正在卖出 %s" % context.security)
                context.order.sell(context.security, quantity=str(getattr(context.account, context.security)))
