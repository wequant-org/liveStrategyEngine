rem 1、先将下面PYTHONPATH的路径改为你本机上wequantstrategy_sample路径，如 PYTHONPATH=E:\wequantstrategy_sample
rem 2、讲CodeDirectory路径改为BanZhuan.py所在路径，如E:\wequantstrategy_sample\liveStrategyEngine
rem 3、将Python3.5的路径改为你本机路径，就是python.exe 所在路径如C:\Python\Python35

@set PYTHONPATH=E:\wequantstrategy_sample
@set CodeDirectory=E:\wequantstrategy_sample\liveStrategyEngine
@set PythonDirectory=C:\Python\Python35

set MainHardDisk = %CodeDirectory:~0,2%

%MainHardDisk %
cd %CodeDirectory%
%PythonDirectory%\python.exe BanZhuan.py


pause