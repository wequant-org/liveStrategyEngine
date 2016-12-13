#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 用于进行http请求，以及MD5加密，生成签名的工具类

import hashlib
import urllib
from urllib.parse import urljoin

import requests


def buildMySign(params, secretKey):
    sign = ''
    for key in sorted(params.keys()):
        sign += key + '=' + str(params[key]) + '&'
    data = sign + 'secret_key=' + secretKey
    return hashlib.md5(data.encode("utf8")).hexdigest().upper()


def httpGet(url, resource, params=''):
    '''
    conn = http.client.HTTPSConnection(url, timeout=10)
    conn.request("GET", resource + '?' + params)
    response = conn.getresponse()
    data = response.read().decode('utf-8')
    return json.loads(data)
    '''
    fullURL = urljoin(url, resource + "?" + params)
    response = requests.get(fullURL, timeout=20)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception("httpGet failed, detail is:%s" % response.text)


def httpPost(url, resource, params):
    '''
    headers = {
        "Content-type": "application/x-www-form-urlencoded",
    }
    conn = http.client.HTTPSConnection(url, timeout=10)
    temp_params = urllib.parse.urlencode(params)
    conn.request("POST", resource, temp_params, headers)
    response = conn.getresponse()
    data = response.read().decode('utf-8')
    params.clear()
    conn.close()
    return json.loads(data)
    '''
    headers = {
        "Content-type": "application/x-www-form-urlencoded",
    }
    fullURL = urljoin(url, resource)
    temp_params = urllib.parse.urlencode(params)
    response = requests.post(fullURL, temp_params, headers=headers, timeout=20)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception("httpPost failed, detail is:%s" % response.text)
