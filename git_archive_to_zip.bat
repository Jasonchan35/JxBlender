@REM #change current directory to this file
%~d0
cd %~dp0

:: Get current timestamp in YYYYMMDD_HHMMSS format
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "timestamp=%dt:~0,4%-%dt:~4,2%-%dt:~6,2%_%dt:~8,2%%dt:~10,2%%dt:~12,2%"

:: Create zip file with timestamp
git archive --prefix="" --output="JxBlender_%timestamp%.zip" HEAD jx

@pause