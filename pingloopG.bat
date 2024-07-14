@ECHO OFF

:LOOPSTART

time /T
@echo: >> pingloopG.txt
@echo %date% %time% >> pingloopG.txt
ping www.google.com >> pingloopG.txt
timeout 5 > nul

GOTO LOOPSTART