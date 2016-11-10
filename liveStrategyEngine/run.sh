#!/bin/sh
# run.sh

now=`pwd`
#替换字符串
#输入：字符串 要替换子串 用于替换的字符串
function str_replace()
{
    echo ${1/$2/$3}
}

#替换字符串
pythonpath=`str_replace "$now" "/liveStrategyEngine" ""`

#执行
PYTHONPATH=$pythonpath python BanZhuan.py