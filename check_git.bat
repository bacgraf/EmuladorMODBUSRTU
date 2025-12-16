@echo off
cd "Z:\111 PUB\01 INTRANET\Marcel Hilleshein\PROJ\SimuladorBMS"
echo.
echo === Git Status ===
git status
echo.
echo === Git Remote ===
git remote -v
echo.
echo === Git Log ===
git log --oneline -5
echo.
pause

