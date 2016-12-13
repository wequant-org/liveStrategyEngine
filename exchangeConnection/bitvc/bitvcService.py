#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""BitVC api features & whatnot"""
import hashlib
import pprint

import requests

import accountConfig
from exchangeConnection.bitvc.errors import error_text
from utils.helper import *


def config_map():
    return {
        "key": accountConfig.BITVC["CNY_1"]["ACCESS_KEY"],
        "secret": accountConfig.BITVC["CNY_1"]["SECRET_KEY"],
        "base": accountConfig.BITVC["CNY_1"]["SERVICE_API"],
        "futurebase": accountConfig.BITVC["CNY_1"]["FUTURE_SERVICE_API"]
    }


def format_check(output):
    """check for errors and print"""
    try:
        msg = error_text(output['code'])
        print("Error {}: {}".format(output['code'], msg))
    except KeyError:
        ppt = pprint.PrettyPrinter(indent=4)
        ppt.pprint(output)


class BitVC(object):
    """make requests, return data, and stuff"""

    def __init__(self):
        self.cfg = config_map()

    def sign(self, items):
        """
        computes signed key to pass with authenticated request
        items:  dict of parameters to include in auth request
        returns:    tuple (md5 auth string, timestamp)
        """
        auth = hashlib.md5()
        auth.update(("access_key=" + self.cfg['key'] + "&").encode('utf-8'))

        timestamp = int(time.time())
        items["created"] = timestamp

        for key in sorted(items.keys()):
            auth.update((key + "=" + str(items[key]) + "&").encode('utf-8'))

        auth.update(("secret_key=" + self.cfg['secret']).encode('utf-8'))
        return (auth.hexdigest(), timestamp)

    def assets(self):
        """
        get personal assets info
        returns:    dict of balances
        """
        sign = self.sign({})
        params = {'access_key': self.cfg['key'], 'created': sign[1], 'sign': sign[0]}
        req = requests.post(self.cfg['base'] + 'accountInfo/get', data=params, timeout=20).json()

        return req

    def list_orders(self, currency):
        """
        get list of orders
        currency:   int 2 = Wright (fiat), 1 = BTC
        returns:    list of order dicts
        """
        sign = self.sign({'coin_type': currency})
        params = {'access_key': self.cfg['key'], 'coin_type': currency, 'created': sign[1], 'sign': sign[0]}
        req = requests.post(self.cfg['base'] + 'order/list', data=params, timeout=20).json()

        return req

    def order_info(self, currency, order_id):
        """
        get info on a specific order
        currency:   int 2 = Wright (fiat), 1 = BTC
        order_id:   int order id
        returns:    dict with order info
        """
        sign = self.sign({'coin_type': currency, 'id': order_id})
        params = {'access_key': self.cfg['key'], 'coin_type': currency, 'created': sign[1], 'sign': sign[0]}
        req = requests.post(self.cfg['base'] + 'order/' + str(order_id), data=params, timeout=20).json()

        return req

    def order_cancel(self, currency, order_id):
        """
        cancel order
        currency:   int 2 = Wright (fiat), 1 = BTC
        order_id:   int order id
        returns:    dict, check 'Result' key
        """
        sign = self.sign({'coin_type': currency, 'id': order_id})
        params = {'access_key': self.cfg['key'], 'coin_type': currency, 'created': sign[1], 'sign': sign[0]}
        req = requests.post(self.cfg['base'] + 'cancel/' + str(order_id), data=params, timeout=20).json()

        return req


class BitVCFuture(object):
    """make requests, return data, and stuff"""

    def __init__(self):
        self.cfg = config_map()

    def sign(self, items):
        """
        computes signed key to pass with authenticated request
        items:  dict of parameters to include in auth request
        returns:    tuple (md5 auth string, timestamp)
        """
        auth = hashlib.md5()
        auth.update(("accessKey=" + self.cfg['key'] + "&").encode('utf-8'))

        timestamp = int(time.time())
        items["created"] = timestamp

        for key in sorted(items.keys()):
            auth.update((key + "=" + str(items[key]) + "&").encode('utf-8'))

        auth.update(("secretKey=" + self.cfg['secret']).encode('utf-8'))
        return (auth.hexdigest(), timestamp)

    def balance(self, coin_type):
        """
        get personal assets info
        returns:    dict of balances
        """
        sign = self.sign({'coinType': coin_type})
        params = {'accessKey': self.cfg['key'], 'coinType': coin_type, 'created': sign[1], 'sign': sign[0]}
        req = requests.post(self.cfg['futurebase'] + 'balance', data=params, timeout=20).json()

        return req

    def list_orders(self, currency):
        """
        get list of orders
        currency:   int 2 = Wright (fiat), 1 = BTC
        returns:    list of order dicts
        """
        sign = self.sign({'coin_type': currency})
        params = {'access_key': self.cfg['key'], 'coin_type': currency, 'created': sign[1], 'sign': sign[0]}
        req = requests.post(self.cfg['futurebase'] + 'order/list', data=params, timeout=20).json()

        return req

    def order_info(self, currency, order_id):
        """
        get info on a specific order
        currency:   int 2 = Wright (fiat), 1 = BTC
        order_id:   int order id
        returns:    dict with order info
        """
        sign = self.sign({'coin_type': currency, 'id': order_id})
        params = {'access_key': self.cfg['key'], 'coin_type': currency, 'created': sign[1], 'sign': sign[0]}
        req = requests.post(self.cfg['futurebase'] + 'order/' + str(order_id), data=params, timeout=20).json()

        return req

    def order_cancel(self, currency, order_id):
        """
        cancel order
        currency:   int 2 = Wright (fiat), 1 = BTC
        order_id:   int order id
        returns:    dict, check 'Result' key
        """
        sign = self.sign({'coin_type': currency, 'id': order_id})
        params = {'access_key': self.cfg['key'], 'coin_type': currency, 'created': sign[1], 'sign': sign[0]}
        req = requests.post(self.cfg['futurebase'] + 'cancel/' + str(order_id), data=params, timeout=20).json()

        return req

    def get_current_bitvc_future_deal_price(self):
        req = requests.get("http://market.bitvc.com/futures/ticker_btc_week.js", timeout=20).json()
        return req


# 返回期货平台的动态权益的人民币市值
def getBitVCDynamicRightsInCNY():
    bitvcFuture = BitVCFuture()
    if bitvcFuture.cfg["key"] == "":
        return 0
    else:
        balance = bitvcFuture.balance(HUOBI_COIN_TYPE_BTC)  # 币种 1比特币 2莱特币
        dynamicRights = balance["dynamicRights"]
        priceStruct = bitvcFuture.get_current_bitvc_future_deal_price()
        return round(float(priceStruct["last"]) * dynamicRights, 2)
