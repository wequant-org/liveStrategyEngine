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
from huobi import HuobiService
from huobi.Util import *
from okcoin.Util import getOkcoinSpot


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

    def sell(self, security, quantity, exchange="huobi"): #quantity is a string value
        if exchange == "huobi":
            self.timeLog("开始下达火币市价卖单...")
            self.timeLog("只保留下单数量的小数点后4位...")
            self.timeLog("原始下单数量:%s"%quantity)
            tmp = float(quantity)
            tmp = helper.myRound(tmp,4)
            quantity = str(tmp)
            self.timeLog("做完小数点处理后的下单数量:%s"%quantity)
            if float(quantity)<self.huobi_min:
                self.timeLog(
                            "数量:%s 小于交易所最小交易数量(火币最小数量:%f),因此无法下单,此处忽略该信号"%(quantity, self.huobi_min))
                return None
            if security == helper.COIN_TYPE_BTC_CNY:
                coin_type = 1
            else:
                coin_type = 2
            res = self.HuobiService.sellMarket(coin_type, quantity, None, None, helper.coinTypeStructure[self.coinMarketType]["huobi"]["market"],SELL_MARKET)
            if u"result" not in res or res[u"result"] != u'success':
                self.timeLog("下达火币市价卖单（数量：%s）失败！"%quantity)
                return None
            order_id = res[u"id"]
            # 查询订单执行情况
            order_info = self.HuobiService.getOrderInfo(coin_type, order_id, helper.coinTypeStructure[self.coinMarketType]["huobi"]["market"],ORDER_INFO)
            self.timeLog("下达如下火币市价卖单，数量：%s"%quantity)
            self.timeLog(str(order_info))
            if order_info["status"] != 2:
                self.timeLog("等待%f秒直至订单完成" % self.orderWaitingTime)
                time.sleep(self.orderWaitingTime)
                order_info = self.HuobiService.getOrderInfo(coin_type, order_id, helper.coinTypeStructure[self.coinMarketType]["huobi"]["market"], ORDER_INFO)
                self.timeLog(str(order_info))
            executed_qty = float(order_info["processed_amount"])
            self.timeLog("火币市价卖单已被执行，执行数量：%f，收到的现金：%.2f" % (executed_qty, executed_qty*float(order_info["processed_price"])))
            self.dataLog()
            return executed_qty
        elif exchange == "okcoin":
            self.timeLog("开始下达okcoin市价卖单...")
            self.timeLog("只保留下单数量的小数点后2位...")
            self.timeLog("原始下单数量:%s"%quantity)
            tmp = float(quantity)
            tmp = helper.myRound(tmp,2)
            quantity = str(tmp)
            self.timeLog("做完小数点处理后的下单数量:%s"%quantity)
            if float(quantity)<self.okcoin_min:
                self.timeLog(
                            "数量:%s 小于交易所最小交易数量(火币最小数量:%f),因此无法下单,此处忽略该信号"%(quantity, self.okcoin_min))
                return None
            res = self.OKCoinService.trade(helper.coinTypeStructure[self.coinMarketType]["okcoin"]["coin_type"], "sell_market", amount=quantity)
            if "result" not in res or res["result"] != True:
                self.timeLog("下达okcoin市价卖单（数量：%s）失败"%quantity)
                return None
            order_id = res["order_id"]
            # 查询订单执行情况
            order_info = self.OKCoinService.orderinfo(helper.coinTypeStructure[self.coinMarketType]["okcoin"]["coin_type"], str(order_id))
            self.timeLog("下达如下okcoin市价卖单，数量：%s"%quantity)
            self.timeLog(str(order_info))
            if order_info["orders"][0]["status"] != 2:
                self.timeLog("等待%.1f秒直至订单完成" % self.orderWaitingTime)
                time.sleep(self.orderWaitingTime)
                order_info = self.OKCoinService.orderinfo(helper.coinTypeStructure[self.coinMarketType]["okcoin"]["coin_type"], str(order_id))
                self.timeLog(str(order_info))
            executed_qty = order_info["orders"][0]["deal_amount"]
            self.timeLog("okcoin市价卖单已被执行，执行数量：%f，收到的现金：%.2f"%(executed_qty,executed_qty*order_info["orders"][0]["avg_price"]))
            self.dataLog()
            return executed_qty

    def buy(self, security, cash_amount, exchange="huobi",sell_1_price=None): #cash_amount is a string value
        if exchange == "huobi":
            self.timeLog("开始下达火币市价买单...")
            self.timeLog("只保留下单数量的小数点后2位...")
            self.timeLog("原始下单金额:%s"%cash_amount)
            tmp = float(cash_amount)
            tmp = helper.myRound(tmp,2)
            cash_amount = str(tmp)
            self.timeLog("做完小数点处理后的下单金额:%s"%cash_amount)

            if float(cash_amount)<1:
                self.timeLog("金额:%s 小于交易所最小交易金额(火币最小金额:1元),因此无法下单,此处忽略该信号"%cash_amount)
                return None

            if security == helper.COIN_TYPE_BTC_CNY:
                coin_type = 1
            else:
                coin_type = 2
            res = self.HuobiService.buyMarket(coin_type, cash_amount, None, None, helper.coinTypeStructure[self.coinMarketType]["huobi"]["market"],BUY_MARKET)
            if u"result" not in res or res[u"result"] != u'success':
                self.timeLog("下达火币市价买单（金额：%s）失败！"%cash_amount)
                return None
            order_id = res[u"id"]
            # 查询订单执行情况
            order_info = self.HuobiService.getOrderInfo(coin_type, order_id, helper.coinTypeStructure[self.coinMarketType]["huobi"]["market"],ORDER_INFO)
            self.timeLog("下达如下火币市价买单，金额：%s"%cash_amount)
            self.timeLog(str(order_info))
            if order_info["status"] != 2:
                self.timeLog("等待%f秒直至订单完成" % self.orderWaitingTime)
                time.sleep(self.orderWaitingTime)
                order_info = self.HuobiService.getOrderInfo(coin_type, order_id, helper.coinTypeStructure[self.coinMarketType]["huobi"]["market"], ORDER_INFO)
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
            self.timeLog("原始下单金额:%s"%cash_amount)
            tmp = float(cash_amount)
            tmp = helper.myRound(tmp,2)
            cash_amount = str(tmp)
            self.timeLog("做完小数点处理后的下单金额:%s"%cash_amount)

            if float(cash_amount)<self.okcoin_min*sell_1_price:
                self.timeLog(
                            "金额:%s 不足以购买交易所最小交易数量(okcoin最小数量:%f，当前卖一价格%.2f,最小金额要求：%.2f),因此无法下单,此处忽略该信号"%(cash_amount,self.okcoin_min,sell_1_price,self.okcoin_min*sell_1_price))
                return None
            res = self.OKCoinService.trade(helper.coinTypeStructure[self.coinMarketType]["okcoin"]["coin_type"], "buy_market",price=cash_amount)

            if "result" not in res or res["result"] != True:
                self.timeLog("下达okcoin市价买单（金额：%s）失败"%cash_amount)
                return None
            order_id = res["order_id"]
            # 查询订单执行情况
            order_info = self.OKCoinService.orderinfo(helper.coinTypeStructure[self.coinMarketType]["okcoin"]["coin_type"], str(order_id))
            self.timeLog("下达如下okcoin市价买单，金额：%s"%cash_amount)
            self.timeLog(str(order_info))
            if order_info["orders"][0]["status"] != 2:
                self.timeLog("等待%.1f秒直至订单完成" % self.orderWaitingTime)
                time.sleep(self.orderWaitingTime)
                order_info = self.OKCoinService.orderinfo(helper.coinTypeStructure[self.coinMarketType]["okcoin"]["coin_type"], str(order_id))
                self.timeLog(str(order_info))
            executed_qty = order_info["orders"][0]["deal_amount"]
            self.timeLog("okcoin市价买单已被执行，执行数量：%f，花费的现金：%.2f"%(executed_qty,executed_qty*order_info["orders"][0]["avg_price"]))
            self.dataLog()
            return executed_qty

    def go(self):
        self.timeLog("日志启动于 %s" % self.getStartRunningTime().strftime(self.TimeFormatForLog))
        self.dataLog(
            content="time|huobi_cny|huobi_btc|huobi_ltc|huobi_cny_loan|huobi_btc_loan|huobi_ltc_loan|huobi_cny_frozen|huobi_btc_frozen|huobi_ltc_frozen|huobi_total|huobi_net|okcoin_cny|okcoin_btc|okcoin_ltc|okcoin_cny_frozen|okcoin_btc_frozen|okcoin_ltc_frozen|okcoin_total|okcoin_net|total_net")
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
                self.timeLog("发现信号")
                self.timeLog("火币深度:%s" % str(huobiDepth))
                self.timeLog("okcoin深度:%s" % str(okcoinDepth))

                # 每次只能吃掉一定ratio的深度
                Qty = helper.myRound(min(huobi_buy_1_qty, okcoin_sell_1_qty) * self.orderRatio, 4)
                # 每次搬砖前要检查是否有足够security和cash
                Qty = min(Qty, accountInfo[helper.coinTypeStructure[self.coinMarketType]["huobi"]["coin_str"]], helper.myRound(accountInfo[helper.coinTypeStructure[self.coinMarketType]["okcoin"]["market_str"]] / okcoin_sell_1_price, 4))
                Qty = helper.myRound(Qty,4)
                Qty = helper.getRoundedQuantity(Qty, self.coinMarketType)

                if Qty < self.huobi_min or Qty < self.okcoin_min:
                    self.timeLog(
                        "数量:%f 小于交易所最小交易数量(火币最小数量:%f, okcoin最小数量:%f),因此无法下单并忽略该信号" %(Qty, self.huobi_min, self.okcoin_min))
                    continue
                else:
                    # step1: 先处理卖
                    executed_qty = self.sell(self.coinMarketType,str(Qty),exchange="huobi")

                    # step2: 再执行买
                    Qty2 = min(executed_qty, Qty)
                    Qty2 = max(helper.getRoundedQuantity(Qty2,self.coinMarketType),self.okcoin_min)
                    self.buy(self.coinMarketType,str(Qty2*okcoin_sell_1_price),exchange="okcoin",sell_1_price=okcoin_sell_1_price)

            elif okcoin_buy_1_price > huobi_sell_1_price:  # 获利信号：OKcoin卖，huobi买
                self.timeLog("发现信号")
                self.timeLog("火币深度:%s" % str(huobiDepth))
                self.timeLog("okcoin深度:%s" % str(okcoinDepth))

                # 每次只能吃掉一定ratio的深度
                Qty = helper.myRound(min(huobi_sell_1_qty, okcoin_buy_1_qty) * self.orderRatio, 4)
                # 每次搬砖前要检查是否有足够security和cash
                Qty = min(Qty, accountInfo[helper.coinTypeStructure[self.coinMarketType]["okcoin"]["coin_str"]], helper.myRound(accountInfo[helper.coinTypeStructure[self.coinMarketType]["huobi"]["market_str"]] / huobi_sell_1_price), 4)
                Qty = helper.getRoundedQuantity(Qty, self.coinMarketType)

                if Qty < self.huobi_min or Qty < self.okcoin_min:
                    self.timeLog("数量:%f 小于交易所最小交易数量(火币最小数量:%f, okcoin最小数量:%f),因此无法下单并忽略该信号"%(Qty, self.huobi_min, self.okcoin_min))
                    continue
                else:
                    # step1: 先处理卖
                    executed_qty = self.sell(self.coinMarketType,str(Qty),exchange="okcoin")

                    # step2: 再执行买
                    Qty2 = min(executed_qty, Qty)
                    self.buy(self.coinMarketType,str(Qty2*huobi_sell_1_price),exchange="huobi")


if __name__ == "__main__":
    # btc
    strat = BanzhuanStrategy(datetime.datetime.now(), 0.8, 1, 0.1, 30, helper.COIN_TYPE_BTC_CNY, dailyExitTime="23:30:00")
    strat.go()

    '''
    # ltc
    strat = BanzhuanStrategy(datetime.datetime.now(), 0.8, 1, 0.1, 30, helper.COIN_TYPE_LTC_CNY, dailyExitTime="23:30:00")
    strat.go()
    '''



