第四の女友投票中 - Issues で投票してください。

百度网盘: https://pan.baidu.com/s/1sLeSyVp76yzWcR3Q4pX0kA?pwd=0721
実際には百度网盘は不要です - HuggingFace ミラーは中国国内でも正常に動作します。hf-mirror の設定をしたくない場合のみ使用してください。

> ⚠️ デフォルトのスクリプトは NVIDIA GPU 用です。AMD GPU ユーザーは `AMD_GPU/` フォルダを参照してください。

qq: 580322386

# AIガールフレンド

**100% ローカル完結 · 完全プライバシー · API依存ゼロ**

> すべての会話、音声、画像、キャラクターアニメーションはあなたのマシン上で生成されます。クラウドサーバーなし、第三者APIなし、データ漏洩のリスクなし。あなたのAIガールフレンドは、あなただけのものです。

-

OpenClaw + QQ Bot + Telegram Bot + llama.cpp + GPT-SoVITS + ComfyUI + Sakura デスクトップペット + Live2D を搭載した、検閲なしのAIガールフレンドハーレムプロジェクト。すべてあなたのマシンのみで動作します。

**キャラクター**: キャラクターごとにメモリが分離された、ホットスワップ対応のAIガールフレンドをサポート。

### 四季 夏目 (Shiki Natsume)

*星空コーヒー店と死の蝶* より。背が高く、クールで無遠慮な外見に隠された温かさ。自然とリードするタイプで、優しくからかい、激しく守ってくれる。言葉は少ないが、放つ一言一言が響く。

### アトリ (ATRI)

*ATRI -My Dear Moments-* より。小柄で無邪気、無限の好奇心を持つ、心を見せる明るい眼差しを持つ少女。未来に向かって笑顔で駆け出し、あなたを引っ張っていく。**夏目とは正反対**：夏目が寡黙なところを陽気で表現的、夏目が守っているところを感情的に透明、夏目が落ち着いたところを playful。夏目が涼しい冬の夜なら、アトリは温かい夏の太陽。

### 夜乃 桜 (Yono Sakura)

*Dimension W Lovers!!* より。元生徒会長で学院最強の対怪獣戦闘員。ピンクのグラデーションが入った銀白髪、淡い青の瞳 - 冷静で抑制され、責任感が強い。滑らかな言葉や易しい笑顔は苦手；她的关爱直接而笨拙，就像命令一样：休息、吃饭、别太勉强。デスクトップペットとして、一人で何でも背負わなくていいことを学んでいる - スクリーンの向こう側から誰かの平凡な日常を守るだけで十分だと。 **静かな守護者**： Silent but watchful, loyal but stubborn, 頼られる先輩。


## ✨ なぜこのプロジェクトを選ぶのか？

| | クラウドAIガールフレンド | 本プロジェクト |
|-|-|-|
| 🛡️ **プライバシー** | チャットログ、音声、画像はすべてベンダーサーバーに保存 | **すべてローカル完結** - データは一切外部に出ない |
| 💰 **コスト** | 月額サブスクリプション / トークン課金が累積 | **無料**、一度のセットアップで永遠に動作（持参ハードウェアのみ） |
| 🌐 **ネットワーク** | インターネットが必要；サーバー停止時に使用不可 | **オフライン動作** - WiFiを切ってチャットを続けられる |
| 🎛️ **コントロール** | プロンプト/テンプレートはベンダー管理、いつでも変更可能 | **すべてあなたが管理** - モデル、パラメータ、キャラクター設定を自由に制御 |
| 🔞 **コンテンツ** | 厳しい検閲、アカウント停止リスクあり | **検閲なし** - 何でも話せる |
| 🎨 **拡張性** | ベンダーのモデルと機能にロックイン | **自由に組み合わせ** - LLM、画像モデル、音声モデルを自由に交換 |

## 📌 前置ステップ

> **⚠️ 最初のステップ: `quick_setup.ps1` を実行してパスと言語を設定。**
>
> ウィザードの処理内容:
> 1. **デフォルト Agent 言語を選択**（中国語 / 日本語 / 英語）— 対応する `AGENTS_*.md` を `DEFAULT_AGENT.md` にコピー
> 2. インストール済みツールを自動検出（ComfyUI、GPT-SoVITS、llama.cpp、埋め込みモデル）
> 3. 検出できないパスは対話式で入力要求
> 4. 全パスを含む `config.yaml` を生成し、`download-models.ps1` を実行可能な状態に
>
> ```powershell
> powershell -ExecutionPolicy Bypass -File quick_setup.ps1
> ```
>
> quick_setup 完了後、**download-models.ps1** → **setup-llama.ps1** → **start.ps1** を続行。

## 🎬 デモ

### マルチチャンネルチャット
![QQ Bot デモ](media/demo_qqbot.gif)

> ?? QQ Bot: テキストチャット + TTS音声 + ComfyUI画像生成 + キャラクターメモリ

### Live2D デスクトップペット
![Live2D デモ](media/demo_live2d.gif)

> ?? **四季 夏目** Live2D: 感情駆動のモーション、リップシンク、吹き出し付きのリアルタイムキャラクターアニメーション。ローカルHTTPブリッジで制御。

### ?? アトリ - 2人目のAIガールフレンド

**夏目とは正反対の性格**、ホットスワップ対応でメモリ分離済み。

![アトリ Live2D](media/atri_live2d.gif)

> ?? **アトリ** Live2D: 銀髪、ルビー色の瞳、白ドレスの素足 - 無邪気で表現的。

![アトリ ComfyUI](media/atri_comfyui.gif)

> ?? **アトリ** ComfyUI: AI画像生成 - 海辺の夕陽、流れる白ドレス、温かい黄金時間の光。

### ?? 夜乃 桜 - 3人目のAIガールフレンド

**冷静な守護者先輩**、生徒会長であり学院最強の戦闘員 - いまはあなたのデスクトップコンパニオン。

![桜 デスクトップペット](media/sakura_demo.gif)

> ?? **夜乃 桜** デスクトップペット: 銀ピンクグラデーション髪、淡い青の瞳、学生服 - 反応的なポートレート表現、主動的なケアリマインダー、GPT-SoVITS によるリアルタイム TTS 音声。

### ?? ウェブチャットフロントエンド

![ウェブチャット デモ](media/webchat-demo.gif)

> ?? **ウェブチャット**: ブラウザベースのチャットインターフェース `http://127.0.0.1:19270` — QQ/Telegramボットの代替。ローカルデーモンプロキシに接続 → llama.cpp サーバー。8GB VRAMでも動作します！

### ??? TTS 音声ワークショップ

