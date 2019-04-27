
set appName=PiTools
set dd=%date:~0,4%%date:~5,2%%date:~8,2%%time:~0,2%%time:~3,2%%time:~6,2%
set dd=%dd: =0%
set folder=%appName%-%dd%

if exist %folder% (
    del %folder%\* /F /A /Q
) else (
    mkdir %folder%
)

REM pyinstaller -F -i icon/logo.ico main.py
pyinstaller -F -w -i pi.ico main.py

copy dist\main.exe %folder%\%appName%-%dd%.exe

7z a -t7z %folder%.7z %folder%\

del %folder% /F /A /Q
rmdir %folder%