@echo off
rem 同步 CDR AUTo -> WorkBuddy skill 副本（在 CDR AUTo 改动引擎/手册后运行本脚本）
set SRC=C:\Users\Mayn\Desktop\CDR AUTo
set DST=C:\Users\Mayn\.workbuddy\skills\coreldraw-hangtag
copy /Y "%SRC%\SKILL.md" "%DST%\SKILL.md"
copy /Y "%SRC%\references\api_gotchas.md" "%DST%\references\api_gotchas.md"
copy /Y "%SRC%\scripts\*.py" "%DST%\scripts\"
copy /Y "%SRC%\scripts\example_card.json" "%DST%\scripts\example_card.json"
echo sync done
