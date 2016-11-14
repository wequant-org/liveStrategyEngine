#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################
#   获取更多免费策略，请加入WeQuant比特币量化策略交流QQ群：519538535
#   群主邮箱：lanjason@foxmail.com，群主微信/QQ：64008672
#   沉迷量化，无法自拔
###############################################################

from bitvc.bitvc_service import *

a = BitVC()
print(a.assets())
print(a.list_orders(1)) #币种 1比特币 2莱特币

b = BitVCFuture()
print(b.balance(1))#币种 1比特币 2莱特币