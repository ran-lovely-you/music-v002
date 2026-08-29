#!/usr/bin/env bash
# 認知機能サポートBGM AI - 起動スクリプト（Mac / Linux共通）
# 初回は自動的にセットアップ（仮想環境作成・依存関係インストール）まで行います。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
BACKEND_PORT=8000
FRONTEND_PORT=5173

info()  { printf '\n\033[1;34m[INFO]\033[0m %s\n' "$1"; }
warn()  { printf '\n\033[1;33m[WARN]\033[0m %s\n' "$1"; }
error() { printf '\n\033[1;31m[ERROR]\033[0m %s\n' "$1"; }

pause_and_exit() {
  echo
  read -r -p "Enterキーを押すとウィンドウを閉じます..." _ || true
  exit 1
}

OS_NAME="$(uname -s)"

# --- Homebrew経由での自動インストール（Macのみ） ---
ensure_homebrew() {
  if command -v brew >/dev/null 2>&1; then
    return 0
  fi
  warn "Homebrewが見つかりません。自動でインストールします…（数分かかることがあります。ログインパスワードを求められる場合があります）"
  NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || return 1
  for candidate in /opt/homebrew/bin/brew /usr/local/bin/brew; do
    if [ -x "$candidate" ]; then
      eval "$("$candidate" shellenv)"
      break
    fi
  done
  command -v brew >/dev/null 2>&1
}

brew_install() {
  local pkg="$1"
  ensure_homebrew || return 1
  info "${pkg} を自動インストールしています…"
  brew install "$pkg"
}

# --- 前提ツールの確認 ---
PYTHON_BIN=""
for cand in python3.11 python3 python; do
  if command -v "$cand" >/dev/null 2>&1; then
    PYTHON_BIN="$cand"
    break
  fi
done
if [ -z "$PYTHON_BIN" ] && [ "$OS_NAME" = "Darwin" ]; then
  brew_install python@3.11 || true
  for cand in python3.11 python3 python; do
    if command -v "$cand" >/dev/null 2>&1; then
      PYTHON_BIN="$cand"
      break
    fi
  done
fi
if [ -z "$PYTHON_BIN" ]; then
  error "Pythonが見つかりません。https://www.python.org/downloads/ からインストールするか、Macなら 'brew install python@3.11' を実行してください。"
  pause_and_exit
fi

if ! command -v npm >/dev/null 2>&1 && [ "$OS_NAME" = "Darwin" ]; then
  brew_install node || true
fi
if ! command -v npm >/dev/null 2>&1; then
  error "Node.js/npmが見つかりません。https://nodejs.org/ からインストールするか、Macなら 'brew install node' を実行してください。"
  pause_and_exit
fi

if ! command -v ffmpeg >/dev/null 2>&1 && [ "$OS_NAME" = "Darwin" ]; then
  brew_install ffmpeg || true
fi
if ! command -v ffmpeg >/dev/null 2>&1; then
  warn "ffmpegが見つかりません。MP3書き出しができません（WAV/FLACは利用できます）。Macなら 'brew install ffmpeg' でインストールできます。"
fi

# --- バックエンドのセットアップ（初回のみ） ---
if [ ! -d "$BACKEND_DIR/.venv" ]; then
  info "初回セットアップ: Python仮想環境を作成しています…"
  "$PYTHON_BIN" -m venv "$BACKEND_DIR/.venv"
fi

VENV_PY="$BACKEND_DIR/.venv/bin/python"
VENV_UVICORN="$BACKEND_DIR/.venv/bin/uvicorn"

if [ ! -f "$BACKEND_DIR/.venv/.deps_installed" ]; then
  info "初回セットアップ: 必要なライブラリをインストールしています…（数分かかることがあります）"
  "$VENV_PY" -m pip install --upgrade pip >/dev/null
  "$VENV_PY" -m pip install -r "$BACKEND_DIR/requirements.txt"
  touch "$BACKEND_DIR/.venv/.deps_installed"
fi

if [ ! -f "$BACKEND_DIR/.env" ]; then
  cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
fi

# --- フロントエンドのセットアップ（初回のみ） ---
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
  info "初回セットアップ: フロントエンドのライブラリをインストールしています…"
  (cd "$FRONTEND_DIR" && npm install)
fi

VITE_BIN="$FRONTEND_DIR/node_modules/.bin/vite"

# --- ポート使用状況の確認 ---
port_in_use() {
  "$PYTHON_BIN" - "$1" <<'PY'
import socket, sys
port = int(sys.argv[1])
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(0.5)
result = s.connect_ex(("127.0.0.1", port))
s.close()
sys.exit(0 if result == 0 else 1)
PY
}

ALREADY_RUNNING=0
if port_in_use "$BACKEND_PORT" && port_in_use "$FRONTEND_PORT"; then
  info "すでに起動しているようです。ブラウザだけ開きます。"
  ALREADY_RUNNING=1
fi

BACKEND_PID=""
FRONTEND_PID=""
CLEANED_UP=0

cleanup() {
  [ "$CLEANED_UP" -eq 1 ] && return
  CLEANED_UP=1
  info "終了処理をしています…"
  [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null || true
  [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM HUP

if [ "$ALREADY_RUNNING" -eq 0 ]; then
  info "サーバーを起動しています…"
  (cd "$BACKEND_DIR" && exec "$VENV_UVICORN" app.main:app --port "$BACKEND_PORT" --log-level warning) &
  BACKEND_PID=$!

  (cd "$FRONTEND_DIR" && exec "$VITE_BIN" --port "$FRONTEND_PORT" --strictPort) &
  FRONTEND_PID=$!

  info "起動を待っています…"
  READY=0
  for _ in $(seq 1 30); do
    if port_in_use "$BACKEND_PORT" && port_in_use "$FRONTEND_PORT"; then
      READY=1
      break
    fi
    sleep 1
  done
  if [ "$READY" -eq 0 ]; then
    error "起動に時間がかかっています。ターミナルのログを確認してください。"
  fi
fi

URL="http://localhost:$FRONTEND_PORT"
info "ブラウザで開きます: $URL"
if command -v open >/dev/null 2>&1; then
  open "$URL" 2>/dev/null || true
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$URL" 2>/dev/null || true
else
  info "自動でブラウザを開けませんでした。手動で $URL を開いてください。"
fi

info "認知機能サポートBGM AI が起動しました。"
info "終了するには、このウィンドウを閉じるか Ctrl+C を押してください。"

if [ "$ALREADY_RUNNING" -eq 1 ]; then
  exit 0
fi

wait
