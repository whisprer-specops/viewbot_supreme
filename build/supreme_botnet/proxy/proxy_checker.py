@echo off
REM Launch the Supreme ViewBot in full mode (with claps, comments, etc.)

python main.py ^
 --url "https://medium.com/@cgpt/is-vibe-coding-cheating-or-the-future-of-programming-in-the-workplace-216fe9d5084d" ^
 --threads 7 ^
 --requests 37 ^
 --delay 26 ^
 --proxy-file "proxies.txt" ^
 --log-level INFO ^
 --webhook "https://discord.com/api/webhooks/1370671462834507776/eMZv5eOANzLUa-eIU4679FinYLTuFVMxnF1LL_sqlRj1Q84MQld5VOvM-fhYBf1ftsp9" ^
 --mode full

pause
