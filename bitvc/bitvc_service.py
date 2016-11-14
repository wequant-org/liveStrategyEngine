#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################
#   获取更多免费策略，请加入WeQuant比特币量化策略交流QQ群：519538535
#   群主邮箱：lanjason@foxmail.com，群主微信/QQ：64008672
#   沉迷量化，无法自拔
###############################################################

"""BitVC api features & whatnot"""
import configparser
import hashlib
import pprint
import time

import requests

from bitvc.errors import error_text

CFG = configparser.ConfigParser()
CFG.read('config')

def config_map(section):
    """get us some configs"""
    data = {}
    try:
        for name, _ in CFG.items(section):
            try:
                data[name] = CFG.get(section, name)
            except configparser.Error:
                data[name] = None
        return data
    except configparser.NoSectionError:
        return None

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
        self.cfg = config_map('API')

    def sign(self, items):
        """
        computes signed key to pass with authenticated request
        items:  dict of parameters to include in auth request
        returns:    tuple (md5 auth string, timestamp)
        """
        auth = hashlib.md5()
        auth.update(("access_key="+self.cfg['key']+"&").encode('utf-8'))

        timestamp = int(time.time())
        items["created"] = timestamp

        for key in sorted(items.keys()):
            auth.update((key+"="+str(items[key])+"&").encode('utf-8'))

        auth.update(("secret_key="+self.cfg['secret']).encode('utf-8'))
        return (auth.hexdigest(), timestamp)

    def assets(self):
        """
        get personal assets info
        returns:    dict of balances
        """
        sign = self.sign({})
        params = {'access_key': self.cfg['key'], 'created': sign[1], 'sign': sign[0]}
        req = requests.post(self.cfg['base']+'accountInfo/get', data=params).json()

        return req

    def list_orders(self, currency):
        """
        get list of orders
        currency:   int 2 = Wright (fiat), 1 = BTC
        returns:    list of order dicts
        """
        sign = self.sign({'coin_type': currency})
        params = {'access_key': self.cfg['key'], 'coin_type': currency, 'created': sign[1], 'sign': sign[0]}
        req = requests.post(self.cfg['base']+'order/list', data=params).json()

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
        req = requests.post(self.cfg['base']+'order/'+str(order_id), data=params).json()

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
        req = requests.post(self.cfg['base']+'cancel/'+str(order_id), data=params).json()

        return req


class BitVCFuture(object):
    """make requests, return data, and stuff"""
    def __init__(self):
        self.cfg = config_map('API')

    def sign(self, items):
        """
        computes signed key to pass with authenticated request
        items:  dict of parameters to include in auth request
        returns:    tuple (md5 auth string, timestamp)
        """
        auth = hashlib.md5()
        auth.update(("accessKey="+self.cfg['key']+"&").encode('utf-8'))

        timestamp = int(time.time())
        items["created"] = timestamp

        for key in sorted(items.keys()):
            auth.update((key+"="+str(items[key])+"&").encode('utf-8'))

        auth.update(("secretKey="+self.cfg['secret']).encode('utf-8'))
        return (auth.hexdigest(), timestamp)

    def balance(self,coin_type):
        """
        get personal assets info
        returns:    dict of balances
        """
        sign = self.sign({'coinType':coin_type})
        params = {'accessKey': self.cfg['key'], 'coinType':coin_type, 'created': sign[1], 'sign': sign[0]}
        req = requests.post(self.cfg['futurebase']+'balance', data=params).json()

        return req

    def list_orders(self, currency):
        """
        get list of orders
        currency:   int 2 = Wright (fiat), 1 = BTC
        returns:    list of order dicts
        """
        sign = self.sign({'coin_type': currency})
        params = {'access_key': self.cfg['key'], 'coin_type': currency, 'created': sign[1], 'sign': sign[0]}
        req = requests.post(self.cfg['futurebase']+'order/list', data=params).json()

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
        req = requests.post(self.cfg['futurebase']+'order/'+str(order_id), data=params).json()

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
        req = requests.post(self.cfg['futurebase']+'cancel/'+str(order_id), data=params).json()

        return req

