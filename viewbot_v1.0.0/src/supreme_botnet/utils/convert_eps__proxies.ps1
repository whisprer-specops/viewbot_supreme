# convert_eps_proxies.ps1
$source = "$env:APPDATA\EPS\proxylist.txt"
$dest = "D:\code\repos\github_desktop\viewbot_supreme\build\xxx\proxies.txt"

# Read lines, add http:// if missing, remove dupes
$normalized = Get-Content $source |
    ForEach-Object {
        if ($_ -notmatch '^http') { "http://$_" } else { $_ }
    } | Sort-Object -Unique

# Write to new file
$normalized | Set-Content $dest -Encoding UTF8
Write-Host "Proxies updated at $dest"
