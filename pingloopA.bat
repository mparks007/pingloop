@ECHO OFF

:LOOPSTART

time /T
@echo: >> pingloopA.txt
@echo %date% %time% >> pingloopA.txt
ping www.amazon.com >> pingloopA.txt
timeout 5 > nul

GOTO LOOPSTART