@REM #change current directory to this file
%~d0
cd %~dp0

git archive --format=zip --output jx.zip HEAD jx

@pause