#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################
#   获取更多免费策略，请加入WeQuant比特币量化策略交流QQ群：519538535
#   群主邮箱：lanjason@foxmail.com，群主微信/QQ：64008672
#   沉迷量化，无法自拔
###############################################################

import datetime
import logging

import numpy as np

from exchangeConnection.huobi import huobiService
from exchangeConnection.huobi.util import *
from exchangeConnection.okcoin.util import getOkcoinSpot
from utils import helper
from utils.errors import StartRunningTimeEmptyError


class StatArbSignalGenerator(object):
    def __init__(self, startRunningTime, orderRatio, timeInterval, orderWaitingTime, dataLogFixedTimeWindow,
                 coinMarketType, maximum_qty_multiplier=None, auto_rebalance_on=False,
                 auto_rebalance_on_exit=False,
                 dailyExitTime=None):
        self.startRunningTime = startRunningTime
        self.orderRatio = orderRatio  # 每次预计能吃到的盘口深度的百分比
        self.timeInterval = timeInterval  # 每次循环结束之后睡眠的时间, 单位：秒
        self.orderWaitingTime = orderWaitingTime  # 每次等待订单执行的最长时间
        self.coinMarketType = coinMarketType
        self.dailyExitTime = dailyExitTime
        self.TimeFormatForFileName = "%Y%m%d%H%M%S%f"
        self.TimeFormatForLog = "%Y-%m-%d %H:%M:%S.%f"
        self.OKCoinService = getOkcoinSpot()
        self.HuobiService = huobiService
        self.huobi_min_quantity = self.HuobiService.getMinimumOrderQty(
            helper.coinTypeStructure[self.coinMarketType]["huobi"]["coin_type"])
        self.huobi_min_cash_amount = self.HuobiService.getMinimumOrderCashAmount()
        self.okcoin_min_quantity = self.OKCoinService.getMinimumOrderQty(
            helper.coinTypeStructure[self.coinMarketType]["okcoin"]["coin_type"])
        # okcoin 的比特币最小市价买单下单金额是：0.01BTC*比特币当时市价
        # okcoin 的莱特币最小市价买单下单金额是：0.1LTC*莱特币当时市价
        self.last_data_log_time = None

        # setup timeLogger
        self.timeLogger = helper.TimeLogger(self.getTimeLogFileName())
        self.dataLogFixedTimeWindow = dataLogFixedTimeWindow
        # setup dataLogger
        self.dataLogger = logging.getLogger('dataLog')
        self.dataLogger.setLevel(logging.DEBUG)
        self.dataLogHandler = logging.FileHandler(self.getDataLogFileName())
        self.dataLogHandler.setLevel(logging.DEBUG)
        self.dataLogger.addHandler(self.dataLogHandler)

        # spread list and other open/close conditions
        self.spread1List = []  # huobi_buy1 - okcoin_sell1
        self.spread2List = []  # okcoin_buy1 - huobi_sell1
        self.spread1_mean = None
        self.spread1_stdev = None
        self.spread2_mean = None
        self.spread2_stdev = None
        self.sma_window_size = 10
        self.spread1_open_condition_stdev_coe = 2
        self.spread2_open_condition_stdev_coe = 2
        self.spread1_close_condition_stdev_coe = 0.3
        self.spread2_close_condition_stdev_coe = 0.3
        self.current_position_direction = 0  # 1: long spread1(buy okcoin, sell huobi);  2: long spread2( buy huobi, sell okcoin), 0: no position
        self.spread1_pos_qty = 0
        self.spread2_pos_qty = 0
        self.position_proportion_alert_threshold = 0.80  # if position proportion > position_proportion_alert_threshold, generate alerts
        self.position_proportion_threshold = 0.90  # if position proportion > position_proportion_threshold, stop upsizing, only allow downsizing
        self.spread_pos_qty_minimum_size = max(self.okcoin_min_quantity, self.huobi_min_quantity) * 1.5

        # rebalance setup
        self.rebalanced_position_proportion = 0.5
        self.auto_rebalance_on = auto_rebalance_on
        self.auto_rebalance_on_exit = auto_rebalance_on_exit

        # add order query retry maximum times
        self.huobi_order_query_retry_maximum_times = 5
        self.okcoin_order_query_retry_maximum_times = 5

        # add order "cancellation" query retry maximum times
        self.huobi_order_cancel_query_retry_maximum_times = 5
        self.okcoin_order_cancel_query_retry_maximum_times = 5

        # 每次最多可以搬得最小单位倍数
        self.maximum_qty_multiplier = maximum_qty_multiplier

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

    def timeLog(self, content, level=logging.INFO):
        self.timeLogger.timeLog(content, level=level)

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

    def getAccuntInfo(self):
        huobiAcct = self.HuobiService.getAccountInfo(helper.coinTypeStructure[self.coinMarketType]["huobi"]["market"],
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

        okcoinAcct = self.OKCoinService.userinfo()
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

    # 限价卖单
    def sell_limit(self, security, price, quantity, exchange="huobi"):  # price, quantity are in string format
        if exchange == "huobi":
            self.timeLog("开始下达火币限价卖单...")
            self.timeLog("只保留下单数量的小数点后4位，下单价格的小数点后2位...")
            self.timeLog("原始下单数量:%s" % quantity)
            tmp = float(quantity)
            tmp = helper.downRound(tmp, 4)
            quantity = str(tmp)
            self.timeLog("做完小数点处理后的下单数量:%s" % quantity)
            if float(quantity) < self.huobi_min_quantity:
                self.timeLog(
                    "数量:%s 小于交易所最小交易数量(火币最小数量:%f),因此无法下单,此处忽略该信号" % (quantity, self.huobi_min_quantity),
                    level=logging.WARN)
                return None

            self.timeLog("原始下单价格:%s" % price)
            tmp = float(price)
            tmp = helper.downRound(tmp, 2)
            price = str(tmp)
            self.timeLog("做完小数点处理后的下单价格:%s" % price)

            coin_type = helper.coinTypeStructure[self.coinMarketType]["huobi"]["coin_type"]
            market = helper.coinTypeStructure[self.coinMarketType]["huobi"]["market"]

            res = self.HuobiService.sell(coin_type, price, quantity, None, None, market, SELL)
            if helper.componentExtract(res, u"result", "") != u'success':
                self.timeLog("下达火币限价卖单（数量：%s, 价格：%s）失败, 结果是: %s！" % (
                    quantity, price, helper.componentExtract(res, u"result", "")),
                             level=logging.ERROR)
                return None

            order_id = res[u"id"]
            # 查询订单执行情况
            order_info = self.HuobiService.getOrderInfo(coin_type, order_id, market, ORDER_INFO)
            self.timeLog("下达如下火币限价卖单，数量：%s, 价格：%s" % (quantity, price))
            self.timeLog(str(order_info))

            retry_time = 0
            while retry_time < self.huobi_order_query_retry_maximum_times and order_info["status"] != 2:
                self.timeLog("等待%f秒直至订单完成" % self.orderWaitingTime)
                time.sleep(self.orderWaitingTime)
                order_info = self.HuobiService.getOrderInfo(coin_type, order_id, market, ORDER_INFO)
                self.timeLog(str(order_info))
                retry_time += 1

            # if order is not fully filled, cancel order if after timeout, cancel order is synchronized
            if order_info["status"] != 2:
                cancel_result = self.HuobiService.cancelOrder(coin_type, order_id, market, CANCEL_ORDER)
                retry_time = 0
                while retry_time < self.huobi_order_cancel_query_retry_maximum_times and helper.componentExtract(
                        cancel_result, u"result", "") != u'success':
                    self.timeLog("等待%f秒直至订单取消完成" % self.orderWaitingTime)
                    time.sleep(self.orderWaitingTime)
                    cancel_result = self.HuobiService.cancelOrder(coin_type, order_id, market, CANCEL_ORDER)
                    retry_time += 1
                order_info = self.HuobiService.getOrderInfo(coin_type, order_id, market, ORDER_INFO)

            executed_qty = float(order_info["processed_amount"])
            self.timeLog(
                "火币限价卖单已被执行，执行数量：%f，收到的现金：%.2f" % (executed_qty, executed_qty * float(order_info["processed_price"])))
            return executed_qty
        elif exchange == "okcoin":
            self.timeLog("开始下达okcoin限价卖单...")
            self.timeLog("只保留下单数量的小数点后2位...")
            self.timeLog("原始下单数量:%s" % quantity)
            tmp = float(quantity)
            tmp = helper.downRound(tmp, 2)
            quantity = str(tmp)
            self.timeLog("做完小数点处理后的下单数量:%s" % quantity)
            if float(quantity) < self.okcoin_min_quantity:
                self.timeLog(
                    "数量:%s 小于交易所最小交易数量(okcoin最小数量:%f),因此无法下单,此处忽略该信号" % (quantity, self.okcoin_min_quantity),
                    level=logging.WARN)
                return None

            self.timeLog("原始下单价格:%s" % price)
            tmp = float(price)
            tmp = helper.downRound(tmp, 2)
            price = str(tmp)
            self.timeLog("做完小数点处理后的下单价格:%s" % price)

            coin_type = helper.coinTypeStructure[self.coinMarketType]["okcoin"]["coin_type"]

            res = self.OKCoinService.trade(coin_type, "sell", price=price, amount=quantity)
            if helper.componentExtract(res, "result") != True:
                self.timeLog(
                    "下达okcoin限价卖单（数量：%s, 价格：%s）失败, 结果是：%s" % (quantity, price, helper.componentExtract(res, "result")),
                    level=logging.ERROR)
                return None
            order_id = res["order_id"]
            # 查询订单执行情况
            order_info = self.OKCoinService.orderinfo(coin_type, str(order_id))
            self.timeLog("下达如下okcoin限价卖单，数量：%s, 价格：%s" % (quantity, price))
            self.timeLog(str(order_info))

            retry_time = 0
            while retry_time < self.okcoin_order_query_retry_maximum_times and order_info["orders"][0]["status"] != 2:
                self.timeLog("等待%.1f秒直至订单完成" % self.orderWaitingTime)
                time.sleep(self.orderWaitingTime)
                order_info = self.OKCoinService.orderinfo(coin_type, str(order_id))
                self.timeLog(str(order_info))
                retry_time += 1

            if order_info["orders"][0]["status"] != 2:
                cancel_result = self.OKCoinService.CancelOrder(coin_type, str(order_id))
                retry_time = 0
                while retry_time < self.okcoin_order_cancel_query_retry_maximum_times and helper.componentExtract(
                        cancel_result, u"result", "") != True:
                    self.timeLog("等待%f秒直至订单取消完成" % self.orderWaitingTime)
                    time.sleep(self.orderWaitingTime)
                    cancel_result = self.OKCoinService.CancelOrder(coin_type, str(order_id))
                    retry_time += 1
                order_info = self.OKCoinService.orderinfo(coin_type, str(order_id))

            executed_qty = order_info["orders"][0]["deal_amount"]
            self.timeLog("okcoin限价卖单已被执行，执行数量：%f，收到的现金：%.2f" % (
                executed_qty, executed_qty * order_info["orders"][0]["avg_price"]))
            return executed_qty

    # 市价卖单
    def sell_market(self, security, quantity, exchange="huobi"):  # quantity is a string value
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
                    "数量:%s 小于交易所最小交易数量(火币最小数量:%f),因此无法下单,此处忽略该信号" % (quantity, self.huobi_min_quantity),
                    level=logging.WARN)
                return None

            coin_type = helper.coinTypeStructure[self.coinMarketType]["huobi"]["coin_type"]
            market = helper.coinTypeStructure[self.coinMarketType]["huobi"]["market"]

            res = self.HuobiService.sellMarket(coin_type, quantity, None, None, market, SELL_MARKET)
            if helper.componentExtract(res, u"result", "") != u'success':
                self.timeLog("下达火币市价卖单（数量：%s）失败, 结果是: %s！" % (quantity, helper.componentExtract(res, u"result", "")),
                             level=logging.ERROR)
                return None
            order_id = res[u"id"]
            # 查询订单执行情况
            order_info = self.HuobiService.getOrderInfo(coin_type, order_id, market, ORDER_INFO)
            self.timeLog("下达如下火币市价卖单，数量：%s" % quantity)
            self.timeLog(str(order_info))

            retry_time = 0
            while retry_time < self.huobi_order_query_retry_maximum_times and order_info["status"] != 2:
                self.timeLog("等待%f秒直至订单完成" % self.orderWaitingTime)
                time.sleep(self.orderWaitingTime)
                order_info = self.HuobiService.getOrderInfo(coin_type, order_id, market, ORDER_INFO)
                self.timeLog(str(order_info))
                retry_time += 1

            executed_qty = float(order_info["processed_amount"])
            self.timeLog(
                "火币市价卖单已被执行，执行数量：%f，收到的现金：%.2f" % (executed_qty, executed_qty * float(order_info["processed_price"])))
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
                    "数量:%s 小于交易所最小交易数量(火币最小数量:%f),因此无法下单,此处忽略该信号" % (quantity, self.okcoin_min_quantity),
                    level=logging.WARN)
                return None

            coin_type = helper.coinTypeStructure[self.coinMarketType]["okcoin"]["coin_type"]

            res = self.OKCoinService.trade(coin_type, "sell_market", amount=quantity)
            if helper.componentExtract(res, "result") != True:
                self.timeLog("下达okcoin市价卖单（数量：%s）失败, 结果是：%s" % (quantity, helper.componentExtract(res, "result")),
                             level=logging.ERROR)
                return None
            order_id = res["order_id"]
            # 查询订单执行情况
            order_info = self.OKCoinService.orderinfo(coin_type, str(order_id))
            self.timeLog("下达如下okcoin市价卖单，数量：%s" % quantity)
            self.timeLog(str(order_info))

            retry_time = 0
            while retry_time < self.okcoin_order_query_retry_maximum_times and order_info["orders"][0]["status"] != 2:
                self.timeLog("等待%.1f秒直至订单完成" % self.orderWaitingTime)
                time.sleep(self.orderWaitingTime)
                order_info = self.OKCoinService.orderinfo(coin_type, str(order_id))
                self.timeLog(str(order_info))
                retry_time += 1

            executed_qty = order_info["orders"][0]["deal_amount"]
            self.timeLog("okcoin市价卖单已被执行，执行数量：%f，收到的现金：%.2f" % (
                executed_qty, executed_qty * order_info["orders"][0]["avg_price"]))
            return executed_qty

    # 限价买单
    def buy_limit(self, security, price, quantity, exchange="huobi"):
        if exchange == "huobi":
            self.timeLog("开始下达火币限价买单...")
            self.timeLog("只保留下单数量的小数点后4位，下单价格的小数点后2位...")
            self.timeLog("原始下单数量:%s" % quantity)
            tmp = float(quantity)
            tmp = helper.downRound(tmp, 4)
            quantity = str(tmp)
            self.timeLog("做完小数点处理后的下单数量:%s" % quantity)

            if float(quantity) < self.huobi_min_quantity:
                self.timeLog(
                    "数量:%s 小于交易所最小交易数量(火币最小数量:%f),因此无法下单,此处忽略该信号" % (quantity, self.huobi_min_quantity),
                    level=logging.WARN)
                return None

            self.timeLog("原始下单价格:%s" % price)
            tmp = float(price)
            tmp = helper.downRound(tmp, 2)
            price = str(tmp)
            self.timeLog("做完小数点处理后的下单价格:%s" % price)

            coin_type = helper.coinTypeStructure[self.coinMarketType]["huobi"]["coin_type"]
            market = helper.coinTypeStructure[self.coinMarketType]["huobi"]["market"]

            res = self.HuobiService.buy(coin_type, price, quantity, None, None, market, BUY)
            if helper.componentExtract(res, u"result", "") != u'success':
                self.timeLog(
                    "下达火币限价买单（数量：%s，价格：%s）失败, 结果是：%s！" % (quantity, price, helper.componentExtract(res, u"result", "")),
                    level=logging.ERROR)
                return None
            order_id = res[u"id"]
            # 查询订单执行情况
            order_info = self.HuobiService.getOrderInfo(coin_type, order_id, market, ORDER_INFO)
            self.timeLog("下达如下火币限价买单，数量：%s, 价格：%s" % (quantity, price))
            self.timeLog(str(order_info))

            retry_time = 0
            while retry_time < self.huobi_order_query_retry_maximum_times and order_info["status"] != 2:
                self.timeLog("等待%f秒直至订单完成" % self.orderWaitingTime)
                time.sleep(self.orderWaitingTime)
                order_info = self.HuobiService.getOrderInfo(coin_type, order_id, market, ORDER_INFO)
                self.timeLog(str(order_info))
                retry_time += 1

                # if order is not fully filled, cancel order if after timeout, cancel order is synchronized
            if order_info["status"] != 2:
                cancel_result = self.HuobiService.cancelOrder(coin_type, order_id, market, CANCEL_ORDER)
                retry_time = 0
                while retry_time < self.huobi_order_cancel_query_retry_maximum_times and helper.componentExtract(
                        cancel_result, u"result", "") != u'success':
                    self.timeLog("等待%f秒直至订单取消完成" % self.orderWaitingTime)
                    time.sleep(self.orderWaitingTime)
                    cancel_result = self.HuobiService.cancelOrder(coin_type, order_id, market, CANCEL_ORDER)
                    retry_time += 1
                order_info = self.HuobiService.getOrderInfo(coin_type, order_id, market, ORDER_INFO)

            if float(order_info["processed_price"]) > 0:
                executed_qty = float(order_info["processed_amount"])
                self.timeLog("火币限价买单已被执行，执行数量：%f，花费的现金：%.2f" % (
                    executed_qty, float(order_info["processed_price"]) * executed_qty))
                return executed_qty
            else:
                self.timeLog("火币限价买单未被执行", level=logging.WARN)
                return None

        elif exchange == "okcoin":
            self.timeLog("开始下达okcoin限价买单...")
            self.timeLog("只保留下单数量的小数点后2位...")
            self.timeLog("原始下单数量:%s" % quantity)
            tmp = float(quantity)
            tmp = helper.downRound(tmp, 2)
            quantity = str(tmp)
            self.timeLog("做完小数点处理后的下单数量:%s" % quantity)
            if float(quantity) < self.okcoin_min_quantity:
                self.timeLog(
                    "数量:%s 小于交易所最小交易数量(okcoin最小数量:%f),因此无法下单,此处忽略该信号" % (quantity, self.okcoin_min_quantity),
                    level=logging.WARN)
                return None

            self.timeLog("原始下单价格:%s" % price)
            tmp = float(price)
            tmp = helper.downRound(tmp, 2)
            price = str(tmp)
            self.timeLog("做完小数点处理后的下单价格:%s" % price)

            coin_type = helper.coinTypeStructure[self.coinMarketType]["okcoin"]["coin_type"]

            res = self.OKCoinService.trade(coin_type, "buy", price=price, amount=quantity)

            if helper.componentExtract(res, "result") != True:
                self.timeLog(
                    "下达okcoin限价买单（数量：%s，价格：%s）失败, 结果是：%s！" % (quantity, price, helper.componentExtract(res, "result")),
                    level=logging.ERROR)
                return None

            order_id = res["order_id"]
            # 查询订单执行情况
            order_info = self.OKCoinService.orderinfo(coin_type, str(order_id))
            self.timeLog("下达如下okcoin限价买单，数量：%s，价格：%s" % (quantity, price))
            self.timeLog(str(order_info))

            retry_time = 0
            while retry_time < self.okcoin_order_query_retry_maximum_times and order_info["orders"][0]["status"] != 2:
                self.timeLog("等待%.1f秒直至订单完成" % self.orderWaitingTime)
                time.sleep(self.orderWaitingTime)
                order_info = self.OKCoinService.orderinfo(coin_type, str(order_id))
                self.timeLog(str(order_info))
                retry_time += 1

            if order_info["orders"][0]["status"] != 2:
                cancel_result = self.OKCoinService.CancelOrder(coin_type, str(order_id))
                retry_time = 0
                while retry_time < self.okcoin_order_cancel_query_retry_maximum_times and helper.componentExtract(
                        cancel_result, u"result", "") != True:
                    self.timeLog("等待%f秒直至订单取消完成" % self.orderWaitingTime)
                    time.sleep(self.orderWaitingTime)
                    cancel_result = self.OKCoinService.CancelOrder(coin_type, str(order_id))
                    retry_time += 1
                order_info = self.OKCoinService.orderinfo(coin_type, str(order_id))

            executed_qty = order_info["orders"][0]["deal_amount"]
            self.timeLog("okcoin限价买单已被执行，执行数量：%f，花费的现金：%.2f" % (
                executed_qty, executed_qty * order_info["orders"][0]["avg_price"]))
            return executed_qty

    # 市价买单
    def buy_market(self, security, cash_amount, exchange="huobi", sell_1_price=None):  # cash_amount is a string value
        if exchange == "huobi":
            self.timeLog("开始下达火币市价买单...")
            self.timeLog("只保留下单数量的小数点后2位...")
            self.timeLog("原始下单金额:%s" % cash_amount)
            tmp = float(cash_amount)
            tmp = helper.downRound(tmp, 2)
            cash_amount = str(tmp)
            self.timeLog("做完小数点处理后的下单金额:%s" % cash_amount)

            if float(cash_amount) < self.huobi_min_cash_amount:
                self.timeLog("金额:%s 小于交易所最小交易金额(火币最小金额:1元),因此无法下单,此处忽略该信号" % (cash_amount, self.huobi_min_cash_amount),
                             level=logging.WARN)
                return None

            coin_type = helper.coinTypeStructure[self.coinMarketType]["huobi"]["coin_type"]
            market = helper.coinTypeStructure[self.coinMarketType]["huobi"]["market"]

            res = self.HuobiService.buyMarket(coin_type, cash_amount, None, None, market, BUY_MARKET)
            if helper.componentExtract(res, u"result", "") != u'success':
                self.timeLog("下达火币市价买单（金额：%s）失败, 结果是：%s！" % (cash_amount, helper.componentExtract(res, u"result", "")),
                             level=logging.ERROR)
                return None
            order_id = res[u"id"]
            # 查询订单执行情况
            order_info = self.HuobiService.getOrderInfo(coin_type, order_id, market, ORDER_INFO)
            self.timeLog("下达如下火币市价买单，金额：%s" % cash_amount)
            self.timeLog(str(order_info))

            retry_time = 0
            while retry_time < self.huobi_order_query_retry_maximum_times and order_info["status"] != 2:
                self.timeLog("等待%f秒直至订单完成" % self.orderWaitingTime)
                time.sleep(self.orderWaitingTime)
                order_info = self.HuobiService.getOrderInfo(coin_type, order_id, market, ORDER_INFO)
                self.timeLog(str(order_info))
                retry_time += 1

            if float(order_info["processed_price"]) > 0:
                executed_qty = float(order_info["processed_amount"]) / float(order_info["processed_price"])
                self.timeLog("火币市价买单已被执行，执行数量：%f，花费的现金：%.2f" % (executed_qty, float(order_info["processed_amount"])))
                return executed_qty
            else:
                self.timeLog("火币市价买单未被执行", level=logging.WARN)
                return 0

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
                        cash_amount, self.okcoin_min_quantity, sell_1_price, self.okcoin_min_quantity * sell_1_price),
                    level=logging.WARN)
                return None

            coin_type = helper.coinTypeStructure[self.coinMarketType]["okcoin"]["coin_type"]
            res = self.OKCoinService.trade(coin_type, "buy_market", price=cash_amount)

            if helper.componentExtract(res, "result") != True:
                self.timeLog("下达okcoin市价买单（金额：%s）失败, 结果是：%s！" % (cash_amount, helper.componentExtract(res, "result")),
                             level=logging.ERROR)
                return None
            order_id = res["order_id"]
            # 查询订单执行情况
            order_info = self.OKCoinService.orderinfo(coin_type, str(order_id))
            self.timeLog("下达如下okcoin市价买单，金额：%s" % cash_amount)
            self.timeLog(str(order_info))

            retry_time = 0
            while retry_time < self.okcoin_order_query_retry_maximum_times and order_info["orders"][0]["status"] != 2:
                self.timeLog("等待%.1f秒直至订单完成" % self.orderWaitingTime)
                time.sleep(self.orderWaitingTime)
                order_info = self.OKCoinService.orderinfo(coin_type, str(order_id))
                self.timeLog(str(order_info))
                retry_time += 1

            executed_qty = order_info["orders"][0]["deal_amount"]
            self.timeLog("okcoin市价买单已被执行，执行数量：%f，花费的现金：%.2f" % (
                executed_qty, executed_qty * order_info["orders"][0]["avg_price"]))
            return executed_qty

    # 再平衡仓位
    def rebalance_position(self, accountInfo, price):
        current_huobi_pos_value = accountInfo[
                                      helper.coinTypeStructure[self.coinMarketType]["huobi"]["coin_str"]] * price
        target_huobi_pos_value = accountInfo["huobi_cny_net"] * self.rebalanced_position_proportion
        if target_huobi_pos_value - current_huobi_pos_value > self.spread_pos_qty_minimum_size * price:  # need to buy
            self.timeLog("触发再平衡信号，增加huobi仓位", level=logging.WARN)
            self.buy_market(self.coinMarketType, str(target_huobi_pos_value - current_huobi_pos_value),
                            exchange="huobi")
        elif current_huobi_pos_value - target_huobi_pos_value > self.spread_pos_qty_minimum_size * price:  # need to sell
            self.timeLog("触发再平衡信号，减小huobi仓位", level=logging.WARN)
            self.sell_market(self.coinMarketType, str((current_huobi_pos_value - target_huobi_pos_value) / price),
                             exchange="huobi")

        current_okcoin_pos_value = accountInfo[
                                       helper.coinTypeStructure[self.coinMarketType]["okcoin"]["coin_str"]] * price
        target_okcoin_pos_value = accountInfo["okcoin_cny_net"] * self.rebalanced_position_proportion
        if target_okcoin_pos_value - current_okcoin_pos_value > self.spread_pos_qty_minimum_size * price:  # need to buy
            self.timeLog("触发再平衡信号，增加okcoin仓位", level=logging.WARN)
            self.buy_market(self.coinMarketType, str(target_okcoin_pos_value - current_okcoin_pos_value),
                            exchange="okcoin",
                            sell_1_price=price)
        elif current_okcoin_pos_value - target_okcoin_pos_value > self.spread_pos_qty_minimum_size * price:  # need to sell
            self.timeLog("触发再平衡信号，减小okcoin仓位", level=logging.WARN)
            self.sell_market(self.coinMarketType, str((current_okcoin_pos_value - target_okcoin_pos_value) / price),
                             exchange="okcoin")

        self.current_position_direction = 0  # 1: long spread1(buy okcoin, sell huobi);  2: long spread2( buy huobi, sell okcoin), 0: no position
        self.spread1_pos_qty = 0
        self.spread2_pos_qty = 0

    # 获取现在的持仓比例,取火币和okcoin的持仓比例、现金比例的最大值
    def get_current_position_proportion(self, accountInfo, price):
        huobi_net = accountInfo["huobi_cny_net"]
        huobi_pos_value = accountInfo[helper.coinTypeStructure[self.coinMarketType]["huobi"]["coin_str"]] * price
        huobi_cash_value = accountInfo["huobi_cny_cash"]
        okcoin_net = accountInfo["okcoin_cny_net"]
        okcoin_pos_value = accountInfo[helper.coinTypeStructure[self.coinMarketType]["okcoin"]["coin_str"]] * price
        okcoin_cash_value = accountInfo["okcoin_cny_cash"]
        if huobi_net == 0:
            raise ValueError("您在火币的净资产为零，无法做价差套利，请上huobi.com充值！")
        if okcoin_net == 0:
            raise ValueError("您在OKCoin的净资产为零，无法做价差套利，请上okcoin.cn充值！")
        return np.max([huobi_pos_value / huobi_net, huobi_cash_value / huobi_net, okcoin_pos_value / okcoin_net,
                       okcoin_cash_value / okcoin_net])

    # 计算移动平均
    def calc_sma_and_deviation(self):
        self.spread1_mean = np.mean(self.spread1List[-1 * self.sma_window_size:])
        self.spread1_stdev = np.std(self.spread1List[-1 * self.sma_window_size:])
        self.spread2_mean = np.mean(self.spread2List[-1 * self.sma_window_size:])
        self.spread2_stdev = np.std(self.spread2List[-1 * self.sma_window_size:])

    # 判断开仓、平仓
    def in_or_out(self):
        if self.current_position_direction == 0:  # currently no spread position
            if (self.spread1List[
                    -1] - self.spread1_mean) / self.spread1_stdev > self.spread1_open_condition_stdev_coe:  # huobi > okcoin
                return 1  # buy okcoin, sell huobi
            elif (self.spread2List[
                      -1] - self.spread2_mean) / self.spread2_stdev > self.spread2_open_condition_stdev_coe:  # okcoin > huobi
                return 2  # sell okcoin, buy huobi
        elif self.current_position_direction == 1:  # currently long spread1
            if (self.spread1List[
                    -1] - self.spread1_mean) / self.spread1_stdev > self.spread1_open_condition_stdev_coe:  # huobi > okcoin
                return 1  # continue to buy okcoin, sell huobi, meaning upsizing spread1
            if (self.spread1List[-1] - self.spread1_mean) / self.spread1_stdev < self.spread1_close_condition_stdev_coe:
                return 2  # unwind spread1
        elif self.current_position_direction == 2:  # currently long spread1
            if (self.spread2List[
                    -1] - self.spread2_mean) / self.spread2_stdev > self.spread2_open_condition_stdev_coe:  # okcoin > huobi
                return 2  # continue to sell okcoin, buy huobi, meaning upsizing spread2
            if (self.spread2List[-1] - self.spread2_mean) / self.spread2_stdev < self.spread2_close_condition_stdev_coe:
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

            if len(self.spread1List) < self.sma_window_size:
                self.timeLog("正在获取计算SMA所需的最小数据量(%d/%d)..." % (len(self.spread1List), self.sma_window_size))
                continue

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

            self.calc_sma_and_deviation()

            if self.auto_rebalance_on and current_position_proportion > self.position_proportion_threshold:
                if abs(self.spread2List[
                           -1] - self.spread2_mean) / self.spread2_stdev < self.spread2_close_condition_stdev_coe or abs(
                            self.spread1List[
                                -1] - self.spread1_mean) / self.spread1_stdev < self.spread1_close_condition_stdev_coe:
                    self.rebalance_position(accountInfo, max_price)
                continue

            in_or_out = self.in_or_out()
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
                    Qty = min(Qty,
                              max(self.huobi_min_quantity, self.okcoin_min_quantity) * self.maximum_qty_multiplier)

                # 每次搬砖前要检查是否有足够security和cash
                Qty = min(Qty, accountInfo[helper.coinTypeStructure[self.coinMarketType]["huobi"]["coin_str"]],
                          helper.downRound(accountInfo[helper.coinTypeStructure[self.coinMarketType]["okcoin"][
                              "market_str"]] / okcoin_sell_1_price, 4))
                Qty = helper.downRound(Qty, 4)
                Qty = helper.getRoundedQuantity(Qty, self.coinMarketType)

                if Qty < self.huobi_min_quantity or Qty < self.okcoin_min_quantity:
                    self.timeLog(
                        "数量:%f 小于交易所最小交易数量(火币最小数量:%f, okcoin最小数量:%f),因此无法下单并忽略该信号" % (
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
                    Qty = min(Qty,
                              max(self.huobi_min_quantity, self.okcoin_min_quantity) * self.maximum_qty_multiplier)

                # 每次搬砖前要检查是否有足够security和cash
                Qty = min(Qty, accountInfo[helper.coinTypeStructure[self.coinMarketType]["okcoin"]["coin_str"]],
                          helper.downRound(accountInfo[helper.coinTypeStructure[self.coinMarketType]["huobi"][
                              "market_str"]] / huobi_sell_1_price), 4)
                Qty = helper.getRoundedQuantity(Qty, self.coinMarketType)

                if Qty < self.huobi_min_quantity or Qty < self.okcoin_min_quantity:
                    self.timeLog("数量:%f 小于交易所最小交易数量(火币最小数量:%f, okcoin最小数量:%f),因此无法下单并忽略该信号" % (
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
