@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_ig_raw_truth_2233.ps1" %*
exit /b %ERRORLEVEL%
