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
        self.coinMarketType = helper.getCoinMarketTypeFromSecurity(self.security)
        self.dailyExitTime      = dailyExitTime #如果设置，则为每天程序的退出时间
        self.TimeFormatForFileName = "%Y%m%d%H%M%S%f"
        self.TimeFormatForLog = "%Y-%m-%d %H:%M:%S.%f"
        self.HuobiService = HuobiService
        coin_type = helper.coinTypeStructure[self.coinMarketType]["huobi"]["coin_type"]
        self.huobi_min_quantity = self.HuobiService.getMinimumOrderQty(coin_type)
        self.huobi_min_cash_amount = self.HuobiService.getMinimumOrderCashAmount()
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
        self.timeLog("交易数量只保留到小数点后4位...")
        self.timeLog("原始交易数量:%s"%quantity)
        tmp = float(quantity)
        tmp = helper.myRound(tmp,4)
        quantity = str(tmp)
        self.timeLog("调整后的交易数量:%s"%quantity)

        if float(quantity)<self.huobi_min_quantity:
            self.timeLog("交易数量:%s 小于火币要求的最小交易数量:%.4f, 所以无法下单"%(quantity,self.huobi_min_quantity))
            return

        coin_type = helper.coinTypeStructure[self.coinMarketType]["huobi"]["coin_type"]
        res = self.HuobiService.sellMarket(coin_type, quantity, None, None, helper.coinTypeStructure[self.coinMarketType]["huobi"]["market"],SELL_MARKET)
        if u"result" not in res or res[u"result"] != u'success':
            self.timeLog("向火币下达市价卖单（交易数量：%s）失败"%quantity)
            return
        order_id = res[u"id"]
        # 查询订单执行情况
        order_info = self.HuobiService.getOrderInfo(coin_type, order_id, helper.coinTypeStructure[self.coinMarketType]["huobi"]["market"],ORDER_INFO)
        self.timeLog("向火币下达如下市价卖单（交易数量：%s）"%quantity)
        self.timeLog(str(order_info))
        if order_info["status"] != 2:
            self.timeLog("等待%d秒直至订单完成"%self.orderWaitingTime)
            time.sleep(self.orderWaitingTime)
            order_info = self.HuobiService.getOrderInfo(coin_type, order_id, helper.coinTypeStructure[self.coinMarketType]["huobi"]["market"], ORDER_INFO)
            self.timeLog(str(order_info))
        executed_qty = float(order_info["processed_amount"])
        self.timeLog("向火币下达的市价卖单已成功执行，订单成交数量：%f，收到的现金：%.2f"%(executed_qty, executed_qty*float(order_info["processed_price"])))
        self.dataLog()

    def buy_limit(self,security,price,quantity):
        #TODO: implement the buy limit function
        self.buy(security,str(helper.myRound(float(price)*float(quantity),2)))

    def buy(self, security, cash_amount ): #cash_amount is a string value
        self.timeLog("交易金额只保留到小数点后2位...")
        self.timeLog("原始交易金额:%s"%cash_amount)
        tmp = float(cash_amount)
        tmp = helper.myRound(tmp,2)
        cash_amount = str(tmp)
        self.timeLog("调整后的交易金额:%s"%cash_amount)

        if float(cash_amount)<self.huobi_min_cash_amount:
            self.timeLog("交易金额：%s 小于火币要求的最小交易金额：%.2f，所以无法下单"%(cash_amount,self.huobi_min_cash_amount))
            return

        coin_type = helper.coinTypeStructure[self.coinMarketType]["huobi"]["coin_type"]
        res2 = self.HuobiService.buyMarket(coin_type, cash_amount, None, None,helper.coinTypeStructure[self.coinMarketType]["huobi"]["market"],BUY_MARKET)
        if u"result" not in res2 or res2[u"result"] != u'success':
            self.timeLog("向火币下达市价买单（交易金额：%s）失败"%cash_amount)
            return
        order2_id = res2[u"id"]
        # 查询订单执行情况
        order2_info = self.HuobiService.getOrderInfo(coin_type, order2_id, helper.coinTypeStructure[self.coinMarketType]["huobi"]["market"],ORDER_INFO)
        self.timeLog("向火币下达如下市价买单（交易金额：%s）"%cash_amount)
        self.timeLog(str(order2_info))
        if order2_info["status"] != 2:
            self.timeLog("等待%d秒直至订单完成"%self.orderWaitingTime)
            time.sleep(self.orderWaitingTime)
            order2_info = self.HuobiService.getOrderInfo(coin_type, order2_id, helper.coinTypeStructure[self.coinMarketType]["huobi"]["market"], ORDER_INFO)
            self.timeLog(str(order2_info))
        executed_qty_2 = float(order2_info["processed_amount"]) / float(order2_info["processed_price"])
        self.timeLog("向火币下达的市价买单已成功执行，订单成交数量：%f，花费的现金：%.2f"%(executed_qty_2, float(order2_info["processed_amount"])))
        self.dataLog()


    def go(self):
        self.timeLog("日志启动于 %s" % self.getStartRunningTime().strftime(self.TimeFormatForLog))
        self.dataLog(
            content="time|huobi_cny_cash|huobi_cny_btc|huobi_cny_ltc|huobi_cny_cash_loan|huobi_cny_btc_loan|huobi_cny_ltc_loan|huobi_cny_cash_frozen|huobi_cny_btc_frozen|huobi_cny_ltc_frozen|huobi_cny_total|huobi_cny_net")
        self.dataLog()

        while (True):
            # check whether current time is after the dailyExitTime, if yes, exit
            if self.dailyExitTime is not None and datetime.datetime.now() > datetime.datetime.strptime(
                                    datetime.date.today().strftime("%Y-%m-%d") + " " + self.dailyExitTime,
                                    "%Y-%m-%d %H:%M:%S"):
                self.timeLog("抵达每日终结时间：%s, 现在退出." % self.dailyExitTime)
                break

            self.timeLog("等待 %d 秒进入下一个循环..." % self.timeInterval)
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