#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################
#   获取更多免费策略，请加入WeQuant比特币量化策略交流QQ群：519538535
#   群主邮箱：lanjason@foxmail.com，群主微信/QQ：64008672
#   沉迷量化，无法自拔
###############################################################

"""define bitvc errors"""
# pylint: disable=C0301

def error_text(error_num):
    """figure out our errors"""
    try:
        return ERRORS[error_num]
    except KeyError:
        return "Undefined Error"

# used some vim-fu to help format this
ERRORS = {
    1: "Server Error",
    2: "There is not enough yuan",
    3: "Transaction has started, can not be started again",
    4: "Transaction has ended",
    10: "There is not enough bitcoins",
    11: "Wright does not have enough coins",
    18: "Wrong password funds",
    26: "The commission does not exist",
    32: "Insufficient amount, not transactions or withdrawals",
    33: "The account is locked, you can not operate",
    34: "Assets are locked, unable to trade",
    35: "Leverage limits of your application has not yet returned, still can not buy coins Wright",
    41: "The commission has ended, can not be modified",
    42: "The commission has been canceled, can not be modified",
    44: "Transaction price is too low",
    45: "Transaction price is too high",
    46: "The small number of transactions, the minimum number 0.001",
    47: "Too much the number of transactions",
    48: "Market orders can not be less than one yuan to buy the amount of",
    49: "Limit orders can not be less than the number of transactions Bitcoin 0.001",
    50: "110% of the purchase price can not be higher than the price of",
    51: "Limit the number of single-Wright currency trading is not less than 0.01",
    52: "The number can not be less than 0.001 sold",
    53: "The number can not be less than 0.01 to sell",
    54: "Selling price can not be less than 90% of the price of",
    55: "105% of the purchase price can not be higher than the price of",
    56: "Selling price can not be less than 95% of the price of",
    64: "Invalid request",
    65: "Ineffective methods",
    66: "Access key validation fails",
    67: "Private key authentication fails",
    68: "Invalid price",
    69: "Invalid quantity",
    70: "Invalid submission time",
    71: "Request too many times",
    87: "The number of transactions is less than 0.1 BTC, please do not bid the price higher than the price of one percent",
    88: "The number of transactions is less than 0.1 BTC, please do not sell below the market price of a 1%",
    89: "The number of transactions is less than 0.1 LTC, please do not bid the price higher than the price of one percent",
    90: "The number of transactions is less than 0.1 LTC, please do not sell below the market price of a 1%",
    91: "Invalid currency",
    92: "110% of the purchase price can not be higher than the price of",
    93: "Selling price can not be less than 90% of the price of",
    97: "You have to open financial transactions password, please submit financial transaction password parameters",
    99: "Market orders can not be canceled",
    110: "Bid prices can not be more than two decimal places",
    111: "Bid quantity not more than four decimal places",
    112: "Selling price can not be more than two decimal places",
    113: "Can not sell more than four decimal number",
    114: "Market orders to buy the amount can not be more than 1 million yuan",
    115: "Bitcoin market order to sell the number of not less than 0.001",
    116: "Bitcoin market orders to sell no more than the number 1000",
    117: "Wright currency market order to sell no more than 100,000 the number of",
    118: "Single failure",
    119: "Wright currency market order to sell the number of not less than 0.01",
    120: "Limit orders can not be more than the number of transactions Bitcoin 500",
    121: "Limit order transaction price can not be less than 0.01",
    122: "Limit orders can not be higher than the trading price of 100000",
    125: "Limit orders can not be more than the number of transactions Wright currency 10000",
}
