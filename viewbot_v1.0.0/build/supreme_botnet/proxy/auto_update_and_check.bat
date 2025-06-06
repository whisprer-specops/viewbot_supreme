@echo off
setlocal

REM Step 1: Download fresh proxy list
powershell -Command "Invoke-WebRequest -Uri 'https://www.proxy-list.download/api/v1/get?type=http' -OutFile proxies_raw.txt"

REM Step 2: Add http:// to each and dedupe
powershell -Command "Get-Content proxies_raw.txt | ForEach-Object { if ($_ -notmatch '^http') { 'http://' + $_ } else { $_ } } | Sort-Object -Unique | Set-Content proxylist.txt"

REM Step 3: Run threaded proxy checker
python proxy_checker.py --infile proxylist.txt --outfile proxies.txt --threads 2500 --timeout 4

echo All done. Waiting for next scheduled run...

