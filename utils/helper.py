#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import io
import logging
import math
import sys
import time
import traceback
import uuid

COIN_TYPE_BTC_CNY = "btc_cny"
COIN_TYPE_LTC_CNY = "ltc_cny"
HUOBI_COIN_TYPE_BTC = 1
HUOBI_COIN_TYPE_LTC = 2
COIN_TYPE_CNY = "cny"
COIN_TYPE_USD = "usd"

coinTypeStructure = {
    COIN_TYPE_BTC_CNY: {
        "huobi": {
            "coin_type": HUOBI_COIN_TYPE_BTC,
            "market": COIN_TYPE_CNY,
            "coin_str": "huobi_cny_btc",
            "market_str": "huobi_cny_cash"
        },
        "okcoin": {
            "coin_type": COIN_TYPE_BTC_CNY,
            "market": COIN_TYPE_CNY,
            "coin_str": "okcoin_cny_btc",
            "market_str": "okcoin_cny_cash"
        }
    },
    COIN_TYPE_LTC_CNY: {
        "huobi": {
            "coin_type": HUOBI_COIN_TYPE_LTC,
            "market": COIN_TYPE_CNY,
            "coin_str": "huobi_cny_ltc",
            "market_str": "huobi_cny_cash"
        },
        "okcoin": {
            "coin_type": COIN_TYPE_LTC_CNY,
            "market": COIN_TYPE_CNY,
            "coin_str": "okcoin_cny_ltc",
            "market_str": "okcoin_cny_cash"
        }
    }
}


# 从huobi style的security拿到okcoin style的security
def getCoinMarketTypeFromSecurity(security):
    if security == "huobi_cny_btc":
        return COIN_TYPE_BTC_CNY
    elif security == "huobi_cny_ltc":
        return COIN_TYPE_LTC_CNY
    else:
        raise ValueError("invalid security %s" % security)


# 向下取小数点后decimal_places位精度
def downRound(qty, decimal_places=4):
    return int(qty * math.pow(10, decimal_places)) / int(math.pow(10, decimal_places))


# 对币数量进行精度裁剪
def getRoundedQuantity(qty, coin_type):
    if coin_type == COIN_TYPE_BTC_CNY:
        # 按照okcoin的下单规则，比特币都是0.01 btc的整数倍，取下限
        return downRound(qty, decimal_places=2)
    elif coin_type == COIN_TYPE_LTC_CNY:
        # 按照okcoin的下单规则，莱特币都是0.1 ltc的整数倍，取下限
        return downRound(qty, decimal_places=1)
    else:
        raise ValueError("invalid coin type %s" % coin_type)


# 从对象拿数据
def componentExtract(object, key, default=None):
    if type(object) == dict:
        return object.get(key, default)
    else:
        return getattr(object, key, default)


# 获取uuid
def getUUID():
    return str(uuid.uuid1())


# print traceback to log
def printTracebackToLog(timeLog):
    try:
        output = io.StringIO()
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_tb(exc_traceback, file=output)
        timeLog(output.getvalue())
    finally:
        output.close()


# 获取当前时间，返回字符串，格式为：'YYYYMMDD_hhmmss'
def current_time_str():
    current_time = datetime.datetime.now()
    time_string = current_time.strftime('%Y%m%d_%H%M%S')
    return time_string


# 将时间戳转化为可读时间
def timestamp_to_timestr(timestamp):
    time_struct = time.localtime(timestamp)
    time_string = time.strftime("%Y%m%d_%H%M%S", time_struct)
    return time_string


# 抽象出timelogger
class TimeLogger(object):
    def __init__(self, logFileName):
        self.timeLogger = logging.getLogger('timeLog')
        self.timeLogger.setLevel(logging.DEBUG)
        self.timeLogHandler = logging.FileHandler(logFileName)
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

    def timeLog(self, content, level=logging.INFO):
        if level == logging.DEBUG:
            self.timeLogger.debug(content)
        elif level == logging.INFO:
            self.timeLogger.info(content)
        elif level == logging.WARN:
            self.timeLogger.warn(content)
        elif level == logging.ERROR:
            self.timeLogger.error(content)
        elif level == logging.CRITICAL:
            self.timeLogger.critical(content)
        else:
            raise ValueError("unsupported logging level %d" % level)


# 策略进程
def start_strat(strat):
    if strat.dailyExitTime is not None:
        # check whether current time is after the dailyExitTime, if yes, exit
        while datetime.datetime.now() <= datetime.datetime.strptime(
                                datetime.date.today().strftime("%Y-%m-%d") + " " + strat.dailyExitTime,
                "%Y-%m-%d %H:%M:%S"):
            try:
                strat.go()
            except Exception:
                printTracebackToLog(strat.timeLog)
        strat.timeLog("抵达每日终结时间：%s, 现在退出." % strat.dailyExitTime)
    else:
        while True:
            try:
                strat.go()
            except Exception:
                printTracebackToLog(strat.timeLog)
