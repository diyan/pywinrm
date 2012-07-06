@echo off
cls
set DIR=%~d0%~p0%
set PATH=C:\Python27;C:\Program Files\Python27;C:\Program Files (x86)\Python27;C:\Python27\Scripts;C:\Program Files\Python27\Scripts;C:\Program Files (x86)\Python27\Scripts;%PATH%
cd %DIR%
python setup.py bootstrap_env
pause