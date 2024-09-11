@REM #change current directory to this file
%~d0
cd %~dp0

set DST_PATH=%AppData%\Blender Foundation\Blender\4.2\scripts\addons\

mkdir "%DST_PATH%"

mklink /D "%DST_PATH%\jx" "%~dp0\jx"
@echo !! may need to "Run as admin" if not working
@echo -------


@pause