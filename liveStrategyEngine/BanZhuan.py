#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################
#   获取更多免费策略，请加入WeQuant比特币量化策略交流QQ群：519538535
#   群主邮箱：lanjason@foxmail.com，群主微信/QQ：64008672
#   沉迷量化，无法自拔
###############################################################

import datetime
import logging

from huobi import HuobiService
from huobi.Util import *
from okcoin.Util import getOkcoinSpot
from common import helper
from common.Errors import StartRunningTimeEmptyError

class BanzhuanStrategy(object):
    def __init__(self, startRunningTime, orderRatio, timeInterval, orderWaitingTime, dataLogFixedTimeWindow, coinMarketType,
                 dailyExitTime=None):
        self.startRunningTime = startRunningTime
        self.orderRatio = orderRatio  # 每次预计能吃到的盘口深度的百分比
        self.timeInterval = timeInterval  # 每次循环结束之后睡眠的时间, 单位：秒
        self.orderWaitingTime = orderWaitingTime  # 每次等待订单执行的最长时间
        self.dataLogFixedTimeWindow = dataLogFixedTimeWindow  # in seconds
        self.coinMarketType = coinMarketType
        '''
        helper.COIN_TYPE_BTC_CNY = "btc_cny"
        helper.COIN_TYPE_LTC_CNY = "ltc_cny"
        '''

        self.dailyExitTime = dailyExitTime

        self.TimeFormatForFileName = "%Y%m%d%H%M%S%f"
        self.TimeFormatForLog = "%Y-%m-%d %H:%M:%S.%f"
        self.OKCoinService = getOkcoinSpot()
        self.HuobiService = HuobiService
        self.huobi_min = self.HuobiService.getMinimumOrderQty(helper.coinTypeStructure[self.coinMarketType]["huobi"]["coin_type"])
        self.okcoin_min = self.OKCoinService.getMinimumOrderQty(helper.coinTypeStructure[self.coinMarketType]["okcoin"]["coin_type"])
        self.last_data_log_time = None

        # setup timeLogger
        self.timeLogger = logging.getLogger('timeLog')
        self.timeLogger.setLevel(logging.DEBUG)
        self.timeLogHandler = logging.FileHandler(self.getTimeLogFileName())
        self.timeLogHandler.setLevel(logging.DEBUG)
        self.consoleLogHandler = logging.StreamHandler()
        self.consoleLogHandler.setLevel(logging.DEBUG)
        # 定义handler的输出格式
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
        return "../log/log_%s.txt" % self.getStartRunningTime().strftime(self.TimeFormatForFileName)

    def getDataLogFileName(self):
        return "../data/data_%s.data" % self.getStartRunningTime().strftime(self.TimeFormatForFileName)

    def timeLog(self, content):
        self.timeLogger.info(content)

    def getAccuntInfo(self):
        huobiAcct = self.HuobiService.getAccountInfo(helper.coinTypeStructure[self.coinMarketType]["huobi"]["market"],ACCOUNT_INFO)
        huobi_cny = float(huobiAcct[u'available_cny_display'])
        huobi_btc = float(huobiAcct[u'available_btc_display'])
        huobi_ltc = float(huobiAcct[u'available_ltc_display'])
        huobi_cny_loan = float(huobiAcct[u'loan_cny_display'])
        huobi_btc_loan = float(huobiAcct[u'loan_btc_display'])
        huobi_ltc_loan = float(huobiAcct[u'loan_ltc_display'])
        huobi_cny_frozen = float(huobiAcct[u'frozen_cny_display'])
        huobi_btc_frozen = float(huobiAcct[u'frozen_btc_display'])
        huobi_ltc_frozen = float(huobiAcct[u'frozen_ltc_display'])
        huobi_total = float(huobiAcct[u'total'])
        huobi_net = float(huobiAcct[u'net_asset'])

        okcoinAcct = self.OKCoinService.userinfo()
        okcoin_cny = float(okcoinAcct["info"]["funds"]["free"]["cny"])
        okcoin_btc = float(okcoinAcct["info"]["funds"]["free"]["btc"])
        okcoin_ltc = float(okcoinAcct["info"]["funds"]["free"]["ltc"])
        okcoin_cny_frozen = float(okcoinAcct["info"]["funds"]["freezed"]["cny"])
        okcoin_btc_frozen = float(okcoinAcct["info"]["funds"]["freezed"]["btc"])
        okcoin_ltc_frozen = float(okcoinAcct["info"]["funds"]["freezed"]["ltc"])
        okcoin_total = float(okcoinAcct["info"]["funds"]["asset"]["total"])
        okcoin_net = float(okcoinAcct["info"]["funds"]["asset"]["net"])
        total_net = huobi_net + okcoin_net
        return {
            "huobi_cny": huobi_cny,
            "huobi_btc": huobi_btc,
            "huobi_ltc": huobi_ltc,
            "huobi_cny_loan": huobi_cny_loan,
            "huobi_btc_loan": huobi_btc_loan,
            "huobi_ltc_loan": huobi_ltc_loan,
            "huobi_cny_frozen": huobi_cny_frozen,
            "huobi_btc_frozen": huobi_btc_frozen,
            "huobi_ltc_frozen": huobi_ltc_frozen,
            "huobi_total": huobi_total,
            "huobi_net": huobi_net,

            "okcoin_cny": okcoin_cny,
            "okcoin_btc": okcoin_btc,
            "okcoin_ltc": okcoin_ltc,
            "okcoin_cny_frozen": okcoin_cny_frozen,
            "okcoin_btc_frozen": okcoin_btc_frozen,
            "okcoin_ltc_frozen": okcoin_ltc_frozen,
            "okcoin_total": okcoin_total,
            "okcoin_net": okcoin_net,

            "total_net": total_net,
        }

    def dataLog(self, content=None):
        if content is None:
            accountInfo = self.getAccuntInfo()
            t = datetime.datetime.now()
            content = "%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s" % \
                      (t.strftime(self.TimeFormatForLog),
                       accountInfo["huobi_cny"],
                       accountInfo["huobi_btc"],
                       accountInfo["huobi_ltc"],
                       accountInfo["huobi_cny_loan"],
                       accountInfo["huobi_btc_loan"],
                       accountInfo["huobi_ltc_loan"],
                       accountInfo["huobi_cny_frozen"],
                       accountInfo["huobi_btc_frozen"],
                       accountInfo["huobi_ltc_frozen"],
                       accountInfo["huobi_total"],
                       accountInfo["huobi_net"],
                       accountInfo["okcoin_cny"],
                       accountInfo["okcoin_btc"],
                       accountInfo["okcoin_ltc"],
                       accountInfo["okcoin_cny_frozen"],
                       accountInfo["okcoin_btc_frozen"],
                       accountInfo["okcoin_ltc_frozen"],
                       accountInfo["okcoin_total"],
                       accountInfo["okcoin_net"],
                       accountInfo["total_net"])
            self.last_data_log_time = t
        self.dataLogger.info("%s" % str(content))

    def go(self):
        self.timeLog("log started at %s" % self.getStartRunningTime().strftime(self.TimeFormatForLog))
        self.dataLog(
            content="time|huobi_cny|huobi_btc|huobi_ltc|huobi_cny_loan|huobi_btc_loan|huobi_ltc_loan|huobi_cny_frozen|huobi_btc_frozen|huobi_ltc_frozen|huobi_total|huobi_net|okcoin_cny|okcoin_btc|okcoin_ltc|okcoin_cny_frozen|okcoin_btc_frozen|okcoin_ltc_frozen|okcoin_total|okcoin_net|total_net")
        self.dataLog()

        while (True):
            # check whether current time is after the dailyExitTime, if yes, exit
            if self.dailyExitTime is not None and datetime.datetime.now() > datetime.datetime.strptime(
                                    datetime.date.today().strftime("%Y-%m-%d") + " " + self.dailyExitTime,
                                    "%Y-%m-%d %H:%M:%S"):
                self.timeLog("Reach the EOD cutoff time %s, exit now." % self.dailyExitTime)
                break

            self.timeLog("waiting for %f seconds for next cycle..." % self.timeInterval)
            time.sleep(self.timeInterval)

            # calculate the net asset at a fixed time window
            time_diff = datetime.datetime.now() - self.last_data_log_time
            if time_diff.seconds > self.dataLogFixedTimeWindow:
                self.dataLog()

            # 获取当前账户信息
            accountInfo = self.getAccuntInfo()

            # 查询huobi第一档深度数据
            huobiDepth = self.HuobiService.getDepth(helper.coinTypeStructure[self.coinMarketType]["huobi"]["coin_type"],helper.coinTypeStructure[self.coinMarketType]["huobi"]["market"], depth_size=1)
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

            if huobi_buy_1_price > okcoin_sell_1_price:  # 获利信号：OKcoin买，huobi卖
                self.timeLog("Found signal")
                self.timeLog("huobiDepth:%s" % str(huobiDepth))
                self.timeLog("okcoinDepth:%s" % str(okcoinDepth))

                # 每次只能吃掉一定ratio的深度
                Qty = helper.myRound(min(huobi_buy_1_qty, okcoin_sell_1_qty) * self.orderRatio, 4)
                # 每次搬砖前要检查是否有足够security和cash
                Qty = min(Qty, accountInfo[helper.coinTypeStructure[self.coinMarketType]["huobi"]["coin_str"]], helper.myRound(accountInfo[helper.coinTypeStructure[self.coinMarketType]["okcoin"]["market_str"]] / okcoin_sell_1_price, 4))
                Qty = helper.myRound(Qty,4)
                Qty = helper.getRoundedQuantity(Qty, self.coinMarketType)

                if Qty < self.huobi_min or Qty < self.okcoin_min:
                    self.timeLog(
                        "Qty:%f is smaller than exchange minimum quantity(huobi min:%f, okcoin min:%f),so ignore this signal" % (
                        Qty, self.huobi_min, self.okcoin_min))
                    continue
                else:
                    # step1: 先处理卖
                    res = self.HuobiService.sellMarket(helper.coinTypeStructure[self.coinMarketType]["huobi"]["coin_type"], str(Qty), None, None, helper.coinTypeStructure[self.coinMarketType]["huobi"]["market"],SELL_MARKET)
                    if u"result" not in res or res[u"result"] != u'success':
                        self.timeLog("fail to place market sell order with qty %f into huobi" % Qty)
                        continue
                    order_id = res[u"id"]
                    # 查询订单执行情况
                    order_info = self.HuobiService.getOrderInfo(helper.coinTypeStructure[self.coinMarketType]["huobi"]["coin_type"], order_id, helper.coinTypeStructure[self.coinMarketType]["huobi"]["market"],ORDER_INFO)
                    self.timeLog("placed below market sell order into huobi with quantity: %f, cash amount:%.2f" % (Qty, helper.myRound(Qty * huobi_buy_1_price, 2)))
                    self.timeLog(str(order_info))
                    if order_info["status"] != 2:
                        self.timeLog("waiting for %f for order to be completed" % self.orderWaitingTime)
                        time.sleep(self.orderWaitingTime)
                        order_info = self.HuobiService.getOrderInfo(helper.coinTypeStructure[self.coinMarketType]["huobi"]["coin_type"], order_id, helper.coinTypeStructure[self.coinMarketType]["huobi"]["market"], ORDER_INFO)
                        self.timeLog(str(order_info))
                    executed_qty = float(order_info["processed_amount"])
                    self.timeLog("the market sell order in huobi has been executed with filled quantity: %f, received cash: %.2f" % (executed_qty, executed_qty*float(order_info["processed_price"])))
                    self.dataLog()

                    # step2: 再执行买
                    Qty2 = min(executed_qty, Qty)
                    Qty2 = max(helper.getRoundedQuantity(Qty2,self.coinMarketType),self.okcoin_min)
                    res2 = self.OKCoinService.trade(helper.coinTypeStructure[self.coinMarketType]["okcoin"]["coin_type"], "buy_market",
                                                    price=str(round(Qty2 * okcoin_sell_1_price, 2)))
                    if "result" not in res2 or res2["result"] != True:
                        self.timeLog("fail to place market buy order with qty %f into okcoin" % Qty2)
                        continue
                    order2_id = res2["order_id"]
                    # 查询订单执行情况
                    order2_info = self.OKCoinService.orderinfo(helper.coinTypeStructure[self.coinMarketType]["okcoin"]["coin_type"], str(order2_id))
                    self.timeLog("placed below market buy order into okcoin with quantity: %f, cash amount: %.2f" %(Qty2,round(Qty2 * okcoin_sell_1_price, 2)))
                    self.timeLog(str(order2_info))
                    if order2_info["orders"][0]["status"] != 2:
                        self.timeLog("waiting for %f for order to be completed" % self.orderWaitingTime)
                        time.sleep(self.orderWaitingTime)
                        order2_info = self.OKCoinService.orderinfo(helper.coinTypeStructure[self.coinMarketType]["okcoin"]["coin_type"], str(order2_id))
                        self.timeLog(str(order2_info))
                    executed_qty_2 = order2_info["orders"][0]["deal_amount"]
                    self.timeLog("the market buy order in okcoin has been executed with filled quantity: %f, spent cash: %.2f" % (executed_qty_2,executed_qty_2*order2_info["orders"][0]["avg_price"]))
                    self.dataLog()
            elif okcoin_buy_1_price > huobi_sell_1_price:  # 获利信号：OKcoin卖，huobi买
                self.timeLog("Found signal")
                self.timeLog("huobiDepth:%s" % str(huobiDepth))
                self.timeLog("okcoinDepth:%s" % str(okcoinDepth))

                # 每次只能吃掉一定ratio的深度
                Qty = helper.myRound(min(huobi_sell_1_qty, okcoin_buy_1_qty) * self.orderRatio, 4)
                # 每次搬砖前要检查是否有足够security和cash
                Qty = min(Qty, accountInfo[helper.coinTypeStructure[self.coinMarketType]["okcoin"]["coin_str"]], helper.myRound(accountInfo[helper.coinTypeStructure[self.coinMarketType]["huobi"]["market_str"]] / huobi_sell_1_price), 4)
                Qty = helper.getRoundedQuantity(Qty, self.coinMarketType)

                if Qty < self.huobi_min or Qty < self.okcoin_min:
                    self.timeLog(
                        "Qty:%f is smaller than exchange minimum quantity(huobi min:%f, okcoin min:%f),so ignore this signal" % (
                        Qty, self.huobi_min, self.okcoin_min))
                    continue
                else:
                    # step1: 先处理卖
                    res = self.OKCoinService.trade(helper.coinTypeStructure[self.coinMarketType]["okcoin"]["coin_type"], "sell_market", amount=str(Qty))
                    if "result" not in res or res["result"] != True:
                        self.timeLog("fail to place market sell order with qty %f into okcoin" % Qty)
                        continue
                    order_id = res["order_id"]
                    # 查询订单执行情况
                    order_info = self.OKCoinService.orderinfo(helper.coinTypeStructure[self.coinMarketType]["okcoin"]["coin_type"], str(order_id))
                    self.timeLog("placed below market sell order into okcoin with quantity: %f" % Qty)
                    self.timeLog(str(order_info))
                    if order_info["orders"][0]["status"] != 2:
                        self.timeLog("waiting for %f for order to be completed" % self.orderWaitingTime)
                        time.sleep(self.orderWaitingTime)
                        order_info = self.OKCoinService.orderinfo(helper.coinTypeStructure[self.coinMarketType]["okcoin"]["coin_type"], str(order_id))
                        self.timeLog(str(order_info))
                    executed_qty = order_info["orders"][0]["deal_amount"]
                    self.timeLog("the market sell order in okcoin has been executed with filled quantity: %f, received cash: %.2f" % (executed_qty,executed_qty*order_info["orders"][0]["avg_price"]))
                    self.dataLog()

                    # step2: 再执行买
                    Qty2 = min(executed_qty, Qty)
                    res2 = self.HuobiService.buyMarket(helper.coinTypeStructure[self.coinMarketType]["huobi"]["coin_type"], str(round(Qty2 * huobi_sell_1_price, 2)), None, None,helper.coinTypeStructure[self.coinMarketType]["huobi"]["market"],
                                                       BUY_MARKET)
                    if u"result" not in res2 or res2[u"result"] != u'success':
                        self.timeLog("fail to place market buy order with qty %f into huobi" % Qty2)
                        continue
                    order2_id = res2[u"id"]
                    # 查询订单执行情况
                    order2_info = self.HuobiService.getOrderInfo(helper.coinTypeStructure[self.coinMarketType]["huobi"]["coin_type"], order2_id, helper.coinTypeStructure[self.coinMarketType]["huobi"]["market"],ORDER_INFO)
                    self.timeLog("placed below market buy order into huobi with quantity: %f, cash amount:%.2f" % (Qty2, round(Qty2 * huobi_sell_1_price, 2)))
                    self.timeLog(str(order2_info))
                    if order2_info["status"] != 2:
                        self.timeLog("waiting for %f for order to be completed" % self.orderWaitingTime)
                        time.sleep(self.orderWaitingTime)
                        order2_info = self.HuobiService.getOrderInfo(helper.coinTypeStructure[self.coinMarketType]["huobi"]["coin_type"], order2_id, helper.coinTypeStructure[self.coinMarketType]["huobi"]["market"], ORDER_INFO)
                        self.timeLog(str(order2_info))
                    executed_qty_2 = float(order2_info["processed_amount"]) / float(order2_info["processed_price"])
                    self.timeLog("the market buy order in huobi has been executed with filled quantity: %f, spent cash: %.2f" % (executed_qty_2, float(order2_info["processed_amount"])))
                    self.dataLog()


if __name__ == "__main__":
    # btc
    strat = BanzhuanStrategy(datetime.datetime.now(), 0.8, 1, 0.1, 30, helper.COIN_TYPE_BTC_CNY, dailyExitTime="23:30:00")
    strat.go()

    '''
    # ltc
    strat = BanzhuanStrategy(datetime.datetime.now(), 0.8, 1, 0.1, 30, helper.COIN_TYPE_LTC_CNY, dailyExitTime="23:30:00")
    strat.go()
    '''



