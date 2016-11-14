#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################
#   获取更多免费策略，请加入WeQuant比特币量化策略交流QQ群：519538535
#   群主邮箱：lanjason@foxmail.com，群主微信/QQ：64008672
#   沉迷量化，无法自拔
###############################################################


import datetime
import logging

import huobi.history as history
from common.Account import Account
from common.Data import Data
from common.Errors import StartRunningTimeEmptyError
from common.Errors import TypeError
from common.Order import Order
from common.Time import Time
from common.UserData import UserData
from huobi import HuobiService
from huobi.Util import *


class BaseLiveStrategyEngine(object):
    def __init__(self, strat, startRunningTime, orderWaitingTime, dataLogFixedTimeWindow, dailyExitTime=None):
        self.strat = strat
        self.user_data = UserData()
        self.strat.initialize(self)
        self.startRunningTime = startRunningTime
        self.timeInterval = history.frequency_to_seconds[self.frequency]# 每次循环结束之后睡眠的时间, 单位：秒
        self.orderWaitingTime = orderWaitingTime  # 每次等待订单执行的最长时间
        self.dataLogFixedTimeWindow = dataLogFixedTimeWindow  # 每隔固定的时间打印账单信息，单位：秒

        if self.security == "huobi_cny_btc":
            self.coinMarketType = helper.COIN_TYPE_BTC_CNY
        elif self.security == "huobi_cny_ltc":
            self.coinMarketType = helper.COIN_TYPE_LTC_CNY
        else:
            raise TypeError("invalid security name '%s'"%self.security)

        self.dailyExitTime      = dailyExitTime #如果设置，则为每天程序的退出时间
        self.TimeFormatForFileName = "%Y%m%d%H%M%S%f"
        self.TimeFormatForLog = "%Y-%m-%d %H:%M:%S.%f"
        self.HuobiService = HuobiService

        if self.coinMarketType in ["btc_cny","btc_usd"]:
            coin_type = 1
        else:
            coin_type = 2

        self.huobi_min = self.HuobiService.getMinimumOrderQty(coin_type)
        self.last_data_log_time = None

        # setup timeLogger
        self.timeLogger = logging.getLogger('timeLog')
        self.timeLogger.setLevel(logging.DEBUG)
        timeLogHandler = logging.FileHandler(self.getTimeLogFileName())
        timeLogHandler.setLevel(logging.DEBUG)
        consoleLogHandler = logging.StreamHandler()
        consoleLogHandler.setLevel(logging.DEBUG)
        # 定义handler的输出格式
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        timeLogHandler.setFormatter(formatter)
        consoleLogHandler.setFormatter(formatter)
        # 给timeLogger添加handler
        self.timeLogger.addHandler(timeLogHandler)
        self.timeLogger.addHandler(consoleLogHandler)

        # setup dataLogger
        self.dataLogger = logging.getLogger('dataLog')
        self.dataLogger.setLevel(logging.DEBUG)
        dataLogHandler = logging.FileHandler(self.getDataLogFileName())
        dataLogHandler.setLevel(logging.DEBUG)
        self.dataLogger.addHandler(dataLogHandler)

        self.log = self.timeLogger

        data = Data()
        data.get_price = history.get_price
        data.get_current_price=history.get_current_price
        data.get_all_securities = history.get_all_securities
        self.data = data

        order = Order()
        order.buy = self.buy
        order.buy_limit = self.buy_limit
        order.sell = self.sell
        order.sell_limit = self.sell_limit
        self.order = order

        self.account = Account()
        self.account_initial = Account()
        self.updateAccountInfo(initial_setup=True)
        self.handle_data = self.strat.handle_data
        #self.params =self.strat.params

        time = Time()
        time.get_current_time = self.get_current_time
        self.time = time


    def get_current_time(self):
        return datetime.datetime.now()

    def updateAccountInfo(self, initial_setup = False):
        huobiAcct = self.getAccuntInfo()
        self.account.huobi_cny_btc = huobiAcct["huobi_cny_btc"]
        self.account.huobi_cny_ltc = huobiAcct["huobi_cny_ltc"]
        self.account.huobi_cny_cash = huobiAcct["huobi_cny_cash"]
        self.account.huobi_cny_btc_loan = huobiAcct["huobi_cny_btc_loan"]
        self.account.huobi_cny_ltc_loan = huobiAcct["huobi_cny_ltc_loan"]
        self.account.huobi_cny_cash_loan = huobiAcct["huobi_cny_cash_loan"]
        self.account.huobi_cny_btc_frozen = huobiAcct["huobi_cny_btc_frozen"]
        self.account.huobi_cny_ltc_frozen = huobiAcct["huobi_cny_ltc_frozen"]
        self.account.huobi_cny_cash_frozen = huobiAcct["huobi_cny_cash_frozen"]
        self.account.huobi_cny_total = huobiAcct["huobi_cny_total"]
        self.account.huobi_cny_net = huobiAcct["huobi_cny_net"]
        if initial_setup:
            self.account_initial.huobi_cny_btc = huobiAcct["huobi_cny_btc"]
            self.account_initial.huobi_cny_ltc = huobiAcct["huobi_cny_ltc"]
            self.account_initial.huobi_cny_cash = huobiAcct["huobi_cny_cash"]
            self.account_initial.huobi_cny_btc_loan = huobiAcct["huobi_cny_btc_loan"]
            self.account_initial.huobi_cny_ltc_loan = huobiAcct["huobi_cny_ltc_loan"]
            self.account_initial.huobi_cny_cash_loan = huobiAcct["huobi_cny_cash_loan"]
            self.account_initial.huobi_cny_btc_frozen = huobiAcct["huobi_cny_btc_frozen"]
            self.account_initial.huobi_cny_ltc_frozen = huobiAcct["huobi_cny_ltc_frozen"]
            self.account_initial.huobi_cny_cash_frozen = huobiAcct["huobi_cny_cash_frozen"]
            self.account_initial.huobi_cny_total = huobiAcct["huobi_cny_total"]
            self.account_initial.huobi_cny_net = huobiAcct["huobi_cny_net"]
            self.account_initial.initial_time = datetime.datetime.now()

    def getStartRunningTime(self):
        if self.startRunningTime == None:
            raise StartRunningTimeEmptyError("startRunningTime is not set yet!")
        return self.startRunningTime

    def getTimeLogFileName(self):
        return "../log/%s_log_%s.txt" % (self.strat.__name__, self.getStartRunningTime().strftime(self.TimeFormatForFileName))

    def getDataLogFileName(self):
        return "../data/%s_data_%s.data" % (self.strat.__name__, self.getStartRunningTime().strftime(self.TimeFormatForFileName))

    def timeLog(self, content):
        self.timeLogger.info(content)

    def getAccuntInfo(self):
        huobiAcct = self.HuobiService.getAccountInfo(helper.coinTypeStructure[self.coinMarketType]["huobi"]["market"],ACCOUNT_INFO)
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
            "huobi_cny_net": huobi_cny_net
        }

    def dataLog(self, content=None):
        if content is None:
            accountInfo = self.getAccuntInfo()
            t = datetime.datetime.now()
            content = "%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s" % \
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
                       accountInfo["huobi_cny_net"])
            self.last_data_log_time = t
        self.dataLogger.info("%s" % str(content))

    def sell_limit(self,security,price,quantity):
        #TODO: implement the sell limit function
        self.sell(security,quantity)

    def sell(self, security, quantity): #quantity is a string value
        self.timeLog("rounding down the quantity to 4 decimal places...")
        self.timeLog("original value:%s"%quantity)
        tmp = float(quantity)
        tmp = helper.myRound(tmp,4)
        quantity = str(tmp)
        self.timeLog("rounded value:%s"%quantity)

        if float(quantity)<0.001:
            self.timeLog("quantity %s is smaller than 0.001, so did not place the sell order into market"%quantity)
            return

        if security == "huobi_cny_btc":
            coin_type = 1
        else:
            coin_type = 2
        res = self.HuobiService.sellMarket(coin_type, quantity, None, None, helper.coinTypeStructure[self.coinMarketType]["huobi"]["market"],SELL_MARKET)
        if u"result" not in res or res[u"result"] != u'success':
            self.timeLog("fail to place market sell order with qty %s into huobi" % quantity)
            return
        order_id = res[u"id"]
        # 查询订单执行情况
        order_info = self.HuobiService.getOrderInfo(coin_type, order_id, helper.coinTypeStructure[self.coinMarketType]["huobi"]["market"],ORDER_INFO)
        self.timeLog("placed below market sell order into huobi with quantity: %s" % quantity)
        self.timeLog(str(order_info))
        if order_info["status"] != 2:
            self.timeLog("waiting for %f for order to be completed" % self.orderWaitingTime)
            time.sleep(self.orderWaitingTime)
            order_info = self.HuobiService.getOrderInfo(coin_type, order_id, helper.coinTypeStructure[self.coinMarketType]["huobi"]["market"], ORDER_INFO)
            self.timeLog(str(order_info))
        executed_qty = float(order_info["processed_amount"])
        self.timeLog("the market sell order in huobi has been executed with filled quantity: %f, received cash: %.2f" % (executed_qty, executed_qty*float(order_info["processed_price"])))
        self.dataLog()

    def buy_limit(self,security,price,quantity):
        #TODO: implement the buy limit function
        self.buy(security,str(helper.myRound(float(price)*float(quantity),2)))

    def buy(self, security, cash_amount ): #cash_amount is a string value
        self.timeLog("rounding down the cash amount to 2 decimal places...")
        self.timeLog("original value:%s"%cash_amount)
        tmp = float(cash_amount)
        tmp = helper.myRound(tmp,2)
        cash_amount = str(tmp)
        self.timeLog("rounded value:%s"%cash_amount)

        if float(cash_amount)<1:
            self.timeLog("cash amount %s is smaller than 1, so did not place the buy order into market"%cash_amount)
            return

        if security == "huobi_cny_btc":
            coin_type = 1
        else:
            coin_type = 2

        res2 = self.HuobiService.buyMarket(coin_type, cash_amount, None, None,helper.coinTypeStructure[self.coinMarketType]["huobi"]["market"],BUY_MARKET)
        #Qty2 = helper.myRound(cash_amount / current_sell_1_price)
        if u"result" not in res2 or res2[u"result"] != u'success':
            self.timeLog("fail to place market buy order with cash amount %s into huobi" % cash_amount)
            return
        order2_id = res2[u"id"]
        # 查询订单执行情况
        order2_info = self.HuobiService.getOrderInfo(coin_type, order2_id, helper.coinTypeStructure[self.coinMarketType]["huobi"]["market"],ORDER_INFO)
        self.timeLog("placed below market buy order into huobi with cash amount:%s" % cash_amount)
        self.timeLog(str(order2_info))
        if order2_info["status"] != 2:
            self.timeLog("waiting for %f for order to be completed" % self.orderWaitingTime)
            time.sleep(self.orderWaitingTime)
            order2_info = self.HuobiService.getOrderInfo(coin_type, order2_id, helper.coinTypeStructure[self.coinMarketType]["huobi"]["market"], ORDER_INFO)
            self.timeLog(str(order2_info))
        executed_qty_2 = float(order2_info["processed_amount"]) / float(order2_info["processed_price"])
        self.timeLog("the market buy order in huobi has been executed with filled quantity: %f, spent cash: %.2f" % (executed_qty_2, float(order2_info["processed_amount"])))
        self.dataLog()


    def go(self):
        self.timeLog("log started at %s" % self.getStartRunningTime().strftime(self.TimeFormatForLog))
        self.dataLog(
            content="time|huobi_cny_cash|huobi_cny_btc|huobi_cny_ltc|huobi_cny_cash_loan|huobi_cny_btc_loan|huobi_cny_ltc_loan|huobi_cny_cash_frozen|huobi_cny_btc_frozen|huobi_cny_ltc_frozen|huobi_cny_total|huobi_cny_net")
        self.dataLog()

        while (True):
            # check whether current time is after the dailyExitTime, if yes, exit
            if self.dailyExitTime is not None and datetime.datetime.now() > datetime.datetime.strptime(
                                    datetime.date.today().strftime("%Y-%m-%d") + " " + self.dailyExitTime,
                                    "%Y-%m-%d %H:%M:%S"):
                self.timeLog("Reach the EOD cutoff time %s, exit now." % self.dailyExitTime)
                break

            self.timeLog("waiting for %f seconds for next cycle..." % self.timeInterval)
            #time.sleep(self.timeInterval)
            #TODO: to remove this line in production
            time.sleep(5)

            # calculate the net asset at a fixed time window
            time_diff = datetime.datetime.now() - self.last_data_log_time
            if time_diff.seconds > self.dataLogFixedTimeWindow:
                self.dataLog()

            self.updateAccountInfo()
            self.handle_data(self)
            self.updateAccountInfo()