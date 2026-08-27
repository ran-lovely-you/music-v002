# 認知機能サポートBGM AI

高齢者の方が落ち着いて聴けるBGM（リラックス／穏やかな気分／集中しやすい環境づくり／睡眠前／軽い認知活動の時間など）を、AIを使って手軽に制作できるソフトウェアです。

> **重要（免責事項）**
> 本ソフトウェアが生成する音楽・スコア・チェック結果は、**音響・コンテンツ設計上の参考値**です。「認知症を予防する」「認知症を治療する」「記憶力を改善する」といった医学的効果を保証・断定するものではありません。UI・生成テキストでは「認知機能サポート」「リラックス」「集中環境」「穏やかな生活環境」といった表現のみを使用します。

---

## 目次

1. [できること](#できること)
2. [アーキテクチャ](#アーキテクチャ)
3. [ディレクトリ構成](#ディレクトリ構成)
4. [動作要件](#動作要件)
5. [Macでのセットアップ手順（Claude Codeを使う場合）](#macでのセットアップ手順claude-codeを使う場合)
6. [起動方法](#起動方法)
7. [使い方（BGM生成の流れ）](#使い方bgm生成の流れ)
8. [API設定方法（外部AI音楽生成サービスを使う場合）](#api設定方法外部ai音楽生成サービスを使う場合)
9. [WAV / MP3 / FLAC 書き出し方法](#wav--mp3--flac-書き出し方法)
10. [バックエンドAPI一覧](#バックエンドapi一覧)
11. [テストの実行方法](#テストの実行方法)
12. [トラブルシューティング](#トラブルシューティング)
13. [セキュリティ・著作権について](#セキュリティ著作権について)
14. [既知の制限・今後の拡張](#既知の制限今後の拡張)

---

## できること

- 7種類のBGMタイプ（朝の目覚め／昼間のリラックス／集中・軽い認知活動／回想・思い出／森・自然／夜・睡眠前／神秘的な森）
- 雰囲気・楽器・自然音・再生時間（5〜120分）・テンポ／BPMの詳細な組み合わせ
- 選択内容からの **Short / Detailed / Professional** 3種類の英語AIプロンプト自動生成 + Negative Prompt自動生成
- **APIキー不要で実際に音が出るローカル作曲エンジン（procedural プロバイダー）**を標準搭載
  - 外部AI音楽生成サービス（ElevenLabs Music API / Stability AI Audio API）にも `MusicProvider` インターフェース経由で対応（任意・APIキーが必要）
- 音響処理（Normalize / Fade in・out / Gentle Compression / EQ / Stereo Width / Silence Detection / Loop処理 / LUFSベースの自動音量調整）
- 音響分析（LUFS・Peak・RMS・クリッピング検出・周波数バランス・急激な音量変化・リズムの激しさ）
- 高齢者向け安全チェック（🟢 推奨 / 🟡 注意 / 🔴 要調整 の3段階表示）
- BGM品質スコア（100点満点、7項目のブレークダウン）
- プロジェクト保存（SQLite）、WAV(24bit/48kHz)・MP3(320kbps)・FLAC書き出し
- YouTube用メタデータ自動生成（タイトル案・説明文・タグ・ハッシュタグ・サムネイル用画像プロンプト・紹介文）
- 大きな文字・大きなボタン・高コントラスト・日本語UIのアクセシブルなウィザード画面

---

## アーキテクチャ

```
[React + TypeScript + Vite]  ── ウィザードUI（大きなボタン・日本語）
        │  fetch (/api/*)
        ▼
[FastAPI backend]
  ├─ Prompt Generator          … 設定 → Short/Detailed/Professional/Negative プロンプト
  ├─ MusicProvider Interface   … プロバイダーを差し替え可能にする抽象化
  │    ├─ ProceduralMusicProvider（デフォルト・APIキー不要・実際に作曲する内蔵エンジン）
  │    ├─ ElevenLabsMusicProvider（任意・要APIキー）
  │    └─ StabilityMusicProvider（任意・要APIキー）
  ├─ Audio Processing Engine   … Normalize / Fade / Compression / EQ / Stereo / Loop / LUFS調整
  ├─ Audio Analysis Engine     … LUFS / Peak / RMS / クリッピング / 周波数バランス / 動的変化 / リズム
  ├─ Safety Check              … 🟢/🟡/🔴 の高齢者向け安全判定
  ├─ Quality Scoring           … 100点満点スコア（医学的効果を示すものではない旨を明記）
  ├─ Exporter                  … WAV(24bit/48kHz) / MP3(320kbps) / FLAC
  ├─ Project Storage (SQLite)  … プロジェクトの保存・読込・削除
  └─ YouTube Metadata Generator
```

`MusicProvider` インターフェースの下に複数の実装を差し込む構成のため、新しいAI音楽生成サービスを追加したい場合は `backend/app/music_providers/` に新しいアダプタを1つ追加し、`registry.py` に登録するだけで済みます。

---

## ディレクトリ構成

```
music-v002/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI エントリポイント
│   │   ├── config.py               # .env 設定読み込み（Pydantic Settings）
│   │   ├── domain/                 # モデル・プリセット・安全設計の共通定義
│   │   ├── prompt/generator.py     # AIプロンプト自動生成
│   │   ├── music_providers/        # MusicProvider インターフェースと各アダプタ
│   │   ├── audio/                  # 合成(synthesis) / 処理(processing) / 分析(analysis) / 安全チェック / スコア
│   │   ├── export/exporter.py      # WAV / MP3 / FLAC 書き出し
│   │   ├── storage/                # SQLite (プロジェクト保存)
│   │   ├── youtube/metadata.py     # YouTube用メタデータ生成
│   │   └── api/                    # FastAPI ルーター群
│   ├── tests/                      # pytest テストスイート
│   ├── requirements.txt
│   ├── pytest.ini
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/                  # ホーム〜保存までのウィザード各画面
│   │   ├── components/             # ChoiceGrid / AudioPlayer(波形付き) / StepNav 等
│   │   ├── api/client.ts           # バックエンドAPIクライアント
│   │   ├── i18n/ja.ts              # 日本語UI文言（将来の多言語対応を見据えた構造）
│   │   └── styles/global.css       # 高齢者向けアクセシビリティを意識したスタイル
│   ├── package.json
│   └── vite.config.ts
├── .gitignore
└── README.md
```

---

## 動作要件

- **Python 3.11以上**
- **Node.js 18以上 / npm**
- **ffmpeg**（MP3書き出しに使用。WAV/FLACはPythonの `soundfile` のみで完結します）

---

## Macでのセットアップ手順（Claude Codeを使う場合）

Claude Codeを初めて使う方でも迷わないよう、ターミナル操作を1つずつ説明します。

### 1. 必要なツールをインストールする

Macに [Homebrew](https://brew.sh/) が入っていない場合はまずインストールしてください。

```bash
# Homebrewのインストール（未導入の場合のみ）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 必要なツールをインストール
brew install python@3.11 node ffmpeg git
```

### 2. Claude Codeでリポジトリを開く

```bash
# 好きな場所にプロジェクトを取得（すでに手元にある場合は cd だけでOK）
git clone <このリポジトリのURL> music-v002
cd music-v002

# Claude Codeを起動
claude
```

Claude Code内で「バックエンドをセットアップして」のように指示すれば、以下のコマンドを代わりに実行してくれます。もちろん自分でターミナルに入力しても構いません。

### 3. バックエンド（FastAPI）のセットアップ

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 環境変数ファイルを作成（APIキーは空のままでOK。procedural提供者はキー不要）
cp .env.example .env
```

### 4. フロントエンド（React）のセットアップ

新しいターミナルタブを開いて：

```bash
cd music-v002/frontend
npm install
```

これでセットアップは完了です。次の「起動方法」に進んでください。

---

## 起動方法

**ターミナル1（バックエンド）:**

```bash
cd music-v002/backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**ターミナル2（フロントエンド）:**

```bash
cd music-v002/frontend
npm run dev
```

ブラウザで `http://localhost:5173` を開くと、BGM制作アプリのホーム画面が表示されます。
（フロントエンドの開発サーバーは `/api` と `/outputs` を自動的に `http://localhost:8000` へプロキシします。）

---

## 使い方（BGM生成の流れ）

1. **ホーム** →「新しいBGMを作る」
2. **BGMタイプ選択**（朝の目覚め／昼間のリラックス／集中／回想／森・自然／夜・睡眠前／神秘的な森）
3. **雰囲気選択**（複数選択可。未選択ならおすすめが自動で使われます）
4. **楽器選択**（ピアノ・ハープ・オルゴール・アコースティックギター・フルート・クラリネット・マリンバ・柔らかなストリングス・パッド・ベル・チャイム）
5. **自然音選択**（雨・川・波・森・鳥・風・焚き火）
6. **再生時間・テンポ設定**（5〜120分／とてもゆっくり〜普通、詳細設定でBPM数値指定・生成方法も選択可）
7. **AIプロンプト確認**（Short / Detailed / Professional / Negative Prompt を自動表示）
8. **BGM生成**（procedural プロバイダーはAPIキー不要でその場で作曲します）
9. **音響チェック**（🟢/🟡/🔴 の安全判定とBGM品質スコアを表示）
10. **プレビュー**（波形表示付きの再生・一時停止・停止・音量・ループ）
11. **保存・書き出し**（プロジェクト保存、WAV/MP3/FLAC書き出し、YouTube用メタデータ生成）

---

## API設定方法（外部AI音楽生成サービスを使う場合）

デフォルトの `procedural` プロバイダーはAPIキーなしで動作します。外部の音楽生成AIサービスを使いたい場合のみ、`backend/.env` に以下を設定してください。

```dotenv
# .env
DEFAULT_MUSIC_PROVIDER=procedural   # procedural / elevenlabs / stability
ELEVENLABS_API_KEY=sk-...           # ElevenLabs Music APIを使う場合のみ
STABILITY_API_KEY=sk-...            # Stability AI Audio APIを使う場合のみ
```

- APIキーはソースコードに直接書かず、必ず `.env` で管理してください（`.env` は `.gitignore` 済みでコミットされません）。
- APIキーはログやエラーメッセージに一切出力されません。
- キー未設定のプロバイダーを選択した場合は、APIキーの値を含まない分かりやすいエラーメッセージが表示されます。
- `elevenlabs` / `stability` のアダプタは `MusicProvider` インターフェースに準拠した実装のリファレンスとして同梱していますが、各社APIの実際のエンドポイント仕様は変更される可能性があるため、ご利用の際は公式ドキュメントに合わせて `backend/app/music_providers/` 内のリクエスト内容を調整してください。

---

## WAV / MP3 / FLAC 書き出し方法

「保存・書き出し」画面のボタンから、以下の形式でその場でダウンロードできます。

| 形式 | 仕様 |
|---|---|
| WAV | 24bit / 48kHz |
| MP3 | 320kbps（ffmpeg + libmp3lame を使用） |
| FLAC | 可逆圧縮（24bit / 48kHz） |

---

## バックエンドAPI一覧

| メソッド | パス | 説明 |
|---|---|---|
| GET | `/api/health` | ヘルスチェック |
| GET | `/api/options` | BGMタイプ・雰囲気・楽器・自然音・時間・プロバイダー等の選択肢一覧 |
| POST | `/api/prompt/generate` | AIプロンプト（Short/Detailed/Professional/Negative）生成 |
| POST | `/api/bgm/generate` | BGM生成（音楽生成 → 音響処理 → 分析 → 安全チェック → スコア） |
| GET | `/api/bgm/{generation_id}` | 生成結果の再取得 |
| POST | `/api/bgm/{generation_id}/export?format=wav\|mp3\|flac` | 音声ファイル書き出し |
| POST | `/api/projects` | プロジェクト保存 |
| GET | `/api/projects` | プロジェクト一覧 |
| GET | `/api/projects/{id}` | プロジェクト取得 |
| DELETE | `/api/projects/{id}` | プロジェクト削除 |
| POST | `/api/youtube/metadata` | YouTube用メタデータ生成 |

例：procedural プロバイダーで5分のBGMを生成する

```bash
curl -X POST http://localhost:8000/api/bgm/generate \
  -H "Content-Type: application/json" \
  -d '{
        "bgm_type": "forest",
        "moods": ["healing", "natural"],
        "instruments": ["piano", "harp"],
        "nature_sounds": ["river", "birds"],
        "duration_sec": 300,
        "tempo_level": "slow"
      }'
```

---

## テストの実行方法

### バックエンド（pytest）

```bash
cd backend
source .venv/bin/activate
pytest
```

BGM生成・プロンプト生成・APIエラー・APIキー未設定・WAV/MP3/FLAC出力・長時間BGM（時間パラメータの検証）・音量チェック・クリッピング検出・プロジェクト保存/読込・API全体の統合テストまでを網羅しています（37テスト、全て実行環境で動作確認済み）。

### フロントエンド（型チェック・ビルド）

```bash
cd frontend
npm run build
```

`tsc -b` による型チェックと `vite build` によるプロダクションビルドを実行します。レスポンシブ対応（モバイル幅）は `src/styles/global.css` の `@media (max-width: 600px)` で確認できます。

---

## トラブルシューティング

| 症状 | 原因・対処法 |
|---|---|
| `ffmpeg: command not found` | `brew install ffmpeg` を実行してください。WAV/FLACのみならffmpegなしでも動作しますが、MP3書き出しには必須です。 |
| フロントエンドから「サーバーに接続できませんでした」と出る | バックエンド（`uvicorn app.main:app --reload --port 8000`）が起動しているか確認してください。 |
| BGM生成が「APIキーが設定されていません」で失敗する | `elevenlabs` / `stability` を選択した状態で `.env` にキーを設定していない場合に発生します。`procedural`（APIキー不要）を選ぶか、`.env` にキーを設定してください。 |
| ポート `8000` / `5173` が使用中 | `uvicorn app.main:app --reload --port 8001` のように別ポートを指定し、`frontend/vite.config.ts` の proxy先も合わせて変更してください。 |
| 60〜120分のBGM生成に時間がかかる／メモリを多く使う | 長時間の音声はメモリ上に float32 のステレオ波形として保持するため、120分では概算で3GB弱のメモリを使用します。まずは5〜15分で動作確認し、環境のメモリに応じて時間を調整してください。 |
| pytest がタイムアウトする／遅い | procedural プロバイダーは実際に音を合成するため、5分のBGM生成テストに20〜30秒程度かかります（意図した挙動です）。 |
| 保存したプロジェクトが再起動後に消える | `backend/data/projects.db`（SQLite）と `backend/data/outputs/` に保存されます。`.env` の `DATA_DIR` を変更した場合はそちらを確認してください。 |

---

## セキュリティ・著作権について

- APIキーはソースコードに直接書かず `.env` で管理し、`.gitignore` によりコミット対象から除外しています。
- APIキーの値はログ・エラーメッセージに一切出力しません。
- ユーザーが生成した音楽ファイルを外部へ無断送信することはありません（外部AIプロバイダーを明示的に選択した場合のみ、そのプロバイダーへプロンプトを送信します）。
- 生成する音楽は完全オリジナルの作曲を目的としており、特定の既存楽曲を模倣・複製する機能は提供していません。
- 外部AI音楽生成サービスや自然音素材を利用する場合は、各サービス・素材の商用利用・YouTube利用・再配布に関するライセンス条件を必ずご自身でご確認ください。

---

## 既知の制限・今後の拡張

- `procedural` プロバイダーは加算合成ベースの内蔵エンジンであり、実在の楽器を録音したものではありません。より高品質な音源が必要な場合は外部AI音楽生成サービスのアダプタをご利用ください。
- 120分など長時間のBGMは、生成・分析処理をメモリ上の波形データとして扱うため、環境のメモリ量に応じて時間がかかる場合があります。
- `elevenlabs` / `stability` アダプタは `MusicProvider` インターフェースの実装例です。各社の実際のAPI仕様に応じて調整してください。
- 現在は日本語UIのみですが、`frontend/src/i18n/ja.ts` と同じキー構造で `en.ts` を追加すれば英語対応を拡張できる構造にしています。
