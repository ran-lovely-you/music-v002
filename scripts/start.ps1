# 認知機能サポートBGM AI - 起動スクリプト（Windows）
# 初回は自動的にセットアップ（仮想環境作成・依存関係インストール）まで行います。
#
# 注意: $ErrorActionPreference は意図的に既定値(Continue)のままにしている。
# "Stop" にすると、npm/pip が警告をstderrへ出力しただけでスクリプトが
# 異常終了してしまう環境があるため（PowerShellのネイティブコマンド周りの挙動）。
# 各ステップの成否は $LASTEXITCODE を明示的に確認する。

$RootDir = Split-Path -Parent $PSScriptRoot
Set-Location $RootDir

$BackendDir = Join-Path $RootDir "backend"
$FrontendDir = Join-Path $RootDir "frontend"
$BackendPort = 8000
$FrontendPort = 5173

function Info($msg)  { Write-Host "`n[INFO] $msg" -ForegroundColor Cyan }
function WarnMsg($msg) { Write-Host "`n[WARN] $msg" -ForegroundColor Yellow }
function ErrorMsg($msg) { Write-Host "`n[ERROR] $msg" -ForegroundColor Red }

function Pause-AndExit {
    Read-Host "`nEnterキーを押すとウィンドウを閉じます"
    exit 1
}

# --- 前提ツールの確認 ---
$PyExe = $null
$PyBaseArgs = @()
if (Get-Command py -ErrorAction SilentlyContinue) {
    $PyExe = "py"
    $PyBaseArgs = @("-3.11")
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $PyExe = "python"
    $PyBaseArgs = @()
}
if (-not $PyExe) {
    ErrorMsg "Pythonが見つかりません。https://www.python.org/downloads/ からインストールするか、'winget install Python.Python.3.11' を実行してください。"
    Pause-AndExit
}

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    ErrorMsg "Node.js/npmが見つかりません。https://nodejs.org/ からインストールするか、'winget install OpenJS.NodeJS.LTS' を実行してください。"
    Pause-AndExit
}

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    WarnMsg "ffmpegが見つかりません。MP3書き出しができません（WAV/FLACは利用できます）。'winget install ffmpeg' でインストールできます。"
}

# --- バックエンドのセットアップ（初回のみ） ---
$VenvDir = Join-Path $BackendDir ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$VenvUvicorn = Join-Path $VenvDir "Scripts\uvicorn.exe"

if (-not (Test-Path $VenvDir)) {
    Info "初回セットアップ: Python仮想環境を作成しています…"
    & $PyExe @PyBaseArgs -m venv $VenvDir
    if ($LASTEXITCODE -ne 0) {
        ErrorMsg "Python仮想環境の作成に失敗しました。"
        Pause-AndExit
    }
}

$DepsMarker = Join-Path $VenvDir ".deps_installed"
if (-not (Test-Path $DepsMarker)) {
    Info "初回セットアップ: 必要なライブラリをインストールしています…（数分かかることがあります）"
    & $VenvPython -m pip install --upgrade pip | Out-Null
    & $VenvPython -m pip install -r (Join-Path $BackendDir "requirements.txt")
    if ($LASTEXITCODE -ne 0) {
        ErrorMsg "ライブラリのインストールに失敗しました。インターネット接続をご確認のうえ、再度お試しください。"
        Pause-AndExit
    }
    New-Item -ItemType File -Path $DepsMarker | Out-Null
}

$EnvFile = Join-Path $BackendDir ".env"
if (-not (Test-Path $EnvFile)) {
    Copy-Item (Join-Path $BackendDir ".env.example") $EnvFile
}

# --- フロントエンドのセットアップ（初回のみ） ---
$NodeModules = Join-Path $FrontendDir "node_modules"
if (-not (Test-Path $NodeModules)) {
    Info "初回セットアップ: フロントエンドのライブラリをインストールしています…"
    Push-Location $FrontendDir
    npm install
    $npmExit = $LASTEXITCODE
    Pop-Location
    if ($npmExit -ne 0) {
        ErrorMsg "フロントエンドのライブラリインストールに失敗しました。インターネット接続をご確認のうえ、再度お試しください。"
        Pause-AndExit
    }
}

# vite.cmd経由だと子プロセス(node)がプロセスツリーに隠れて終了処理が不安定になるため、
# node + vite.js を直接起動してプロセスIDを正確に把握できるようにする。
$ViteJs = Join-Path $FrontendDir "node_modules\vite\bin\vite.js"

function Test-PortInUse($port) {
    try {
        $conn = New-Object System.Net.Sockets.TcpClient
        $iar = $conn.BeginConnect("127.0.0.1", $port, $null, $null)
        $ok = $iar.AsyncWaitHandle.WaitOne(500)
        if ($ok -and $conn.Connected) {
            $conn.Close()
            return $true
        }
        $conn.Close()
        return $false
    } catch {
        return $false
    }
}

$AlreadyRunning = (Test-PortInUse $BackendPort) -and (Test-PortInUse $FrontendPort)

$BackendProc = $null
$FrontendProc = $null

function Cleanup {
    Info "終了処理をしています…"
    if ($BackendProc) {
        & taskkill /F /T /PID $BackendProc.Id 2>$null | Out-Null
    }
    if ($FrontendProc) {
        & taskkill /F /T /PID $FrontendProc.Id 2>$null | Out-Null
    }
}

if (-not $AlreadyRunning) {
    Info "サーバーを起動しています…"
    $BackendProc = Start-Process -FilePath $VenvUvicorn `
        -ArgumentList @("app.main:app", "--port", $BackendPort, "--log-level", "warning") `
        -WorkingDirectory $BackendDir -PassThru -WindowStyle Hidden

    $FrontendProc = Start-Process -FilePath "node" `
        -ArgumentList @($ViteJs, "--port", $FrontendPort, "--strictPort") `
        -WorkingDirectory $FrontendDir -PassThru -WindowStyle Hidden

    Info "起動を待っています…"
    $ready = $false
    for ($i = 0; $i -lt 30; $i++) {
        if ((Test-PortInUse $BackendPort) -and (Test-PortInUse $FrontendPort)) {
            $ready = $true
            break
        }
        Start-Sleep -Seconds 1
    }
    if (-not $ready) {
        ErrorMsg "起動に時間がかかっています。ウィンドウのログを確認してください。"
    }
}

$Url = "http://localhost:$FrontendPort"
Info "ブラウザで開きます: $Url"
Start-Process $Url | Out-Null

$LanIp = (Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*" } |
    Select-Object -First 1).IPAddress

Info "認知機能サポートBGM AI が起動しました。"
if ($LanIp) {
    Info "ご家族の他のスマホ・タブレットからも、同じWi-Fiに接続していれば次のURLで使えます: http://${LanIp}:$FrontendPort"
}
Info "終了するには、このウィンドウを閉じるか Ctrl+C を押してください。"

if ($AlreadyRunning) {
    exit 0
}

try {
    while ($true) { Start-Sleep -Seconds 1 }
} finally {
    Cleanup
}
