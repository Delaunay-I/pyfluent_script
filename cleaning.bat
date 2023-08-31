@echo off
cd /d "%~dp0"

rem Delete files with .out extension
del *.out /q
del *.trn /q
del *error.log /q
del cleanup-fluent-*.bat /q

echo Files with .out, .trn extensions, and cleanup-fluent-*.bat files deleted.
