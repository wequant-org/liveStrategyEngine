rem 1、先将下面PYTHONPATH的路径改为你本机上wequantstrategy_sample路径，如 PYTHONPATH=E:\wequantstrategy_sample
rem 2、将Python3.5的路径改为你本机路径，就是python.exe 所在路径如C:\Python\Python35

@set PYTHONPATH=E:\wequantstrategy_sample
@set PythonDirectory=C:\Python\Python35

cd %PYTHONPATH%
%PythonDirectory%\python.exe main_banZhuan.py


pause