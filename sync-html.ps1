# sync-html.ps1
# 将根目录 index.html 同步到三个部署目录
# 用法：在项目根目录执行 .\sync-html.ps1

$src = Join-Path $PSScriptRoot "index.html"
$targets = @(
    "docs\index.html",
    "cloudflare\public\index.html",
    "templates\index.html"
)

foreach ($t in $targets) {
    $dst = Join-Path $PSScriptRoot $t
    Copy-Item $src $dst -Force
    Write-Host "✓ synced → $t"
}
Write-Host "`nDone. Run 'git add -A && git commit && git push' to deploy."
