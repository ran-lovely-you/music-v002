#!/usr/bin/env bash
# Finderでダブルクリックすると、認知機能サポートBGM AI が起動します。
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$DIR/scripts/start.sh"
