param(
    [string]$BaseUrl = "http://localhost:8080",

    [switch]$TestChat
)

$ErrorActionPreference = "Stop"
$NormalizedBaseUrl = $BaseUrl.TrimEnd("/")

Write-Host "[1/3] 프론트엔드 확인"
$FrontendResponse = Invoke-WebRequest `
    -UseBasicParsing `
    -Uri "$NormalizedBaseUrl/" `
    -Method Get
if ($FrontendResponse.StatusCode -ne 200) {
    throw "프론트엔드 응답 실패: HTTP $($FrontendResponse.StatusCode)"
}

Write-Host "[2/3] FastAPI Health Check"
Invoke-RestMethod `
    -Uri "$NormalizedBaseUrl/api/health" `
    -Method Get | ConvertTo-Json

Write-Host "[3/3] FastAPI 환경 정보"
$Info = Invoke-RestMethod `
    -Uri "$NormalizedBaseUrl/api/info" `
    -Method Get
$Info | ConvertTo-Json

if ($TestChat) {
    if (-not $Info.openai_configured) {
        throw "OPENAI_API_KEY가 설정되지 않아 채팅 요청을 테스트할 수 없습니다."
    }

    Write-Host "[선택] OpenAI 채팅 요청 - API 사용량과 비용이 발생할 수 있습니다."
    $Body = @{
        messages = @(
            @{
                role = "user"
                content = "Docker Compose를 한 문장으로 설명해 주세요."
            }
        )
    } | ConvertTo-Json -Depth 4

    Invoke-RestMethod `
        -Uri "$NormalizedBaseUrl/api/chat" `
        -Method Post `
        -ContentType "application/json" `
        -Body $Body | ConvertTo-Json
}

Write-Host "서비스 점검이 성공했습니다."
