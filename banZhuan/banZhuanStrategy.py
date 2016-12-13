#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################
#   获取更多免费策略，请加入WeQuant比特币量化策略交流QQ群：519538535
#   群主邮箱：lanjason@foxmail.com，群主微信/QQ：64008672
#   沉迷量化，无法自拔
###############################################################

import datetime
import logging

from common.Errors import StartRunningTimeEmptyError
from exchangeConnection.huobi import huobiService
from exchangeConnection.huobi.util import *
from exchangeConnection.okcoin.util import getOkcoinSpot
from utils import helper


class BanZhuanStrategy(object):
    def __init__(self, startRunningTime, orderRatio, timeInterval, orderWaitingTime, dataLogFixedTimeWindow,
                 coinMarketType,
                 dailyExitTime=None):
        self.startRunningTime = startRunningTime
        self.orderRatio = orderRatio  # 每次预计能吃到的盘口深度的百分比
        self.timeInterval = timeInterval  # 每次循环结束之后睡眠的时间, 单位：秒
        self.orderWaitingTime = orderWaitingTime  # 每次等待订单执行的最长时间
        self.dataLogFixedTimeWindow = dataLogFixedTimeWindow  # in seconds
        self.coinMarketType = coinMarketType
        self.dailyExitTime = dailyExitTime
        self.TimeFormatForFileName = "%Y%m%d%H%M%S%f"
        self.TimeFormatForLog = "%Y-%m-%d %H:%M:%S.%f"
        self.okcoinService = getOkcoinSpot()
        self.huobiService = huobiService
        self.huobi_min_quantity = self.huobiService.getMinimumOrderQty(
            helper.coinTypeStructure[self.coinMarketType]["huobi"]["coin_type"])
        self.huobi_min_cash_amount = self.huobiService.getMinimumOrderCashAmount()
        self.okcoin_min_quantity = self.okcoinService.getMinimumOrderQty(
            helper.coinTypeStructure[self.coinMarketType]["okcoin"]["coin_type"])
        # okcoin 的比特币最小市价买单下单金额是：0.01BTC*比特币当时市价
        # okcoin 的莱特币最小市价买单下单金额是：0.1LTC*莱特币当时市价
        self.last_data_log_time = None

        # setup timeLogger
        self.timeLogger = logging.getLogger('timeLog')
        self.timeLogger.setLevel(logging.DEBUG)
        self.timeLogHandler = logging.FileHandler(self.getTimeLogFileName())
        self.timeLogHandler.setLevel(logging.DEBUG)
        self.consoleLogHandler = logging.StreamHandler()
        self.consoleLogHandler.setLevel(logging.DEBUG)
        # 定义handler的输出格式
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.timeLogHandler.setFormatter(formatter)
        self.consoleLogHandler.setFormatter(formatter)
        # 给timeLogger添加handler
        self.timeLogger.addHandler(self.timeLogHandler)
        self.timeLogger.addHandler(self.consoleLogHandler)

        # setup dataLogger
        self.dataLogger = logging.getLogger('dataLog')
        self.dataLogger.setLevel(logging.DEBUG)
        self.dataLogHandler = logging.FileHandler(self.getDataLogFileName())
        self.dataLogHandler.setLevel(logging.DEBUG)
        self.dataLogger.addHandler(self.dataLogHandler)

    def getStartRunningTime(self):
        if self.startRunningTime == None:
            raise StartRunningTimeEmptyError("startRunningTime is not set yet!")
        return self.startRunningTime

    def getTimeLogFileName(self):
        return "log/%s_log_%s.txt" % (
            self.__class__.__name__, self.getStartRunningTime().strftime(self.TimeFormatForFileName))

    def getDataLogFileName(self):
        return "data/%s_data_%s.data" % (
            self.__class__.__name__, self.getStartRunningTime().strftime(self.TimeFormatForFileName))

    def timeLog(self, content):
        self.timeLogger.info(content)

    def getAccuntInfo(self):
        huobiAcct = self.huobiService.getAccountInfo(helper.coinTypeStructure[self.coinMarketType]["huobi"]["market"],
                                                     ACCOUNT_INFO)
        huobi_cny_cash = float(huobiAcct[u'available_cny_display'])
        huobi_cny_btc = float(huobiAcct[u'available_btc_display'])
        huobi_cny_ltc = float(huobiAcct[u'available_ltc_display'])
        huobi_cny_cash_loan = float(huobiAcct[u'loan_cny_display'])
        huobi_cny_btc_loan = float(huobiAcct[u'loan_btc_display'])
        huobi_cny_ltc_loan = float(huobiAcct[u'loan_ltc_display'])
        huobi_cny_cash_frozen = float(huobiAcct[u'frozen_cny_display'])
        huobi_cny_btc_frozen = float(huobiAcct[u'frozen_btc_display'])
        huobi_cny_ltc_frozen = float(huobiAcct[u'frozen_ltc_display'])
        huobi_cny_total = float(huobiAcct[u'total'])
        huobi_cny_net = float(huobiAcct[u'net_asset'])

        okcoinAcct = self.okcoinService.userinfo()
        okcoin_cny_cash = float(okcoinAcct["info"]["funds"]["free"]["cny"])
        okcoin_cny_btc = float(okcoinAcct["info"]["funds"]["free"]["btc"])
        okcoin_cny_ltc = float(okcoinAcct["info"]["funds"]["free"]["ltc"])
        okcoin_cny_cash_frozen = float(okcoinAcct["info"]["funds"]["freezed"]["cny"])
        okcoin_cny_btc_frozen = float(okcoinAcct["info"]["funds"]["freezed"]["btc"])
        okcoin_cny_ltc_frozen = float(okcoinAcct["info"]["funds"]["freezed"]["ltc"])
        okcoin_cny_total = float(okcoinAcct["info"]["funds"]["asset"]["total"])
        okcoin_cny_net = float(okcoinAcct["info"]["funds"]["asset"]["net"])
        total_net = huobi_cny_net + okcoin_cny_net
        return {
            "huobi_cny_cash": huobi_cny_cash,
            "huobi_cny_btc": huobi_cny_btc,
            "huobi_cny_ltc": huobi_cny_ltc,
            "huobi_cny_cash_loan": huobi_cny_cash_loan,
            "huobi_cny_btc_loan": huobi_cny_btc_loan,
            "huobi_cny_ltc_loan": huobi_cny_ltc_loan,
            "huobi_cny_cash_frozen": huobi_cny_cash_frozen,
            "huobi_cny_btc_frozen": huobi_cny_btc_frozen,
            "huobi_cny_ltc_frozen": huobi_cny_ltc_frozen,
            "huobi_cny_total": huobi_cny_total,
            "huobi_cny_net": huobi_cny_net,

            "okcoin_cny_cash": okcoin_cny_cash,
            "okcoin_cny_btc": okcoin_cny_btc,
            "okcoin_cny_ltc": okcoin_cny_ltc,
            "okcoin_cny_cash_frozen": okcoin_cny_cash_frozen,
            "okcoin_cny_btc_frozen": okcoin_cny_btc_frozen,
            "okcoin_cny_ltc_frozen": okcoin_cny_ltc_frozen,
            "okcoin_cny_total": okcoin_cny_total,
            "okcoin_cny_net": okcoin_cny_net,

            "total_net": total_net,
        }

    def dataLog(self, content=None):
        if content is None:
            accountInfo = self.getAccuntInfo()
            t = datetime.datetime.now()
            content = "%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s" % \
                      (t.strftime(self.TimeFormatForLog),
                       accountInfo["huobi_cny_cash"],
                       accountInfo["huobi_cny_btc"],
                       accountInfo["huobi_cny_ltc"],
                       accountInfo["huobi_cny_cash_loan"],
                       accountInfo["huobi_cny_btc_loan"],
                       accountInfo["huobi_cny_ltc_loan"],
                       accountInfo["huobi_cny_cash_frozen"],
                       accountInfo["huobi_cny_btc_frozen"],
                       accountInfo["huobi_cny_ltc_frozen"],
                       accountInfo["huobi_cny_total"],
                       accountInfo["huobi_cny_net"],
                       accountInfo["okcoin_cny_cash"],
                       accountInfo["okcoin_cny_btc"],
                       accountInfo["okcoin_cny_ltc"],
                       accountInfo["okcoin_cny_cash_frozen"],
                       accountInfo["okcoin_cny_btc_frozen"],
                       accountInfo["okcoin_cny_ltc_frozen"],
                       accountInfo["okcoin_cny_total"],
                       accountInfo["okcoin_cny_net"],
                       accountInfo["total_net"])
            self.last_data_log_time = t
        self.dataLogger.info("%s" % str(content))

    def sell(self, security, quantity, exchange="huobi"):  # quantity is a string value
        if exchange == "huobi":
            self.timeLog("开始下达火币市价卖单...")
            self.timeLog("只保留下单数量的小数点后4位...")
            self.timeLog("原始下单数量:%s" % quantity)
            tmp = float(quantity)
            tmp = helper.downRound(tmp, 4)
            quantity = str(tmp)
            self.timeLog("做完小数点处理后的下单数量:%s" % quantity)
            if float(quantity) < self.huobi_min_quantity:
                self.timeLog(
                    "数量:%s 小于交易所最小交易数量(火币最小数量:%f),因此无法下单,此处忽略该信号" % (quantity, self.huobi_min_quantity))
                return None

            coin_type = helper.coinTypeStructure[self.coinMarketType]["huobi"]["coin_type"]
            res = self.huobiService.sellMarket(coin_type, quantity, None, None,
                                               helper.coinTypeStructure[self.coinMarketType]["huobi"]["market"],
                                               SELL_MARKET)
            if u"result" not in res or res[u"result"] != u'success':
                self.timeLog("下达火币市价卖单（数量：%s）失败！" % quantity)
                return None
            order_id = res[u"id"]
            # 查询订单执行情况
            order_info = self.huobiService.getOrderInfo(coin_type, order_id,
                                                        helper.coinTypeStructure[self.coinMarketType]["huobi"][
                                                            "market"], ORDER_INFO)
            self.timeLog("下达如下火币市价卖单，数量：%s" % quantity)
            self.timeLog(str(order_info))
            if order_info["status"] != 2:
                self.timeLog("等待%f秒直至订单完成" % self.orderWaitingTime)
                time.sleep(self.orderWaitingTime)
                order_info = self.huobiService.getOrderInfo(coin_type, order_id,
                                                            helper.coinTypeStructure[self.coinMarketType]["huobi"][
                                                                "market"], ORDER_INFO)
                self.timeLog(str(order_info))
            executed_qty = float(order_info["processed_amount"])
            self.timeLog(
                "火币市价卖单已被执行，执行数量：%f，收到的现金：%.2f" % (executed_qty, executed_qty * float(order_info["processed_price"])))
            self.dataLog()
            return executed_qty
        elif exchange == "okcoin":
            self.timeLog("开始下达okcoin市价卖单...")
            self.timeLog("只保留下单数量的小数点后2位...")
            self.timeLog("原始下单数量:%s" % quantity)
            tmp = float(quantity)
            tmp = helper.downRound(tmp, 2)
            quantity = str(tmp)
            self.timeLog("做完小数点处理后的下单数量:%s" % quantity)
            if float(quantity) < self.okcoin_min_quantity:
                self.timeLog(
                    "数量:%s 小于交易所最小交易数量(火币最小数量:%f),因此无法下单,此处忽略该信号" % (quantity, self.okcoin_min_quantity))
                return None
            res = self.okcoinService.trade(helper.coinTypeStructure[self.coinMarketType]["okcoin"]["coin_type"],
                                           "sell_market", amount=quantity)
            if "result" not in res or res["result"] != True:
                self.timeLog("下达okcoin市价卖单（数量：%s）失败" % quantity)
                return None
            order_id = res["order_id"]
            # 查询订单执行情况
            order_info = self.okcoinService.orderinfo(
                helper.coinTypeStructure[self.coinMarketType]["okcoin"]["coin_type"], str(order_id))
            self.timeLog("下达如下okcoin市价卖单，数量：%s" % quantity)
            self.timeLog(str(order_info))
            if order_info["orders"][0]["status"] != 2:
                self.timeLog("等待%.1f秒直至订单完成" % self.orderWaitingTime)
                time.sleep(self.orderWaitingTime)
                order_info = self.okcoinService.orderinfo(
                    helper.coinTypeStructure[self.coinMarketType]["okcoin"]["coin_type"], str(order_id))
                self.timeLog(str(order_info))
            executed_qty = order_info["orders"][0]["deal_amount"]
            self.timeLog("okcoin市价卖单已被执行，执行数量：%f，收到的现金：%.2f" % (
                executed_qty, executed_qty * order_info["orders"][0]["avg_price"]))
            self.dataLog()
            return executed_qty

    def buy(self, security, cash_amount, exchange="huobi", sell_1_price=None):  # cash_amount is a string value
        if exchange == "huobi":
            self.timeLog("开始下达火币市价买单...")
            self.timeLog("只保留下单数量的小数点后2位...")
            self.timeLog("原始下单金额:%s" % cash_amount)
            tmp = float(cash_amount)
            tmp = helper.downRound(tmp, 2)
            cash_amount = str(tmp)
            self.timeLog("做完小数点处理后的下单金额:%s" % cash_amount)

            if float(cash_amount) < self.huobi_min_cash_amount:
                self.timeLog("金额:%s 小于交易所最小交易金额(火币最小金额:1元),因此无法下单,此处忽略该信号" % (cash_amount, self.huobi_min_cash_amount))
                return None

            coin_type = helper.coinTypeStructure[self.coinMarketType]["huobi"]["coin_type"]
            res = self.huobiService.buyMarket(coin_type, cash_amount, None, None,
                                              helper.coinTypeStructure[self.coinMarketType]["huobi"]["market"],
                                              BUY_MARKET)
            if u"result" not in res or res[u"result"] != u'success':
                self.timeLog("下达火币市价买单（金额：%s）失败！" % cash_amount)
                return None
            order_id = res[u"id"]
            # 查询订单执行情况
            order_info = self.huobiService.getOrderInfo(coin_type, order_id,
                                                        helper.coinTypeStructure[self.coinMarketType]["huobi"][
                                                            "market"], ORDER_INFO)
            self.timeLog("下达如下火币市价买单，金额：%s" % cash_amount)
            self.timeLog(str(order_info))
            if order_info["status"] != 2:
                self.timeLog("等待%f秒直至订单完成" % self.orderWaitingTime)
                time.sleep(self.orderWaitingTime)
                order_info = self.huobiService.getOrderInfo(coin_type, order_id,
                                                            helper.coinTypeStructure[self.coinMarketType]["huobi"][
                                                                "market"], ORDER_INFO)
                self.timeLog(str(order_info))
            executed_qty = float(order_info["processed_amount"]) / float(order_info["processed_price"])
            self.timeLog("火币市价买单已被执行，执行数量：%f，花费的现金：%.2f" % (executed_qty, float(order_info["processed_amount"])))
            self.dataLog()
            return executed_qty
        elif exchange == "okcoin":
            if sell_1_price is None:
                raise ValueError("处理okcoin市价买单之前，需要提供当前Okcoin卖一的价格信息，请检查传入的sell_1_price参数是否完备！")
            self.timeLog("开始下达okcoin市价买单...")
            self.timeLog("只保留下单数量的小数点后2位...")
            self.timeLog("原始下单金额:%s" % cash_amount)
            tmp = float(cash_amount)
            tmp = helper.downRound(tmp, 2)
            cash_amount = str(tmp)
            self.timeLog("做完小数点处理后的下单金额:%s" % cash_amount)

            if float(cash_amount) < self.okcoin_min_quantity * sell_1_price:
                self.timeLog(
                    "金额:%s 不足以购买交易所最小交易数量(okcoin最小数量:%f，当前卖一价格%.2f,最小金额要求：%.2f),因此无法下单,此处忽略该信号" % (
                        cash_amount, self.okcoin_min_quantity, sell_1_price, self.okcoin_min_quantity * sell_1_price))
                return None
            res = self.okcoinService.trade(helper.coinTypeStructure[self.coinMarketType]["okcoin"]["coin_type"],
                                           "buy_market", price=cash_amount)

            if "result" not in res or res["result"] != True:
                self.timeLog("下达okcoin市价买单（金额：%s）失败" % cash_amount)
                return None
            order_id = res["order_id"]
            # 查询订单执行情况
            order_info = self.okcoinService.orderinfo(
                helper.coinTypeStructure[self.coinMarketType]["okcoin"]["coin_type"], str(order_id))
            self.timeLog("下达如下okcoin市价买单，金额：%s" % cash_amount)
            self.timeLog(str(order_info))
            if order_info["orders"][0]["status"] != 2:
                self.timeLog("等待%.1f秒直至订单完成" % self.orderWaitingTime)
                time.sleep(self.orderWaitingTime)
                order_info = self.okcoinService.orderinfo(
                    helper.coinTypeStructure[self.coinMarketType]["okcoin"]["coin_type"], str(order_id))
                self.timeLog(str(order_info))
            executed_qty = order_info["orders"][0]["deal_amount"]
            self.timeLog("okcoin市价买单已被执行，执行数量：%f，花费的现金：%.2f" % (
                executed_qty, executed_qty * order_info["orders"][0]["avg_price"]))
            self.dataLog()
            return executed_qty

    def go(self):
        self.timeLog("日志启动于 %s" % self.getStartRunningTime().strftime(self.TimeFormatForLog))
        self.dataLog(
            content="time|huobi_cny_cash|huobi_cny_btc|huobi_cny_ltc|huobi_cny_cash_loan|huobi_cny_btc_loan|huobi_cny_ltc_loan|huobi_cny_cash_frozen|huobi_cny_btc_frozen|huobi_cny_ltc_frozen|huobi_cny_total|huobi_cny_net|okcoin_cny_cash|okcoin_cny_btc|okcoin_cny_ltc|okcoin_cny_cash_frozen|okcoin_cny_btc_frozen|okcoin_cny_ltc_frozen|okcoin_cny_total|okcoin_cny_net|total_net")
        self.dataLog()

        while (True):
            # check whether current time is after the dailyExitTime, if yes, exit
            if self.dailyExitTime is not None and datetime.datetime.now() > datetime.datetime.strptime(
                                    datetime.date.today().strftime("%Y-%m-%d") + " " + self.dailyExitTime,
                    "%Y-%m-%d %H:%M:%S"):
                self.timeLog("抵达每日终结时间：%s, 现在退出." % self.dailyExitTime)
                break

            self.timeLog("等待 %d 秒进入下一个循环..." % self.timeInterval)
            time.sleep(self.timeInterval)

            # calculate the net asset at a fixed time window
            time_diff = datetime.datetime.now() - self.last_data_log_time
            if time_diff.seconds > self.dataLogFixedTimeWindow:
                self.dataLog()

            # 获取当前账户信息
            accountInfo = self.getAccuntInfo()

            # 查询huobi第一档深度数据
            huobiDepth = self.huobiService.getDepth(helper.coinTypeStructure[self.coinMarketType]["huobi"]["coin_type"],
                                                    helper.coinTypeStructure[self.coinMarketType]["huobi"]["market"],
                                                    depth_size=1)
            # 查询okcoin第一档深度数据
            okcoinDepth = self.okcoinService.depth(helper.coinTypeStructure[self.coinMarketType]["okcoin"]["coin_type"])

            huobi_sell_1_price = huobiDepth["asks"][0][0]
            huobi_sell_1_qty = huobiDepth["asks"][0][1]
            huobi_buy_1_price = huobiDepth["bids"][0][0]
            huobi_buy_1_qty = huobiDepth["bids"][0][1]

            okcoin_sell_1_price = okcoinDepth["asks"][0][0]
            okcoin_sell_1_qty = okcoinDepth["asks"][0][1]
            okcoin_buy_1_price = okcoinDepth["bids"][0][0]
            okcoin_buy_1_qty = okcoinDepth["bids"][0][1]

            if huobi_buy_1_price > okcoin_sell_1_price:  # 获利信号：OKcoin买，huobi卖
                self.timeLog("发现信号")
                self.timeLog("火币深度:%s" % str(huobiDepth))
                self.timeLog("okcoin深度:%s" % str(okcoinDepth))

                # 每次只能吃掉一定ratio的深度
                Qty = helper.downRound(min(huobi_buy_1_qty, okcoin_sell_1_qty) * self.orderRatio, 4)
                # 每次搬砖前要检查是否有足够security和cash
                Qty = min(Qty, accountInfo[helper.coinTypeStructure[self.coinMarketType]["huobi"]["coin_str"]],
                          helper.downRound(accountInfo[helper.coinTypeStructure[self.coinMarketType]["okcoin"][
                              "market_str"]] / okcoin_sell_1_price, 4))
                Qty = helper.downRound(Qty, 4)
                Qty = helper.getRoundedQuantity(Qty, self.coinMarketType)

                if Qty < self.huobi_min_quantity or Qty < self.okcoin_min_quantity:
                    self.timeLog(
                        "数量:%f 小于交易所最小交易数量(火币最小数量:%f, okcoin最小数量:%f),因此无法下单并忽略该信号" % (
                            Qty, self.huobi_min_quantity, self.okcoin_min_quantity))
                    continue
                else:
                    # step1: 先处理卖
                    executed_qty = self.sell(self.coinMarketType, str(Qty), exchange="huobi")
                    if executed_qty is not None:
                        # step2: 再执行买
                        Qty2 = min(executed_qty, Qty)
                        Qty2 = max(helper.getRoundedQuantity(Qty2, self.coinMarketType), self.okcoin_min_quantity)

                    if Qty2 < self.okcoin_min_quantity * 1.05:
                        self.buy(self.coinMarketType, str(Qty2 * okcoin_sell_1_price * 1.05), exchange="okcoin",
                                 sell_1_price=okcoin_sell_1_price)
                    else:
                        self.buy(self.coinMarketType, str(Qty2 * okcoin_sell_1_price), exchange="okcoin",
                                 sell_1_price=okcoin_sell_1_price)

            elif okcoin_buy_1_price > huobi_sell_1_price:  # 获利信号：OKcoin卖，huobi买
                self.timeLog("发现信号")
                self.timeLog("火币深度:%s" % str(huobiDepth))
                self.timeLog("okcoin深度:%s" % str(okcoinDepth))

                # 每次只能吃掉一定ratio的深度
                Qty = helper.downRound(min(huobi_sell_1_qty, okcoin_buy_1_qty) * self.orderRatio, 4)
                # 每次搬砖前要检查是否有足够security和cash
                Qty = min(Qty, accountInfo[helper.coinTypeStructure[self.coinMarketType]["okcoin"]["coin_str"]],
                          helper.downRound(accountInfo[helper.coinTypeStructure[self.coinMarketType]["huobi"][
                              "market_str"]] / huobi_sell_1_price), 4)
                Qty = helper.getRoundedQuantity(Qty, self.coinMarketType)

                if Qty < self.huobi_min_quantity or Qty < self.okcoin_min_quantity:
                    self.timeLog("数量:%f 小于交易所最小交易数量(火币最小数量:%f, okcoin最小数量:%f),因此无法下单并忽略该信号" % (
                        Qty, self.huobi_min_quantity, self.okcoin_min_quantity))
                    continue
                else:
                    # step1: 先处理卖
                    executed_qty = self.sell(self.coinMarketType, str(Qty), exchange="okcoin")
                    if executed_qty is not None:
                        # step2: 再执行买
                        Qty2 = min(executed_qty, Qty)
                        self.buy(self.coinMarketType, str(Qty2 * huobi_sell_1_price), exchange="huobi")
