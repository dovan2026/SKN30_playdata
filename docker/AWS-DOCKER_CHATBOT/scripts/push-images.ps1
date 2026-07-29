param(
    [Parameter(Mandatory = $true)]
    [string]$DockerHubUsername,

    [string]$ApiTag = "1.0.0",

    [string]$WebTag = "1.0.0",

    [string]$Platform = "linux/amd64"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ApiImage = "${DockerHubUsername}/compose-ai-api:${ApiTag}"
$WebImage = "${DockerHubUsername}/compose-ai-web:${WebTag}"

Write-Host "[1/5] Docker Engine 확인"
docker version | Out-Null

Write-Host "[2/5] FastAPI 이미지 빌드: $ApiImage"
docker build `
    --platform $Platform `
    --tag $ApiImage `
    (Join-Path $ProjectRoot "backend")

Write-Host "[3/5] HTML/Nginx 이미지 빌드: $WebImage"
docker build `
    --platform $Platform `
    --tag $WebImage `
    (Join-Path $ProjectRoot "frontend")

Write-Host "[4/5] FastAPI 이미지 Push"
docker push $ApiImage

Write-Host "[5/5] HTML/Nginx 이미지 Push"
docker push $WebImage

Write-Host "완료"
Write-Host "API: $ApiImage"
Write-Host "WEB: $WebImage"