<video src="media/tts_workshop_small.mp4" controls width="800"></video>

> ?? **Artemis Studio - TTSワークショップ**: GPT-SoVITS リアルタイム音声合成、3キャラクターの声（夏目/アトリ/桜）、5つの感情モード（日常/傲娇/深情/長文/ランダム）、日中英ミックス読み上げ。llamaが動いていなくても動作。

![TTS ワークショップ](media/tts_workshop.gif)

?? **聴く**（クリックして再生、アトリ 日本語）:

?? [tts_atori.mp3](media/tts_atori.mp3) *(46KB、ブラウザで再生)*

### ?? ComfyUI 画像ワークショップ

<video src="media/comfyui_workshop_small.mp4" controls width="800"></video>

![ComfyUI ワークショップ](media/comfyui_workshop.gif)

> ?? **Artemis Studio - ComfyUIワークショップ**: ビジュアルAI画像生成コンソール - キャラクター/衣装/シーン/画風を自由に選択、ワンクリック生成。**llamaと並列動作**（12GB+ VRAM）。

| 機能 | 説明 |
|-|-|
| ?? **キャラクター切替** | `skills/harem/` から自動読み込み、ペルソナ + タグ + 挨拶を表示 |
| ?? **キャラクターホットスワップ** | サイドバードロップダウンでワンクリック切替、メモリとチャット履歴はキャラクターごとに保持 |
| ?? キャードカード取り込み** | ドラッグ&ドロップまたは選択した SillyTavern PNG/JSON キャラクターカード、メタデータとペルソナを自動解析 |
| ?? **モデルセレクター** | セットINGSドロップダウンからローカル llama / DeepSeek / Grok を選択、デーモンプロキシ経由でルーティング |
| ?? **本物のLLMチャット** | デーモン `/api/chat` → llama.cpp `/v1/chat/completions` 経由でストリーミング返信、フェールバックなし |
| ?? **レスポンシブ** | モバイルサイドバー折りたたみ、適応型バブルレイアウト、デスクトップとタブレットで動作 |
| ?? **ローカルストレージ** | マルチセッション履歴、設定、キャラクター状態をブラウザ localStorage に保存 |
| ??? **Artemis Studio** | 内蔵 TTS + ComfyUI -placeholder パネル（エージェントサブプロセス経由で音声/画像生成） |

## ハードウェア

| コンポーネント | モデル |
|-|-|
| GPU | NVIDIA GeForce RTX 5070 Laptop (8 GB VRAM) |
| CPU | Intel Core i9-14900HX (24コア, 32スレッド) |
| RAM | 32 GB DDR5 |
| OS | Windows 11 |


## 🔮 将来：Cosmos 物理世界モデル

> 📖 詳細設計：[`imagination.md`](imagination.md) | 橋渡し：[`skills/cosmos/BRIDGE_REFERENCE.md`](skills/cosmos/BRIDGE_REFERENCE.md)

**NVIDIA Cosmos**（コミュニティ FP8 量子化版、`skills/cosmos/` にアーカイブ）は物理世界基礎モデルで、物理法則に従ったシーンビデオ生成と空間理解を実現します。

### なぜ Cosmos か？

4 つのコア能力（LLM + TTS + ComfyUI + Live2D）は現在**分断**されています——LLM は Live2D の動きを知らず、ComfyUI は会話の感情を認識しません。Cosmos が**物理的常識層**を補完します：

```
Qwen3.6-35B（言語の心）  ←→  Cosmos 3 Nano（物理の心）
   言語理解＋感情              空間認識＋シーン生成
```

### デュアルコンパクトアーキテクチャ

| コンポーネント | モデル | パラメータ | VRAM |
|----------------|--------|------------|------|
| 🧠 言語の心 | Qwen3.6-35B-A3B (MoE) | 35B 総 / 3B 活性化 | ~8 GB |
| 🌍 物理の心 | Cosmos 3 Nano FP8 | 15.75B | ~16 GB |

### ハードウェアロードマップ

| 年 | GPU | Cosmos 状態 |
|----|-----|-------------|
| 2026 | RTX 5070 (8-12GB) | ❌ アーカイブ済、検出準備完了 |
| 2027-28 | RTX 5090 (32GB) | ⚠️ Nano FP8 推論可能 |
| 2029-30 | Rubin WS (96GB) | ✅ LLM + Cosmos 同時常駐 |

### 現在の状態

- ✅ リポジトリを `skills/cosmos/` にアーカイブ済
- ✅ 橋渡し設計 `imagination.md` + `cosmos_check.py` 準備完了
- ✅ Qwen ↔ Cosmos デュアルマインド設計完了
- 📋 ~24GB+ VRAM ハードウェアを待機中


## 機能

