#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
价值平均定投策略，是一种长期的定投策略。提前确定好每一期期望的持仓总市值。根据期望市值与实际持仓市值的差来决定买入/卖出多少市值的标的。比传统固定金额定投更为灵活，适合长期投资。
这个策略适合长期看好比特币的粉丝，可以有效的抵抗市场波动，做到低吸高抛。

策略实现：
设定好每个周期的目标仓位，每个周期都拿当前仓位与目标仓位比较，计算差值，决定买/卖/不动，以达到目标仓位。
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
    # 每个frequency的持仓总值的增长金额
    context.user_data.pos_value_growth_per_period = 200
    # 记录下当前处于第几个投资周期
    context.user_data.invest_period_count = 0
    # 设置策略期望初始仓位
    context.user_data.initial_pos_value = 0


'''
================================================================================
开始回测
================================================================================
'''


# 计算每一个frequency需要买入/卖出的金额（正为买入，负为卖出）
def cash_to_spent_fn(context, expected_pos_value, current_pos_value, current_cash_pos, current_sec_pos, latest_close_price):
    # 低于目标仓位，需要买入加仓
    if expected_pos_value > current_pos_value:
        result = expected_pos_value - current_pos_value
        if result < current_cash_pos:
            return result
        else:  # 现金不足，投入全部现金加仓
            context.log.warn(
                "现金不足以满足目标仓位, 需要现金:%.2f, 现有现金:%.2f. 本次将用完全部现金" % (result, current_cash_pos))
            return current_cash_pos
    else:  # 当前仓位高于目标仓位，需要卖出减仓
        result = current_pos_value - expected_pos_value
        pos_qty_to_sell = result / latest_close_price
        if pos_qty_to_sell < current_sec_pos:
            return -1 * result
        else:  # 仓位不足，卖出全部仓位
            context.log.warn(
                "现有仓位不足以满足目标仓位, 需要卖出仓位:%.2f, 现有仓位:%.2f. 本次将卖出所有仓位" % (pos_qty_to_sell, current_sec_pos))
            return -1 * latest_close_price * current_sec_pos


# 根据设定的context.frequency每个时间单位调用一次
def handle_data(context):
    # 取得最新价格
    latest_close_price = context.data.get_current_price(context.security).iloc[0]['price']
    # 计算当前实时仓位
    current_pos_value = getattr(context.account, context.security) * latest_close_price

    if context.user_data.initial_pos_value is None:
        context.user_data.initial_pos_value = current_pos_value

    # 计算当前期望仓位
    expected_pos_value = context.user_data.initial_pos_value + context.user_data.pos_value_growth_per_period * (
        context.user_data.invest_period_count + 1)
    # 当前账户持有的人民币现金
    current_cash_pos = context.account.huobi_cny_cash
    # 当前账户持有的数字货币数量
    current_sec_pos = getattr(context.account, context.security)
    # 计算本期需要投入的资金(若为负，则是撤回的资金)
    cash_to_spent = cash_to_spent_fn(context, expected_pos_value, current_pos_value, current_cash_pos, current_sec_pos,
                                     latest_close_price)
    context.log.info("本期需要投入的现金:%f" % cash_to_spent)

    # 更新投资周期至下一期
    context.user_data.invest_period_count += 1

    if cash_to_spent > 0:
        # 需要加仓，市价单买入
        context.log.info("正在买入 %s" % context.security)
        context.order.buy(context.security, cash_amount=str(cash_to_spent))
    else:
        # 需要减仓，计算需要卖出的数量，市价单卖出
        quantity = min(getattr(context.account, context.security), -1 * cash_to_spent / latest_close_price)
        context.log.info("正在卖出 %s" % context.security)
        context.order.sell(context.security, quantity=str(quantity))






