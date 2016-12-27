#!/usr/bin/env python
# -*- coding: utf-8 -*-

from banZhuan.statArbStrategy import *


###############################################################
#   获取更多免费策略，请加入WeQuant比特币量化策略交流QQ群：519538535
#   群主邮箱：lanjason@foxmail.com，群主微信/QQ：64008672
#   沉迷量化，无法自拔
###############################################################


class FixedSpreadSignalGenerator(StatArbSignalGenerator):
    def __init__(self, startRunningTime, orderRatio, timeInterval, orderWaitingTime, dataLogFixedTimeWindow,
                 coinMarketType, open_diff, close_diff, maximum_qty_multiplier=None, auto_rebalance_on=False,
                 auto_rebalance_on_exit=False,
                 dailyExitTime=None):
        super(FixedSpreadSignalGenerator, self).__init__(startRunningTime, orderRatio, timeInterval, orderWaitingTime,
                                                         dataLogFixedTimeWindow,
                                                         coinMarketType,
                                                         maximum_qty_multiplier=maximum_qty_multiplier,
                                                         auto_rebalance_on=auto_rebalance_on,
                                                         auto_rebalance_on_exit=auto_rebalance_on_exit,
                                                         dailyExitTime=dailyExitTime)
        self.open_diff = open_diff
        self.close_diff = close_diff

    # 判断开仓、平仓
    def in_or_out(self, ref_price):
        if self.current_position_direction == 0:  # currently no spread position
            if self.spread1List[-1] / ref_price > self.open_diff:  # huobi > okcoin
                return 1  # buy okcoin, sell huobi
            elif self.spread2List[-1] / ref_price > self.open_diff:  # okcoin > huobi
                return 2  # sell okcoin, buy huobi
        elif self.current_position_direction == 1:  # currently long spread1
            if self.spread1List[-1] / ref_price > self.open_diff:  # huobi > okcoin
                return 1  # continue to buy okcoin, sell huobi, meaning upsizing spread1
            if self.spread1List[-1] / ref_price < self.close_diff:
                return 2  # unwind spread1
        elif self.current_position_direction == 2:  # currently long spread1
            if self.spread2List[-1] / ref_price > self.open_diff:  # okcoin > huobi
                return 2  # continue to sell okcoin, buy huobi, meaning upsizing spread2
            if self.spread2List[-1] / ref_price < self.close_diff:
                return 1  # unwind spread2
        return 0  # no action

    # 主要的逻辑
    def go(self):
        self.timeLog("日志启动于 %s" % self.getStartRunningTime().strftime(self.TimeFormatForLog))
        self.dataLog(
            content="time|huobi_cny_cash|huobi_cny_btc|huobi_cny_ltc|huobi_cny_cash_loan|huobi_cny_btc_loan|huobi_cny_ltc_loan|huobi_cny_cash_frozen|huobi_cny_btc_frozen|huobi_cny_ltc_frozen|huobi_cny_total|huobi_cny_net|okcoin_cny_cash|okcoin_cny_btc|okcoin_cny_ltc|okcoin_cny_cash_frozen|okcoin_cny_btc_frozen|okcoin_cny_ltc_frozen|okcoin_cny_total|okcoin_cny_net|total_net")
        self.dataLog()
        while True:
            if self.timeInterval > 0:
                self.timeLog("等待 %d 秒进入下一个循环..." % self.timeInterval)
                time.sleep(self.timeInterval)

            self.timeLog("记录心跳信息...")

            # calculate the net asset at a fixed time window
            time_diff = datetime.datetime.now() - self.last_data_log_time
            if time_diff.seconds > self.dataLogFixedTimeWindow:
                self.dataLog()

            # 查询huobi第一档深度数据
            huobiDepth = self.HuobiService.getDepth(helper.coinTypeStructure[self.coinMarketType]["huobi"]["coin_type"],
                                                    helper.coinTypeStructure[self.coinMarketType]["huobi"]["market"],
                                                    depth_size=1)
            # 查询okcoin第一档深度数据
            okcoinDepth = self.OKCoinService.depth(helper.coinTypeStructure[self.coinMarketType]["okcoin"]["coin_type"])

            huobi_sell_1_price = huobiDepth["asks"][0][0]
            huobi_sell_1_qty = huobiDepth["asks"][0][1]
            huobi_buy_1_price = huobiDepth["bids"][0][0]
            huobi_buy_1_qty = huobiDepth["bids"][0][1]
            okcoin_sell_1_price = okcoinDepth["asks"][0][0]
            okcoin_sell_1_qty = okcoinDepth["asks"][0][1]
            okcoin_buy_1_price = okcoinDepth["bids"][0][0]
            okcoin_buy_1_qty = okcoinDepth["bids"][0][1]
            spread1 = huobi_buy_1_price - okcoin_sell_1_price
            spread2 = okcoin_buy_1_price - huobi_sell_1_price
            self.spread1List.append(spread1)
            self.spread2List.append(spread2)
            max_price = np.max([huobi_sell_1_price, huobi_buy_1_price, okcoin_sell_1_price, okcoin_buy_1_price])

            # 获取当前账户信息
            accountInfo = self.getAccuntInfo()

            # check whether current time is after the dailyExitTime, if yes, exit
            if self.dailyExitTime is not None and datetime.datetime.now() > datetime.datetime.strptime(
                                    datetime.date.today().strftime("%Y-%m-%d") + " " + self.dailyExitTime,
                    "%Y-%m-%d %H:%M:%S"):
                self.timeLog("抵达每日终结时间：%s, 现在退出." % self.dailyExitTime)
                if self.auto_rebalance_on_exit:
                    self.rebalance_position(accountInfo, max_price)
                break

            current_position_proportion = self.get_current_position_proportion(accountInfo, max_price)
            if self.auto_rebalance_on and current_position_proportion > self.position_proportion_threshold:
                if abs(self.spread1List[-1] / max_price) < self.close_diff or abs(
                                self.spread2List[-1] / max_price) < self.close_diff:
                    self.rebalance_position(accountInfo, max_price)
                continue

            in_or_out = self.in_or_out(max_price)
            if in_or_out == 0:
                self.timeLog("没有发现交易信号，进入下一个轮询...")
                continue
            elif in_or_out == 1:
                if self.current_position_direction == 0:  # 当前没有持仓
                    self.timeLog("发现开仓信号（火币卖，OKcoin买）")
                elif self.current_position_direction == 1:  # 当前long spread1
                    self.timeLog("发现增仓信号（火币卖，OKcoin买）")
                elif self.current_position_direction == 2:  # 当前long spread2
                    self.timeLog("发现减仓信号（火币卖，OKcoin买）")

                self.timeLog("火币深度:%s" % str(huobiDepth))
                self.timeLog("okcoin深度:%s" % str(okcoinDepth))

                if self.current_position_direction == 0 or self.current_position_direction == 1:
                    if current_position_proportion > self.position_proportion_alert_threshold:
                        self.timeLog(
                            "当前仓位比例:%f 大于仓位预警比例：%f" % (
                                current_position_proportion, self.position_proportion_alert_threshold),
                            level=logging.WARN)
                    # 每次只能吃掉一定ratio的深度
                    Qty = helper.downRound(min(huobi_buy_1_qty, okcoin_sell_1_qty) * self.orderRatio, 4)
                elif self.current_position_direction == 2:
                    depthQty = helper.downRound(min(huobi_buy_1_qty, okcoin_sell_1_qty) * self.orderRatio, 4)
                    Qty = min(depthQty, helper.downRound(self.spread2_pos_qty, 4))

                # 每次搬砖最多只搬maximum_qty_multiplier个最小单位
                if self.maximum_qty_multiplier is not None:
                    Qty = min(Qty, max(self.huobi_min_quantity, self.okcoin_min_quantity) * self.maximum_qty_multiplier)

                # 每次搬砖前要检查是否有足够security和cash
                Qty = min(Qty, accountInfo[helper.coinTypeStructure[self.coinMarketType]["huobi"]["coin_str"]],
                          helper.downRound(accountInfo[helper.coinTypeStructure[self.coinMarketType]["okcoin"][
                              "market_str"]] / okcoin_sell_1_price, 4))
                Qty = helper.downRound(Qty, 4)
                Qty = helper.getRoundedQuantity(Qty, self.coinMarketType)

                if Qty < self.huobi_min_quantity or Qty < self.okcoin_min_quantity:
                    self.timeLog("当前在火币的币量：%.4f，OKCoin的现金：%.2f" % (
                    accountInfo[helper.coinTypeStructure[self.coinMarketType]["huobi"]["coin_str"]],
                    accountInfo[helper.coinTypeStructure[self.coinMarketType]["okcoin"]["market_str"]]))
                    self.timeLog("可交易的数量:%.4f 小于交易所最小交易数量(火币最小数量:%.4f, OKCoin最小数量:%.4f),因此无法下单并忽略该信号" % (
                    Qty, self.huobi_min_quantity, self.okcoin_min_quantity), level=logging.WARN)
                    continue
                else:
                    # step1: 先处理卖
                    executed_qty = self.sell_market(self.coinMarketType, str(Qty), exchange="huobi")
                    if executed_qty is not None:
                        # step2: 再执行买
                        Qty2 = min(executed_qty, Qty)
                        Qty2 = max(helper.getRoundedQuantity(Qty2, self.coinMarketType), self.okcoin_min_quantity)

                        if Qty2 < self.okcoin_min_quantity * 1.05:
                            self.buy_market(self.coinMarketType, str(Qty2 * okcoin_sell_1_price * 1.05),
                                            exchange="okcoin",
                                            sell_1_price=okcoin_sell_1_price)
                        else:
                            self.buy_market(self.coinMarketType, str(Qty2 * okcoin_sell_1_price), exchange="okcoin",
                                            sell_1_price=okcoin_sell_1_price)

                    if self.current_position_direction == 0 or self.current_position_direction == 1:
                        self.spread1_pos_qty += Qty2
                    elif self.current_position_direction == 2:
                        self.spread2_pos_qty -= Qty2
            elif in_or_out == 2:
                if self.current_position_direction == 0:  # 当前没有持仓
                    self.timeLog("发现开仓信号（OKcoin卖, 火币买）")
                elif self.current_position_direction == 2:  # 当前long spread2
                    self.timeLog("发现增仓信号（OKcoin卖, 火币买）")
                elif self.current_position_direction == 1:  # 当前long spread1
                    self.timeLog("发现减仓信号（OKcoin卖, 火币买）")

                self.timeLog("火币深度:%s" % str(huobiDepth))
                self.timeLog("okcoin深度:%s" % str(okcoinDepth))

                if self.current_position_direction == 0 or self.current_position_direction == 2:
                    if current_position_proportion > self.position_proportion_alert_threshold:
                        self.timeLog(
                            "当前仓位比例:%f 大于仓位预警比例：%f" % (
                                current_position_proportion, self.position_proportion_alert_threshold),
                            level=logging.WARN)
                    # 每次只能吃掉一定ratio的深度
                    Qty = helper.downRound(min(huobi_sell_1_qty, okcoin_buy_1_qty) * self.orderRatio, 4)
                elif self.current_position_direction == 1:
                    depthQty = helper.downRound(min(huobi_sell_1_qty, okcoin_buy_1_qty) * self.orderRatio, 4)
                    Qty = min(depthQty, helper.downRound(self.spread1_pos_qty, 4))

                # 每次搬砖最多只搬maximum_qty_multiplier个最小单位
                if self.maximum_qty_multiplier is not None:
                    Qty = min(Qty, max(self.huobi_min_quantity, self.okcoin_min_quantity) * self.maximum_qty_multiplier)

                # 每次搬砖前要检查是否有足够security和cash
                Qty = min(Qty, accountInfo[helper.coinTypeStructure[self.coinMarketType]["okcoin"]["coin_str"]],
                          helper.downRound(accountInfo[helper.coinTypeStructure[self.coinMarketType]["huobi"][
                              "market_str"]] / huobi_sell_1_price), 4)
                Qty = helper.getRoundedQuantity(Qty, self.coinMarketType)

                if Qty < self.huobi_min_quantity or Qty < self.okcoin_min_quantity:
                    self.timeLog("当前在OKCoin的币量：%.4f，火币的现金：%.2f" % (
                    accountInfo[helper.coinTypeStructure[self.coinMarketType]["okcoin"]["coin_str"]],
                    accountInfo[helper.coinTypeStructure[self.coinMarketType]["huobi"]["market_str"]]))
                    self.timeLog("可交易数量:%.4f 小于交易所最小交易数量(火币最小数量:%.4f, OKCoin最小数量:%.4f),因此无法下单并忽略该信号" % (
                    Qty, self.huobi_min_quantity, self.okcoin_min_quantity), level=logging.WARN)
                    continue
                else:
                    # step1: 先处理卖
                    executed_qty = self.sell_market(self.coinMarketType, str(Qty), exchange="okcoin")
                    if executed_qty is not None:
                        # step2: 再执行买
                        Qty2 = min(executed_qty, Qty)
                        self.buy_market(self.coinMarketType, str(Qty2 * huobi_sell_1_price), exchange="huobi")
                    if self.current_position_direction == 0 or self.current_position_direction == 2:
                        self.spread2_pos_qty += Qty2
                    elif self.current_position_direction == 1:
                        self.spread1_pos_qty -= Qty2

            if self.spread1_pos_qty > self.spread_pos_qty_minimum_size:
                self.current_position_direction = 1
            elif self.spread2_pos_qty > self.spread_pos_qty_minimum_size:
                self.current_position_direction = 2
            else:
                self.current_position_direction = 0
