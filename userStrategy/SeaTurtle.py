#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import common.helper as helper

#海龟交易法是著名的公开交易系统，1983年著名的商品投机家理查德. 丹尼斯在一个交易员培训班上推广而闻名于世。
#它涵盖了交易系统的各个方面。其法则覆盖了交易的各个方面，并且不给交易员留下一点主观想象决策的余地。
#它具备一个完整的交易系统的所有成分。

# 用户自定义的函数，可以被handle_data调用: 唐奇安通道计算及判断入场离场
# data是日线级别的历史数据，price是当前分钟线数据（用来获取当前行情），T代表需要多少根日线
def IN_OR_OUT(data, price, T):
    up = np.max(data['high'].iloc[-T:])
    down = np.min(data['low'].iloc[-int(T/2):])  # 这里是10日唐奇安下沿，在向下突破10日唐奇安下沿卖出而不是在向下突破20日唐奇安下沿卖出，这是为了及时止损
    if price>up:
        return 1    #当前价格升破20日唐奇安上沿，产生入场信号
    elif price<down:
        return -1    #当前价格跌破10日唐奇安下沿，产生出场信号
    else:
        return 0    #未产生有效信号

# 用户自定义的函数，可以被handle_data调用：ATR值计算
def CalcATR(data):  #data是日线级别的历史数据
    TR_List = []
    for i in range(1,21):
        TR = max(data['high'].iloc[i]-data['low'].iloc[i],data['high'].iloc[i]-data['close'].iloc[i-1],data['close'].iloc[i-1]-data['low'].iloc[i])
        TR_List.append(TR)
    ATR = np.array(TR_List).mean()
    return ATR

# 用户自定义的函数，可以被handle_data调用
# 计算unit
def CalcUnit(perValue,ATR):
    return perValue/ATR

# 用户自定义的函数，可以被handle_data调用
# 判断是否加仓或止损:当价格相对上个买入价上涨 0.5ATR时，再买入一个unit; 当价格相对上个买入价下跌 2ATR时，清仓
def Add_OR_Stop(price, lastprice, ATR):
    if price >= lastprice + 0.5*ATR:
        return 1
    elif price <= lastprice - 2*ATR:
        return -1
    else:
        return 0

def init_local_context(context):
    context.user_data.last_buy_price = 0              #上一次买入价
    context.user_data.hold_flag = False               # 是否持有头寸标志
    context.user_data.limit_unit = 4                     # 限制最多买入的单元数
    context.user_data.unit = 0                           # 现在买入1单元的security数目
    context.user_data.add_time = 0                       # 买入次数

def initialize(context):                    # 初始化虚拟账户状态
    context.frequency = '1m'                # 强制性变量，策略类型，'d'表示策略使用日线回测，'h'表示策略使用小时线回测，'m'表示策略使用分钟线回测
                                            # 可选列表 [ 1m, 5m, 15m, 30m, 60m, 1d, 1w, 1M, 1y ]
    context.benchmark = 'huobi-cnybtc'      # 强制性变量
    context.security_name = 'huobi-cnybtc'  # 用户自定义变量，想操作的security name
    context.user_data.T = 20                          # 20日ATR
    init_local_context(context)
    context.user_data.record = {'break_up':{},'break_down':{},'stop_loss':{},'position':{},'ATR':{}}  # 记录入场、离常、止损点、持仓比、ATR

def handle_data(context):                  # 每个frequency的买入卖出指令
    #下面两行的逻辑是从当前时刻返回当前日期的String format
    today = context.time.get_current_time().strftime("%Y-%m-%d")

    #计算持仓比例
    ratio = 1 - context.account.huobi_cny/context.account.huobi_net
    context.user_data.record['position'].update({today:ratio})  # 虽然每分钟重算，但因为key是日期，最后覆盖为当日最终持仓比

    # 将调仓记录输出到log中
    context.log.info(context.user_data.record)

    #拿日级别的数据
    hist = context.data.get_price(context.security_name, count= context.user_data.T+1, frequency="1d")  #获取日级别历史数据
    hist = hist[hist.security == context.security_name]  # 只取context.security_name的数据
    if len(hist.index) < (context.user_data.T+1):
        context.log.warn("bar number is not enough, waiting for the next bar...")
        return

    #拿分钟级别的数据，作为当前行情
    price = context.data.get_current_price(context.security_name)

    # 1 计算ATR
    ATR = CalcATR(hist)
    context.user_data.record['ATR'].update({today:ATR})

    # 2 判断加仓或止损
    if context.user_data.hold_flag==True and context.account.__getattribute__(helper.getCoinStrFromPricerStr(context.security_name))>0:   # 先判断是否持仓
        temp = Add_OR_Stop(price, context.user_data.last_buy_price, ATR)
        if temp ==1 and context.user_data.add_time<context.user_data.limit_unit:  # 判断加仓
            cash_amount = min(context.account.huobi_cny, context.user_data.unit*price)# 不够1 unit时买入剩下全部
            context.order.buy(context.security_name, cash_amount=str(cash_amount))  # marketOrder
            context.log.info("Buying %s"%context.security_name)
            context.user_data.last_buy_price = price
            context.user_data.add_time += 1
        elif temp== -1:      # 判断止损
            context.order.sell(context.security_name, quantity=str(context.account.__getattribute__(helper.getCoinStrFromPricerStr(context.security_name))))
            context.log.info("Selling %s"%context.security_name)
            # 重新初始化参数  very important here!
            init_local_context(context)
            context.user_data.record['stop_loss'].update({today:price})
    else:
        # 3 判断入场离场
        out = IN_OR_OUT(hist, price, context.user_data.T)
        if out ==1 and context.user_data.hold_flag==False:  #入场
            value = min( context.account.huobi_net * 0.01, context.account.huobi_cny)
            context.user_data.unit = CalcUnit(value,ATR)
            context.order.buy(context.security_name, cash_amount=str(context.user_data.unit*price))  # marketOrder
            context.log.info("Buying %s"%context.security_name)
            context.user_data.add_time = 1
            context.user_data.hold_flag = True
            context.user_data.last_buy_price = price
            context.user_data.record['break_up'].update({today:price})

        elif out==-1 and context.user_data.hold_flag ==True: #离场
            if context.account.__getattribute__(helper.getCoinStrFromPricerStr(context.security_name)) > 0:
                # 卖出时，全仓清空
                context.order.sell(context.security_name, quantity=str(context.account.__getattribute__(helper.getCoinStrFromPricerStr(context.security_name))))  # marketOrder
                context.log.info("Selling %s"%context.security_name)
                # 重新初始化参数  very important here!
                init_local_context(context)
                context.user_data.record['break_down'].update({today:price})