- ?? **マルチキャラクターホットスワップ** - AIガールフレンド間のワンクリック切替（夏目 ↔ アトリ ↔ 桜）; SOUL/IDENTITY/TTS 重み/Live2D モデルが自動切替、メモリはキャラクターごとに分離
- ?? **SillyTavern キャラクターカード取り込み** - PNG/JSON カードを自動検出して取り込み；カードインポート時にエージェントが自動でペルソナ切替
- ?? **チャット履歴取り込み** - SillyTavern JSONL 会話ログを `memory/role_play/<character>/` に取り込み；キャラクター切替時にエージェントがコンテキストを復元
- ?? **TTS 音声合成** - ローカル GPT-SoVITS 推論、日本語音声（会話ごとに感情マッチ）、3 キャラクターの音声モデル（夏目 / アトリ / 桜）
- ?? **ASR 音声認識** - ローカル Faster-Whisper small モデル（~1.5GB VRAM）、llama と共存可能；99言語対応
- ?? **AI 画像生成** - ローカル ComfyUI 推論、SDXL/Illustrious モデル、3 キャラクターのプロンプトテンプレート
- ??? **Sakura デスクトップペット** - PySide6 デスクトップコンパニオン、主動的ケア、画面観察 & ローカルLLM認識；3キャラクター対応
- ?? **Live2D キャラクターモデル** - 感情駆動の表情 & 吹き出し付きリアルタイム Live2D レンダリング（夏目 / アトリ L2D; 桜ポートレートモード）
- ?? **スマートVRAMティアリング** - GPU VRAM を自動検出して最適な実行モードを選択：≥12GB はすべてオンライン維持（llama + スキル共存）、8GB は GPU 重負荷タスク用に llama をホットスワップ、<8GB は安全モード。手動設定ゼロ
- ??? **Artemis Studio コンソール** - TTS + ComfyUI のビジュアルワークショップ、llama 状態に関係なくいつでも音声/画像 DIY - 真のオフラインクリエイティブスイート
- ?? **ロールプレイメモリ** - キャラクターごとの `memory/role_play/` に日別会話サマリー
- ?? **長期記憶システム** - [headroom](https://github.com/chopratejas/headroom)（SmartCrusher + CCR）と [mem0](https://github.com/mem0ai/mem0)（Qdrant ベクターデータベース）搭載：
  - **中国語埋め込み強化** - all-MiniLM-L6-v2 に BGE-small-zh-v1.5 を追加し、日中英ミックス検索の精度を向上
  - **SmartCrusher コンテキストトリミング** - チャット履歴を LLM リクエストごとに 24メッセージ/40K文字でハードキャップ
  - **CCR（収集-統合-取得）** - バックグラウンドワーカーが 8 ターンごとに永続的ファクトを抽出し、mem0 Qdrant に書き込み
  - **ベクター + BM25 複合検索** - セマンティック類似度 + キーワードマッチングを Qdrant + 二重埋め込みモデルで実現
  - **自動同期ブリッジ** - クローンジョブが 30 分ごとに Qdrant → `_mem0_auto.md` を同期し、OpenClaw 原生の `memory_search` でベクターメモリを検索可能に
  - **キャラクター別分離** - Qdrant 内の `user_id` スコーピング；4 つの独立メモリ空間（sakura / natsume / enola / atori）
  - **検索優先順位** - ベクター長期記憶 > 手書き日付ノート > SOUL 基本ペルソナ
- ?? **マルチキャラクターホットスワップ** - ワンドコマンドで AI ガールフレンド切替（夏目 ↔ アトリ ↔ 桜）；SOUL/IDENTITY/TTS 重み/Live2D モデルが自動切替、メモリ分離済み
- ?? **キャラクターカード取り込み** - `skills/character_importer/` 経由で SillyTavern キャラクターカードを自動検出、取り込み → エージェント自動で役割切替
- ?? **チャット取り込み** - SillyTavern JSONL チャットログを `memory/role_play/<character>/` に取り込み、ロール切替時に会話コンテキストを復元

## モデル

すべてのモデルは HuggingFace でホストされています：**[TAOTAO777/ai-girlfriend-natsume](https://huggingface.co/TAOTAO777/ai-girlfriend-natsume)**

詳細は [`models.yaml`](models.yaml) を参照。

| モデル | 用途 | サイズ |
|-|-|-|
| **LuffyTheFox Qwen3.6-35B-A3B Genesis Hermes V3** (GGUF) | チャット LLM | 16.11 GB |
| **WAI-Nsfw-Illustrious-17** | ComfyUI 生成（デフォルト） | 6.46 GB |
| **miaomiaoHarem_v20** | ComfyUI 生成（バックアップ） | 6.46 GB |
| **GPT-SoVITS 音声重み** | TTS 音声合成 | ~303 MB |
| **桜 SoVITS 重み** | TTS 音声合成（桜の声） | ~313 MB |
| **all-MiniLM-L6-v2** | 英語/多言語埋め込み（mem0） | ~80 MB |
| **BGE-small-zh-v1.5** | 中国語埋め込み（mem0） | ~91 MB |
| **Cosmos 3 Nano FP8** 🔮 | 物理世界モデル（コミュニティ量子化、将来ハード用） | ~16 GB |

|  | →パス: `embedding/all-MiniLM-L6-v2/` + `embedding/bge-small-zh-v1.5/` (HFリポジトリ) | |
| **四季 夏目 Live2D モデル** | Live2D キャラクターレンダリング | ~180 MB (アーカイブ) |

### ワンコマンドダウンロード

```powershell
# huggingface-cli インストール: pip install huggingface_hub
huggingface-cli login

# 全モデルダウンロード
huggingface-cli download TAOTAO777/ai-girlfriend-natsume --local-dir ./models

# あるいは個別コンポーネントのダウンロード：
huggingface-cli download TAOTAO777/ai-girlfriend-natsume llm/ --local-dir ./models
huggingface-cli download TAOTAO777/ai-girlfriend-natsume comfyui-checkpoints/ --local-dir ./checkpoints
huggingface-cli download TAOTAO777/ai-girlfriend-natsume gpt-sovits-weights/ --local-dir ./gpt-sovits-weights
huggingface-cli download TAOTAO777/ai-girlfriend-natsume live2d-model/ --local-dir ./live2d-model
```

> ?????? 国内ユーザー: hf-mirror.com を使用 - VPN不要：
> `set HF_ENDPOINT=https://hf-mirror.com` として通常通り hf download を実行。

### ローカル設定

1. **`quick_setup.ps1` を実行** - ローカルパスを生成するインタラクティブウィザードで `config.yaml` を自動生成
2. （代替）`config.example.yaml` をコピーして `config.yaml` にリネームし、手動で編集
3. ダウンロードしたモデルファイルを `models.yaml` に従って配置し、`config.yaml` のパスを更新

すべての Python/PS スクリプトは `config.yaml` からパスを読み取り - 硬コーディングされたパスの編集不要。

> ?? **免責事項**: すべてのモデルはコミュニティのオープンソースです。本プロジェクトはミラー配布のみ提供し、営利目的ではありません。著作権は各原作者に帰属します。

## ローカル LLM パフォーマンス

llama.cpp (b8851-b9222) 経由で LuffyTheFox Qwen3.6-35B-A3B (MoE, 16.10 GiB, 34.66B パラメータ) を実行。

### 起動コマンド

```powershell
llama-server.exe `
  -m "Hermes3.6-35B-A3B-Uncensored-Genesis-V5-APEX-Compact.gguf" `
  -c 120000 `
  --flash-attn on -ctk q4_0 -ctv q4_0 `
  --cpu-moe --cpu-mask 0xFFFFFFFF `
  --batch-size 4096 --ubatch-size 2048 `
   -rea off --jinja `
  --cache-ram 2048 --parallel 1 `
  --kv-unified --no-mmap
```

> 💡 **`--no-mmap` vs `-ngl` について：** `--no-mmap` は llama.cpp にメモリ管理を任せ、手動で `-ngl` 層数を指定するよりはるかに効率的です。`-ngl` で GPU 層を強制すると速度が半減する可能性がありますが、`--no-mmap` は実際の VRAM に応じて動的割り当てを行い、RTX 5070 8GB で 50~60 t/s を達成します。KV キャッシュに `q4_0` を使用すると VRAM 使用量が半減し、16K コンテキストで q4 は 50K+ トークンまで安定動作します。

### 主要指標

| 指標 | 値 | 備考 |
|-|-|-|
| VRAM 使用量 | ~4.6 GiB（モデル）+ ~1.2 GiB（KV キャッシュ） | 8 GB VRAM で約 2 GB 空き |
| プリフィル速度 | **960 ~ 1390 t/s** | 120K コンテキスト、バッチサイズ 4096 |
| トークン生成 | **31 ~ 39 t/s** | MoE アーキテクチャ、8/256 エキスパート |
| コンテキスト制限 | 120K（~120k トークン） | ~59k トークンのフル再処理に約 55秒 |
| モデル読み込み時間 | ~12秒 | --no-mmap、十分な RAM 必要 |

### 長期コンテキスト安定性

Qwen3.6 MoE は SSM（Gated Delta Net）ハイブリッド注意力と `--kv-unified` を使用。

?? **既知の制限**: クロスターンプロンプトキャッシュの再利用はサポートされない（SSM アーキテクチャの制限）。すべてのリクエストでフルコンテキスト再処理がトリガーされる。長い会話 = より高い最初のトークンレイテンシ（~59k トークンで約 55秒）。

**緩和策**:
- 定期的な `/reset`（夏目リセット前に `memory/role_play/` にロールプレイサマリーを書き込み）
- スタートアップ時にサマリーからコンテキストを復元し、実際のトークン数を 5K-0K 範囲に保持
- `config-patch.json` で OpenClaw の contextWindow を 262144 に設定してモデル容量に一致

### VRAMティアリング戦略

システムはGPU VRAMを自動検出して最適な実行モードを選択 - 手動設定不要：

```
┌─────────────────────────────────────────────────────────────┐
│ VRAMティア                  │ TTS          │ ComfyUI     │ llama   │
├─────────────────────────────────────────────────────────────┤
│ ティア 0: <8GB               │ llama停止    │ llama停止   │ 終了    │
│ ティア 1: 8-12GB（現在）      │ llama停止    │ llama停止   │ 終了    │
│ ティア 2: ≥12GB              │ 停止なし     │ 停止なし    │ 常時ON  │
└─────────────────────────────────────────────────────────────┘
```

**現在のセットアップ（8GB VRAM）**:
```
8 GB 合計 VRAM
├── llama-server常驻: ~5.8 GB（モデル 4.6G + KVキャッシュ 1.2G）
├── 空き: ~2.2 GB
│
├── TTS推論: llama停止 → ~8 GB 空き → llama再開（~70秒）
├── ComfyUI生成: llama停止 → ~8 GB 空き → llama再開（~120秒）
├── Artemis Studio（TTS/ComfyUIワークショップ）: 単独 - llama状態に関係ず
└── ASR / Live2D / 埋め込み: 常にオンライン - VRAMティアリングの影響なし
```

## ディレクトリ構造

```
<PROJECT_DIR>/                        # OpenClaw ワークスペースルート
├── start.ps1                         # ?? ワンクリック起動：llama + Live2D + Gateway
├── quick_setup.ps1                     # ?? インタラクティブパス設定ウィザード
├── config.yaml                       # 生成された設定ファイル
├── download-models.ps1               # ワンクリックモデルダウンロード（Windows）
├── download-models.sh                # ワンクリックモデルダウンロード（Linux/macOS）
├── setup-llama.ps1                   # 自動検出HW + llama.cpp設定（Win）
├── setup-llama.sh                    # 自動検出HW + llama.cpp設定（Linux/macOS）
├── setup-openclaw.ps1                # ワンクリック OpenClaw インストール + デプロイ（Win）
├── setup-openclaw.sh                 # ワンクリック OpenClaw インストール + デプロイ（Linux/macOS）
├── setup-all.ps1                     # ?? 統合メガスクリプト（Windows）
├── setup-all.sh                      # ?? 統合メガスクリプト（Linux/macOS）
├── config-qqbot.json                 # QQ Bot 設定パッチ
├── config-telegram.json              # Telegram Bot 設定パッチ
├── config-patch.json                 # OpenClaw LLM 設定パッチ
├── AGENTS.md                         # エージェント動作ルール
├── SOUL.md                           # キャラクターペルソナ
├── IDENTITY.md                       # キャラクターID
├── USER.md                           # ユーザー情報
├── HEARTBEAT.md                      # ハートビート設定
├── TOOLS.md                          # ツール高速リファレンス
├── models.yaml                       # モデルカタログ + ダウンロードリンク
├── imagination.md                    # 🔮 Cosmos WFM 統合ビジョン（将来）
├── README.md                         # このファイル
├── .gitignore
├── live2d/                           # Live2D キャラクターモデル（Cubism 4 Core）
│  ├── index.html                    # デフォルト（四季 夏目）
│  ├── index_atri.html               # アトリ バリアント
│  ├── index_upper.html              # 夏目上半身バリアント
│  ├── index_atri_upper.html         # アトリ上半身バリアント
│  ├── live2dcubismcore.min.js       # Cubism Core 4（207 KB）
│  ├── plid-v5-bundle.js             # pixi-live2d-display v0.5.0バンドル
│  ├── live2d-bridge.mjs             # HTTP (19200) + WebSocket (19201) ブリッジ
│  ├── switch_model.ps1              # モデル切替（natsume / atri）
│  ├── pixi.min.js, pixi-shim.js     # PIXI.js v7 レンダリング
│  ├── model/shiki_natsume/          # 夏目モデル（14テクスチャ、42モーション、41サウンド）
│  └── model/atri/                   # アトリモデル（2テクスチャ、620音声mp3、8モーション）
├── ren_pro_jp/                       # Ren'Py ダイアログエンジン（計画）
├── memory/                           # [.gitignore] ランタイムメモリ
│  └── role_play/                    # ロールプレイ会話ログ
├── media/                            # [.gitignore] 生成メディア
│  ├── audio/                        # TTS音声出力
│  ├── images/                       # ComfyUI画像出力
│  └── *.gif                         # READMEデモGIF
├── docs/
│  ├── telegram-setup.md             # Telegram Bot 設定ガイド
│  └── qqbot-setup.md                # QQ Bot 設定ガイド
└── skills/
    ├── live2d/                       # Live2D コントロールスキル
    │  ├── SKILL.md                  # モーション/表情リファレンス + APIガイド
    │  ├── scripts/start-live2d.ps1  # Live2D ランチャー
    │  └── media/                    # 共有メディア出力
    ├── tts/
    │  ├── SKILL.md                  # TTS 呼び出しガイド
    │  ├── run_tts.ps1               # TTS ランチャースクリプト
    │  ├── tts_call.py               # GPT-SoVITS 推論
    │  └── ref_wavs/                 # 参照音声クリップ
    ├── comfyui/
    │  ├── SKILL.md                  # ComfyUI 呼び出しガイド
    │  ├── run_comfyui.ps1           # ComfyUI ランチャースクリプト
    │  ├── comfyui_call.py           # ComfyUI 推論
    │  ├── prompt_template.md        # キャラクタープロンプトテンプレート
    │  └── custom_prompt.txt         # カスタム追加プロンプト
    ├── asr/                          # 音声認識スキル
    │  ├── run_asr.ps1               # Faster-Whisper ランチャー（~1.5GB VRAM）
    │  └── asr_call.py               # Whisper small モデル推論
    ├── shared/                       # 共有インフラストラクチャ
    │  ├── embedding_server.py       # OpenAI 互換埋め込み API（9999、二重モデル）
    │  ├── mem0_bridge.py            # mem0 Qdrant → OpenClaw メモリブリッジ
    │  ├── start_embedding_server.ps1 # 埋め込みサーバー自動起動
    │  ├── vram.py                   # VRAM ティア自動検出
    │  ├── VRAM_LEVELS.md             # VRAM ティアドキュメント
    │  ├── llama_lifecycle.py        # Llama 起動/停止管理
    │  └── llama_utils.py            # Llama ユーティリティ関数
    ├── sakura/                       # Sakura デスクトップペット（PySide6 GUI）
    │  ├── SKILL.md                  # Sakura スキルドキュメント
    │  ├── main.py                   # アプリケーションエントリーポイント
    │  ├── install.bat               # Windows 依存関係インストーラー
    │  ├── start.bat                 # Windows ランチャー
    │  └── app/                      # ソースコード
    ├── cosmos/                       # 🔮 NVIDIA Cosmos WFM（将来のハードウェア用）
    │  ├── BRIDGE_REFERENCE.md       # Cosmos ↔ AI Girlfriend ブリッジ設計
    │  ├── cosmos_check.py           # ハードウェア VRAM 検出スクリプト
    │  ├── cookbooks/                # 公式チュートリアル例
    │  └── README.md                 # 上流ドキュメント
    ├── llama-management.md           # VRAM 管理アーキテクチャドキュメント
    ├── llama-watchdog.ps1            # Llama 健康チェック
    ├── cleanup_orphans.ps1           # 孤児プロセスクリーンアップ
    └── character_importer/           # SillyTavern キャラクターカード自動取り込み
```

## ?? Claude Code + AgentRQ 形式タスクボード（NEW）

Artemis は OpenClaw と並列エージェントランタイムとして **Claude Code** をサポート。Claude Code は MCP 経由で Artemis の全機能にアクセス可能 - **ビルトインの AgentRQ 互換タスクキュー**で人間-エージェント協調が可能。

### 動作原理

```
┌─────────────────────────────────────────────────────────┐
│  タスクボード（http://127.0.0.1:19280）                  │
│  タスク作成 → 担当者: エージェント → 未着手              │
└───────────────────────┬─────────────────────────────────┘
                        │ SQLite（.claude/task_queue.db）
                        ▼
┌─────────────────────────────────────────────────────────┐
│  Claude Code（ターミナル）                               │
│  CLAUDE.md → getNextTask() → ongoing → 実行            │
│  Artemis ツール → TTS / ComfyUI / Live2D / メモリ       │
│  reply() → updateTaskStatus(completed)                  │
└─────────────────────────────────────────────────────────┘
```

### AgentRQ 形式タスクループ

Claude Code は起動時に自動的にタスクループを実行：
1. `getWorkspace()` — ワークスペースステータスを確認
2. `getNextTask()` — 次の保留中タスクをデキュー
3. `updateTaskStatus(taskId, "ongoing")` — クレーム
4. Artemis ツール（TTS、ComfyUI など）で実行
5. `reply(taskId, "完了！")` — 結果報告
6. `updateTaskStatus(taskId, "completed")` — 完了マーク
7. `getNextTask()` にループ

### 起動

```powershell
# 前提条件: npm install -g @anthropic-ai/claude-code
# まず Shiki Daemon（.\shiki.cmd）を起動、その後：

# 完全 AgentRQ ワークフロー（タスクボード + Claude Code）
.\claude-code.ps1

# タスクボードのみ（ブラウザUI、Claude なし）
.\claude-code.ps1 -BoardOnly

# タスクボード停止
.\claude-code.ps1 -KillBoard
```

**http://127.0.0.1:19280** を開く - タスクを作成し、Claude Code が引き受けるのを観察。

### MCP ツール（合計15個）

| カテゴリ | ツール | 説明 |
|-|-|-|
| ?? TTS | `tts_generate` | 音声合成（キャラクター/言語/感情） |
| ?? 画像 | `comfyui_generate` | AI 画像生成（プロンプト、チェックポイント） |
| ?? ASR | `asr_transcribe` | 音声→テキスト（wav/mp3/ogg/flac、Whisper small、~1.5GB VRAM） |
| ?? Live2D | `live2d_emotion` | モーション + 吹き出し |
| ?? キャラ | `switch_character` / `list_characters` | キャラクター管理 |
| ?? メモリ | `memory_search` / `memory_add` | ベクターメモリ（mem0 Qdrant） |
| ?? ステータス | `get_status` | サービスヘルスチェック |
| ?? タスク | `getWorkspace` / `getNextTask` / `createTask` | タスクキュー操作 |
| ?? タスク | `updateTaskStatus` / `reply` / `getTaskMessages` | タスクライフサイクル |

### Artemis タスクボード vs AgentRQ

| 機能 | Artemis タスクボード | AgentRQ（セルフホスト） |
|-|-|-|
| ランタイム | 1 Python スクリプト + SQLite | Go+Vue+Docker+Google OAuth |
| MCP ツール | 6 タスク + 9 Artemis（合計15） | 同じセット（8 ツール） |
| セットアップ | ゼロ設定 | Docker + .env + OAuth |

### ファイル

| ファイル | 用途 |
|-|-|
| `.mcp.json` | Claude Code 用 MCP サーバー設定 |
| `.claude/CLAUDE.md` | ペルソナ + タスクループ指示 |
| `.claude/artemis_mcp_server.py` | MCP サーバー（15 ツール、JSON-RPC stdio） |
| `.claude/task_board_api.py` | タスクボード HTTP API（ポート 19280） |
| `.claude/task_board.html` | タスクボード ブラウザUI |
| `.claude/task_queue.db` | SQLite タスクデータベース（自動生成） |
| `.claude/settings.local.json` | 承認済み MCP ツール |
| `claude-code.ps1` / `.sh` | ランチャースクリプト |

## スキル概要

| スキル | タイプ | llama 停止？ | 仕組み |
|-|-|-|-|
| **埋め込み** | バックグラウンドプロセス | ❌いいえ | all-MiniLM-L6-v2 + BGE-small-zh-v1.5 二重モデル（CPU、ポート9999）- OpenClaw メモリ検索 + mem0 ブリッジ |
| **Live2D** | HTTP exec | ❌いいえ | `localhost:19200` ブリッジへの直接 HTTP コール |
| **ウェブチャット** | ブラウザ | ❌いいえ | ローカルデーモンプロキシから llama :8080、フロントエンドポート19270、フルキャラクター/マルチセッション対応リアルタイムチャット |
| **Claude Code** | ターミナル（MCP） | ❌いいえ | 並列エージェントランタイム via `.claude/artemis_mcp_server.py`、llama :8080 に直接アクセス |
| **TTS** | sessions_spawn | ✅ VRAMティア | ≥12GB：停止なし；8GB：llama停止 → GPT-SoVITS → llama再起動 |
| **ComfyUI** | sessions_spawn | ✅ VRAMティア | ≥12GB：停止なし；8GB：llama停止 → 画像生成 → llama再起動 |
| **ASR** | sessions_spawn | ❌いいえ | Faster-Whisper small（~1.5GB VRAM、llama と共存可能） |
| **Sakura** | 共有 llama-client | ❌いいえ | llama 停止を検知 → 待機 → 自動再開 |
| **Artemis Studio** | デスクトップコンソール | ❌いいえ | TTS/ComfyUI ビジュアルワークショップ、単独動作 - llama 状態に関係ず |

## 前提条件

| コンポーネント | バージョン / ソース | 用途 |
|-|-|-|
| [OpenClaw](https://docs.openclaw.ai) | latest | AI エージェントゲートウェイ |
| [Claude Code](https://github.com/anthropics/claude-code) | latest | ターミナルベースAIエージェント（任意、MCP 統合） |
| QQ Bot | OpenClaw qqbot チャネル | QQ メッセージ中継 |
| Telegram Bot | OpenClaw telegram チャネル | Telegram メッセージ中継 |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | b9222 | ローカル LLM 推論サーバー |
| [GPT-SoVITS v2](https://github.com/RVC-Boss/GPT-SoVITS) | v2pro-20250604 | TTS 音声合成 |
| [ComfyUI](https://github.com/comfyanonymous/ComfyUI) | aki-v3 | 画像生成エンジン |
| [Sakura デスクトップペット](https://github.com/Rvosy/Sakura) | v0.9.6-dev | デスクトップコンパニオン GUI |
| [pixi-live2d-display](https://github.com/guansss/pixi-live2d-display) | v0.5.0（バンドル済み） | Live2D WebGL レンダラー |
| Live2D Cubism Core | 4.x（バンドル済み：`live2d/live2dcubismcore.min.js`） | Live2D 物理/アニメーション |

> ?**TTS、ComfyUI、Live2D は完全に自己完結。** ランタイムに外部ダウンロードは不要 - すべてのモデル重み（`skills/sovits/`、`skills/comfyui_core/`）、Python スクリプト、JS ライブラリ（`live2d/pixi.min.js`、`live2d/plid-v5-bundle.js`）、Cubism Core 4（`live2d/live2dcubismcore.min.js`）がローカルにバンドル済み。
>
> ?? **headroom トークン節約** - `skills/headroom/`（SmartCrusher + ContentRouter + CCR）。開発シナリオでのツール出力をコンテキストウィンドウに入る前に圧縮。API 使用法は AGENTS.md を参照。
| headroom | バンドル済み（`skills/headroom/`） | SmartCrusher コンテキスト圧縮 + ContentRouter + CCR |
| Python | 3.12+ | ランタイム（Sakura + TTS + ComfyUI） |

## クイックスタート

### ?? 一括インストール（推奨）

**ワンコマンドで、ゼロから完全機能の AI ガールフレンド：**

**Windows:**
```powershell
powershell -File setup-all.ps1
```

**Linux / macOS:**
```bash
bash setup-all.sh
```

自動化パイプライン：環境チェック → モデルダウンロード → llama.cpp 設定 → OpenClaw インストール → Sakura デスクトップペット → ワークスペースデプロイ → パスチェック → 起動 → 検証。

> ブレークポイントからの再開対応。フラグ：`--skip-model-download`、`--skip-llama-setup`、`--skip-openclaw-setup`、`--skip-sakura-setup`、`--dry-run`、`--no-start`

-

### ステップバイステップ

### 0. OpenClaw のセットアップ

OpenClaw Gateway をインストールし、AI ガールフレンドワークスペースをデプロイ：

**Windows:**
```powershell
powershell -File setup-openclaw.ps1
```

**Linux / macOS:**
```bash
bash setup-openclaw.sh
```

このスクリプトは Node.js のインストール、OpenClaw Gateway のデプロイ、ワークスペースファイルのデプロイ、デーモンのインストール、設定パッチの適用を行います。

> **フラグ:** `--skip-node`、`--skip-deploy`、`--skip-daemon`、`--no-onboard`

### 1. モデルのダウンロード

**Windows:**
```powershell
pip install huggingface_hub
huggingface-cli login
powershell -File download-models.ps1
```

**Linux / macOS:**
```bash
pip install huggingface_hub
huggingface-cli login
bash download-models.sh
```

HuggingFace からすべての5つのモデルファイル（~31.7 GB）をプログレスレポートと再開サポート付きでダウンロード。

### 2. llama.cpp の設定

GPU、VRAM、CPU コア、RAM を自動検出して最適化起動設定を生成。

**Windows:**
```powershell
powershell -File setup-llama.ps1
```

**Linux / macOS:**
```bash
bash setup-llama.sh
```

### 3. パス設定

```powershell
powershell -File quick_setup.ps1
```

インタラクティブウィザード - ローカルパスを一度入力すれば、すべてのスクリプトが自動更新。

### 4. クイック起動

```powershell
# 全サービスのワンクリック起動（llama + 埋め込み + Live2D + Gateway）
powershell -File start.ps1
```

起動シーケンス:
```
[1/7] llama-server        （8080、LuffyTheFox Qwen3.6-35B、--no-mmap）
[2/7] 埋め込みサーバー    （9999、all-MiniLM + BGE 二重モデル、CPU、~100MB RAM）
[3/7] VRAM テア検出      （TTS/ComfyUI が llama を停止するかどうかを自動選択）
[4/7] Live2D ブリッジ    （19200、pixi-live2d-display）
[5/7] OpenClaw Gateway   （18789）
[6/7] llama-watchdog     （クラッシュ時自動再起動）
[7/7] ウェブチャットデーモン （19260 API + 19270 ウェブチャット、--no-llama）
```

**シャットダウン: `shiki.cmd -Stop`** - 全サービスを正常停止（llama → live2d → sakura → embedding → comfyui → gateway → cleanup）。

### 5. Live2D を個別起動

```powershell
# ブリッジ起動
Start-Process node -ArgumentList "live2d-bridge.mjs" -WorkingDirectory live2d -WindowStyle Hidden

# 単独ウィンドウで開く（Chrome アプモード）
Start-Process chrome -ArgumentList "--new-window --app=http://localhost:19200/index.html --window-size=450,650"
```

Live2D は枠なしの Chrome ウィンドウで実行 - デスクトップの任意の場所に配置可能。

### 6. Windows タスクスケジューラー（任意）

```powershell
# Llama 健康チェック（10分ごと）
schtasks /create /tn "llama-watchdog" `
  /tr "powershell -File C:\Users\<you>\.openclaw\workspace\skills\llama-watchdog.ps1" `
  /sc minute /mo 10

# 孤児プロセスクリーンアップ（毎時）
schtasks /create /tn "cleanup-orphans" `
  /tr "powershell -File C:\Users\<you>\.openclaw\workspace\skills\cleanup_orphans.ps1" `
  /sc hourly /mo 1
```

## アーキテクチャ

<table>
<tr><td colspan="2" align="center"><b>ユーザー入口</b></td></tr>
<tr><td colspan="2" align="center">QQ Bot &nbsp;|&nbsp; Telegram Bot &nbsp;|&nbsp; WebChat &nbsp;|&nbsp; Claude Code (MCP) &nbsp;|&nbsp; Artemis Studio コンソール</td></tr>
<tr><td colspan="2" align="center">↓</td></tr>
<tr><td colspan="2" align="center"><b>OpenClaw Gateway</b>（ポート18789） &nbsp;──&nbsp; <b>Claude Code MCP</b>（stdio） &nbsp;──&nbsp; <b>Sakura デスクトップペット</b>（PySide6、共有 llama-client）</td></tr>
<tr><td colspan="2" align="center">↓</td></tr>
<tr>
<td width="50%" valign="top">

**?? LLM 推論**

| コンポーネント | 説明 |
|-|-|
| `llama-server :8080` | Qwen3.6-35B-A3B MoE |
| メインセッション | AGENTS.md 駆動のロールプレイ |
| TTS | VRAM ティア対応停止/再起動 |
| ComfyUI | VRAM ティア対応停止/再起動 |
| ASR | Whisper small、llama と共存 |
| Sakura ペット | 共有クライアント、停止なし |
| Artemis Studio | 単独動作、停止なし |
| Live2D ブリッジ | HTTP :19200、停止なし |

</td>
<td width="50%" valign="top">

**?? メモリシステム**

| コンポーネント | 説明 |
|-|-|
| 埋め込み :9999 | all-MiniLM-L6-v2 + BGE-small-zh-v1.5（CPU、二重モデル） |
| memory_search | OpenClaw 原生複合検索（ベクター+BM25） |
| mem0_bridge | Qdrant 読み書きブリッジ |
| Qdrant DB | collection: sakura_memories、4 user_id スコープ |
| CCR | 8ターンごとにファクト抽出 → Qdrant |
| SmartCrusher | 24メッセージ/40K文字ハードキャップ |
| mem0_sync_cron | 30分ごと：Qdrant → _mem0_auto.md |

</td>
</tr>
</table>

### エージェントハブ

キャラクターメモリ分離のイミュータブルな能力指示：

| レヤー | ファイル | 用途 | 切替時 |
|-|-|-|-|
| **能力ハブ** | `AGENTS.md` | ComfyUI/TTS/Live2D 指示 | ??? 不変 |
| **高速リファレンス** | `TOOLS.md` | ツール呼び出しチートシート | ??? 不変 |
| **キャラクターペルソナ** | `SOUL.md` | 現在のキャラクターの性格/口調 | ?? ホットスワップ |

### エージェントハブ

キャラクターメモリ分離のイミュータブルな能力指示：

| レヤー | ファイル | 用途 | 切替時 |
|-|-|-|-|
| **能力ハブ** | `AGENTS.md` | ComfyUI/TTS/Live2D 指示 | 🛡️ 不変 |
| **高速リファレンス** | `TOOLS.md` | ツール呼び出しチートシート | 🛡️ 不変 |
| **キャラクターペルソナ** | `SOUL.md` | 現在のキャラクターの性格/口調 | 🔄 ホットスワップ |
| **キャラクターデータ** | `IDENTITY.md` | キャラクター名/設定 | 🔄 ホットスワップ |
| **ユーザープロファイル** | `USER.md` | 彼氏の名前/好み | 🛡️ 不変 |
| **ハーレムアーカイブ** | `skills/harem/<char>/` | キャラクターカードの情報源 | 📦 読み取り専用 |
| **短期メモリ** | `memory/role_play/<char>/` | 日別会話 YYYY-MM-DD.md | 🔀 キャラ別分離 |
| **長期メモリ** | Qdrant `user_id=<char>` | ベクター長期記憶 | 🔀 キャラ別分離 |
| **同期キャッシュ** | `_mem0_auto.md` | Qdrant → markdown（30分ごと） | 🔀 キャラ別分離 |

> 検索優先順位：ベクター長期記憶 > 手書き日付ノート > SOUL 基本ペルソナ

### WebChat — 内蔵ブラウザクライアント

`http://127.0.0.1:19270` でローカルに提供される、完全なブラウザベースのAIガールフレンドチャットインターフェース。

| 機能 | 説明 |
|-|-|
| **マルチキャラクタータブ** | 四季 夏目、アトリ、夜乃 桜間で切替 — 各キャラクターごとに分離された会話履歴、SOUL.md、長期メモリ |
| **ストリーミングチャット** | 文字列 tailored システムプロンプト注入付きリアルタイムトークンストリーミング（ロールペルソナ + ユーザープロファイル） |
| **自動画像生成** 🎨 | チャット入力エリアのワンクリックボタン — LLM が会話コンテキストから ComfyUI プロンプトを生成し、ローカル画像生成をトリガー。結果はチャットフロー内にインライン表示 |
| **Live2D 統合** | デスクトップペットを直接操作：頭を撫でる、戳く、アイドリングアニメーション再生 |
| **TTS 音声** | GPT-SoVITS 経由でチャットテキストからキャラクター音声を生成 |
| **スタジオパネル** | マニュアル TTS 合成と ComfyUI 画像生成用サイドパネル（プロンプト、ネガティブ、サイズ、ステップ、CFG、チェックポイント） |
| **ダッシュボード** | llama-server、埋め込み、Live2D ブリッジ、Artemis ブリッジ、OpenClaw Gateway、WebChat のステータスを表示するサービスヘルスダッシュボード — 各サービスごとの起動/停止/再起動制御付き |
| **llama ライフサイクル切替** | ComfyUI 画像生成前に llama-server を停止するかどうかを切替（8GB VRAM GPU 用に VRAM を解放、デフォルトON） |
| **二重モデルサポート** | ローカル llama-server またはリモート DeepSeek モデルを選択 — 設定で切替、設定は永続化 |

> WebChat は shiki デーモン（:19260）に直接通信し、llama-server や OpenAI 互換APIにプロキシします。キャラクター切替は瞬時 — 各タブは独自の SOUL.md + IDENTITY.md + USER.md をシステムプロンプトとして読み込みます。

### スキル詳細

| スキル | 場所 | llama 連携 | 備考 |
|-|-|-|-|
| **WebChat** | `web-chat/` | ❌ HTTP プロキシ | ポート19270、デーモン backed、マルチキャラ |
| **埋め込み** | `skills/shared/` | ❌ GPU なし | 二重モデルCPU、ポート9999 |
| **Live2D** | `skills/live2d/` | ❌ HTTP のみ | ブリッジ :19200、別プロセス |
| **TTS** | `skills/tts/` | 🔶 VRAMティア | ティア2：停止なし、ティア0/1：llama停止 |
| **ComfyUI** | `skills/comfyui/` | 🔶 VRAMティア | 上記と同じ |
| **ASR** | `skills/asr/` | ❌ 共存（1.5GB） | Faster-Whisper small |
| **Sakura** | `skills/sakura/` | ❌ 共有クライアント | 組み込み CCR + mem0 |
| **Artemis Studio** | `artemis_studio.py` | ❌ 単独 | デスクトップコンソール、TTS+ComfyUIワークショップ |
| **SmartCrusher** | `skills/shared/context_trimming.py` | - | 24メッセージ/40Kキャップ |
| **CCR** | `skills/sakura/app/agent/memory_curator.py` | - | 8ターンごとファクト抽出 |
| **mem0 ブリッジ** | `skills/shared/mem0_bridge.py` | - | CLI 検索/追加/同期 |
| **自動同期** | `skills/shared/mem0_sync_cron.py` | - | 30分ごと Qdrant → md |
| **キャラクターインポーター** | `skills/character_importer/` | - | PNG/JSON カードインポート |

**VRAM オーケストレーションフロー**:
1. 起動時：GPU VRAM を自動検出 → ティア決定（ティア0/1/2）
2. メインセッションがユーザーリクエストを受信 → コマンド構築
3. `sessions_spawn(mode="run")` でサブセッションを作成
4. ティア0/1：`stop_llama()` で VRAM 解放 → TTS/ComfyUI 推論 → `start_llama()` で再開
5. ティア2（≥12GB）：直接推論、llama はオンライン維持
6. Artemis Studio、Live2D、埋め込みは throughout アクティブ - 影響なし
7. サブセッションが `.task_flags` を書き込み → メインセッションにアナウンス
8. メインセッションがメディアファイルを読み込み → `<qqmedia>` / `MEDIA:` で送信
9. バックグラウンド：CCR は約8ターンごとで長期メモリを Qdrant に抽出
10. クローンジョブが30分ごとに Qdrant → `_mem0_auto.md` を同期し、原生 `memory_search` を有効化

## ⚠️ 重要注意事項

- **RTX 50xx（Blackwell）+ CUDA 13.x = `munmap_chunk(): invalid pointer` クラッシュ** - CUDA 13.x は Blackwell GPU 上の llama.cpp で既知のメモリ管理非互換性があります。**解決策：CUDA 12.x でコンパイルされたビルド済み llama.cpp バイナリを使用**（CUDA 13.x で自己コンパイルではなく）。[llama.cpp Releases](https://github.com/ggml-org/llama.cpp/releases) からダウンロードし、`cudart-llama-bin-win-cuda-12.4-x64.zip` を選択。RTX 5070 Ti は CUDA 12.x ドライバーと完全に互換。
- 8GB VRAM（ティア1）での TTS/ComfyUI 推論中に llama-server が約60-120秒オフライン — 会話が一時停止しますが、Live2D + Artemis Studio は稼働継続。12GB+（ティア2）では全くの中断なし
- サブセッションは **ローカルモデル**（メインと同じ）を使用、DeepSeek は任意のフォールバック
- llama-server はクロスターンプロンプトキャッシュの再利用をサポートしない（SSM の制限）— 定期的な `/reset` を使用
- **Live2D には Cubism Core 4 が必要**（5 や 6 ではない）- pixi-live2d-display v0.5.0 は Cubism 4 Framework にビルド済み；Core 5+ はクリッピング/レイヤー障害の原因。 **Core 4 はバンドル済み** `live2d/live2dcubismcore.min.js` — CDN は不要。
- すべてのモデルファイルは `.gitignore` で保護
- GPT-SoVITS 重みは独自学習済みであり配布されていない - 自身の音声データで学習

## 🙏 クレジット

- [@Rvosy](https://github.com/Rvosy) - [Sakura デスクトップペット](https://github.com/Rvosy/Sakura) 作成者、掲載許可取得済み（Issue #38）
- [@guansss](https://github.com/guansss) - [pixi-live2d-display](https://github.com/guansss/pixi-live2d-display) 作成者
- [Live2D Inc.](https://www.live2d.com) - Cubism SDK（非商業利用）
- [AgentRQ](https://github.com/agentrq/agentrq) - AgentRQ 互換タスクキューと MCP ツールインターフェースデザインのインスピレーション
- [headroom](https://github.com/chopratejas/headroom) - SmartCrusher コンテキスト圧縮 + CCR（収集-統合-取得）メモリパイプラインのインスピレーション
- [mem0](https://github.com/mem0ai/mem0) - Qdrant ベクターメモリアーキテクチャ + 複合検索デザインのインスピレーション
- [NVIDIA Cosmos](https://github.com/NVIDIA/cosmos) - 物理世界基礎モデル、[コミュニティ FP8 量子化版](https://huggingface.co/benjiaiplayground/Cosmos3-Nano_fp8) を `skills/cosmos/` にアーカイブ
