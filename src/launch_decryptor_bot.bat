@echo off
REM Launch the Supreme ViewBot in full mode (with claps, comments, etc.)

python main.py ^
 --url "https://medium.com/@cgpt/is-vibe-coding-cheating-or-the-future-of-programming-in-the-workplace-216fe9d5084d" ^
 --threads 4 ^
 --requests 12 ^
 --delay 39 ^
 --proxy-file "proxies_normalized.txt" ^
 --log-level INFO ^
 --webhook "https://discord.com/api/webhooks/1370671462834507776/eMZv5eOANzLUa-eIU4679FinYLTuFVMxnF1LL_sqlRj1Q84MQld5VOvM-fhYBf1ftsp9" ^
 --mode full

pause
