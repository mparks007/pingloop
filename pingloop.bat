@ECHO OFF

:LOOPSTART

time /T
@echo: >> pingloop.txt
@echo %date% %time% >> pingloop.txt
ping www.google.com >> pingloop.txt
timeout 5 > nul

GOTO LOOPSTART