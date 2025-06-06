# fetch_proxies.ps1
$url = "https://www.proxy-list.download/api/v1/get?type=http"
$output = "D:\code\repos\github_desktop\viewbot_supreme\build\xxx\proxies.txt"

Invoke-WebRequest -Uri $url -OutFile $output

# Add http:// prefix to each
(Get-Content $output) | ForEach-Object {
    if ($_ -notmatch '^http') { "http://$_" } else { $_ }
} | Set-Content $output -Encoding UTF8
