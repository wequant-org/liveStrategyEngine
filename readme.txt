###############################################################
#   获取更多免费策略，请加入WeQuant比特币量化策略交流QQ群：519538535
#   WeQuant微宽网 - https://wequant.io
#   比特币量化交易/优质策略源码/精准回测/免费实盘，尽在微宽网 
###############################################################


一、如何跑搬砖策略？

第一步：下载Python3，建议安装Anaconda 4.2.0(https://www.continuum.io/downloads), 里面包含了Python 3.5 以及各种科学计算库
第二步：去huobi.com注册用户，申请API key，将申请好的API key设置到accountConfig.py中的HUOBI部分去
第三步：去www.okcoin.cn注册用户，申请API key，将申请好的API key设置到accountConfig.py中的OKCOIN部分去
第四步：搬砖策略入口脚本是main_banZhuan.py，如果想跑莱特币搬砖，直接注释掉比特币那两句，去掉莱特币那一段的注释即可


二、如何跑其他在userStrategy目录下的实盘非搬砖策略？
执行main_userStrategy.py，如果要跑其他策略，参考simpleMA对main_userStrategy.py进行修改。之后持续分享的策略都会放在userStrategy目录下.

三、怎么执行main_banZhuan.py？
如果是Mac或者Linux系统，直接在本项目的根目录下：
chmod a+x run_banZhuan.sh
./run_banZhuan.sh

如果是Windows系统，直接在本项目的根目录下：参考run_banZhuan.bat修改成您的系统对应的各项参数，然后直接运行run_banZhuan.bat

四、怎么执行main_userStrategy.py？
请不要跑main_userStrategy里面的策略，因为历史数据现在是Mock出来的

今后拿到实盘数据的话，可以尝试跑一下。怎么跑？
如果是Mac或者Linux系统，直接在本项目的根目录下：
chmod a+x run_userStrategy.sh
./run_userStrategy.sh
如果是Windows系统，直接在本项目的根目录下：参考run_userStrategy.bat修改成您的系统对应的各项参数，然后直接运行run_userStrategy.bat


五、FAQ：
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
去http://www.bitvc.com/ 注册用户，申请API key，将申请好的API key设置到accountConfig.py中的BITVC部分去


