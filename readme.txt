###############################################################
#   获取更多免费策略，请加入WeQuant比特币量化策略交流QQ群：519538535
#   群主邮箱：lanjason@foxmail.com，群主微信/QQ：64008672
#   沉迷量化，无法自拔
###############################################################


如何跑策略？

第一步：下载Python3，建议安装Anaconda 4.2.0(https://www.continuum.io/downloads),里面包含了Python 3.5 以及各种科学计算库
第二步：去huobi.com注册用户，申请API key，将申请好的API key设置到huobi/Config.py中去
第三步：去www.okcoin.cn注册用户，申请API key，将申请好的API key设置到okcoin/Config.py中去
第四步：执行liveStrategyEngine/BanZhuan.py，如果想跑莱特币搬砖，直接注释掉比特币那两句，去掉莱特币那一段的注释即可


如何跑其他在userStrategy目录下的实盘非搬砖策略？
到liveStrategyEngine目录下，参考SimpleMA，修改main.py，然后跑main.py即可。之后持续分享的策略都会放在userStrategy目录下.

怎么执行main.py？
进入到liveStrategyEngine的目录，比如我的当前目录就是：
JanesdeMacBook-Pro:liveStrategyEngine janes$ pwd
/Users/janes/PycharmProjects/wequantstrategy_sample/liveStrategyEngine

如果是Mac或者Linux系统，直接在liveStrategyEngine的目录下：
chmod 777 run.sh
./run.sh

如果是Windows系统，在liveStrategyEngine的目录下，参考run.bat修改成您的系统对应的各项参数，然后直接运行run.bat



FAQ：
1. 我想让我的策略7*24小时不间断运行，怎么做？

不用设置dailyExitTime即可
BanzhuanStrategy(....., dailyExitTime="23:30:00")  ==> BanzhuanStrategy(.....)

2. 我想让我的策略每天23:00终止，怎么做？
设置dailyExitTime为"23:00:00"
BanzhuanStrategy(....., dailyExitTime="23:00:00")

3. 去哪里查看日志？
log目录下有每次运行的日志，日志名里面有当次运行的起始时刻（精确到毫秒）

4. 去哪里看持仓记录？
data目录下有每次运行的持仓记录，持仓记录名里面有当次运行的起始时刻（精确到毫秒）

5. 怎么跑BitVC期货策略
去http://www.bitvc.com/注册用户，申请API key，将申请好的API key设置到bitvc目录下的config中去
然后启动bitvc/test.py

